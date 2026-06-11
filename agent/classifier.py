# P1 lane — decision classifier
import asyncio
import json
import re

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

client = AsyncOpenAI()

SYSTEM_PROMPT = """You classify messages from team communication channels.

Output exactly one of:
- DECISION: the message commits the team to a specific course of action
- DISCUSSION: the message explores options without committing
- NOISE: off-topic, social, or operational

A message is DECISION if it uses commitment language, directive language, or terse decision-note language AND names a specific choice. Commitment language includes:
- Direct: "we'll go with", "let's use", "decided", "we chose", "we're using", "going with", "we picked", "we agreed on"
- Shorthand: "X it is", "X wins", "settled on X", "switching to X", "moving to X", "going forward with X"
- Passive: "X has been chosen", "X was selected", "agreed: X", "consensus: X"
- Mandate: "we need to use X", "all services must use X", "X is our standard"
- Directive: "we should use X" or "we should go with X" when followed by a specific tool, language, or technology name — in a team channel, "we should use X" is a team directive, not a suggestion
- Bare directive: "use SQL for database", "use Postgres", "switch auth to JWT", "standardize on REST". These are DECISION when they are written as an instruction/note, even without "we", "I want", or "decided".

IMPORTANT: "we should use X" naming a specific technology IS a DECISION — do not classify it as DISCUSSION. Contrast: "should we use X or Y?" (no commitment, two options) is DISCUSSION.

A message is DISCUSSION if it raises options without committing:
- "should we use X or Y", "what about", "considering", "leaning toward", "thinking about", "what if we", "anyone tried", "I'm thinking of using"

A message is NOISE if it is social, off-topic, scheduling, or contains no technology/process content.

"extracted_choice" must be the specific technology, tool, or approach that was decided — a short noun phrase (e.g. "JWT", "PostgreSQL", "server-side sessions", "3-step checkout"). Leave as null if label is not DECISION.

Output JSON only, no other text:
{"label": "DECISION"|"DISCUSSION"|"NOISE", "confidence": 0.0-1.0, "extracted_choice": "..." | null}"""

_BARE_DIRECTIVE_RE = re.compile(
    r"^\s*(?:"
    r"use|choose|pick|adopt|standardize\s+on|standardise\s+on|"
    r"switch(?:ing)?\s+(?:to|auth\s+to|database\s+to)?|"
    r"move\s+to|migrate\s+to|go\s+with"
    r")\s+(?P<choice>[a-z0-9][^\n?.!]{1,120})[.!]?\s*$",
    re.IGNORECASE,
)

_TECH_CONTEXT_WORDS = {
    "api",
    "auth",
    "authentication",
    "backend",
    "cache",
    "caching",
    "database",
    "db",
    "deploy",
    "deployment",
    "frontend",
    "queue",
    "storage",
    "webhook",
}

_TECH_CHOICE_WORDS = {
    "aws",
    "django",
    "fastapi",
    "firebase",
    "github",
    "graphql",
    "jwt",
    "linear",
    "mongo",
    "mongodb",
    "mysql",
    "nextjs",
    "notion",
    "postgres",
    "postgresql",
    "python",
    "react",
    "redis",
    "render",
    "rest",
    "slack",
    "sql",
    "supabase",
    "typescript",
    "vercel",
}


def _clean_choice(choice: str) -> str:
    replacements = {
        "api": "API",
        "db": "DB",
        "jwt": "JWT",
        "rest": "REST",
        "sql": "SQL",
    }
    cleaned = choice.strip(" -:;,.")
    for raw, replacement in replacements.items():
        cleaned = re.sub(rf"\b{raw}\b", replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def _deterministic_decision(text: str) -> dict | None:
    stripped = " ".join(text.strip().split())
    if not stripped or "?" in stripped:
        return None

    match = _BARE_DIRECTIVE_RE.match(stripped)
    if not match:
        return None

    choice = _clean_choice(match.group("choice"))
    terms = set(re.findall(r"[a-z0-9]+", choice.lower()))
    if not (terms & _TECH_CHOICE_WORDS or terms & _TECH_CONTEXT_WORDS):
        return None

    return {
        "label": "DECISION",
        "confidence": 0.92,
        "extracted_choice": choice,
    }


async def classify_decision(text: str, context: list[str] = []) -> dict:
    deterministic = _deterministic_decision(text)
    if deterministic:
        return deterministic

    context_str = "\n".join(context[-2:]) if context else ""
    user_content = f"Context:\n{context_str}\n\nMessage:\n{text}" if context_str else text

    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(resp.choices[0].message.content)


async def _run_acceptance() -> None:
    cases = [
        ("Let's go with JWT — stateless, works for mobile", "DECISION", lambda r: r.get("confidence", 0) > 0.8),
        ("use SQL for database", "DECISION", lambda r: r.get("extracted_choice") == "SQL for database"),
        ("Should we use JWT or sessions?", "DISCUSSION", lambda r: True),
        ("Lunch anyone?", "NOISE", lambda r: True),
        ("We're going with Postgres over MongoDB", "DECISION", lambda r: True),
        ("What about Redis for caching?", "DISCUSSION", lambda r: True),
    ]

    all_passed = True
    for index, (text, expected_label, extra_check) in enumerate(cases, start=1):
        result = await classify_decision(text)
        passed = result.get("label") == expected_label and extra_check(result)
        all_passed = all_passed and passed
        status = "PASS" if passed else "FAIL"
        print(f"{index}. {status} expected={expected_label} result={json.dumps(result)}")

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_run_acceptance())
