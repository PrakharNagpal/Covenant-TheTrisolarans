# P1 lane — contradiction detector
import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client

load_dotenv()

client = AsyncOpenAI()

CONTRADICTION_PROMPT = """You check whether new input contradicts a past team decision.

Input format:
PAST_DECISION: {decision object with summary, rationale, alternatives_rejected}
NEW_INPUT: {code diff, spec change, or new message}

Output JSON only, no other text:
{
  "contradicts": true|false,
  "severity": "cosmetic"|"behavioural"|"structural",
  "explanation": "one sentence explaining the contradiction",
  "confidence": 0.0-1.0
}

Severity guide:
- cosmetic: label or naming change, no functional impact
- behavioural: same shape, different logic (e.g. validation timing)
- structural: fundamentally different approach (e.g. JWT to sessions, REST to GraphQL)

Be conservative. Only flag clear contradictions.
confidence below 0.7 should output contradicts: false."""

_STOPWORDS = {
    "about",
    "after",
    "and",
    "also",
    "any",
    "because",
    "before",
    "being",
    "change",
    "changes",
    "commit",
    "const",
    "could",
    "decision",
    "demo",
    "does",
    "each",
    "every",
    "file",
    "for",
    "from",
    "function",
    "get",
    "into",
    "main",
    "new",
    "need",
    "needed",
    "not",
    "only",
    "out",
    "patch",
    "process",
    "proposed",
    "provided",
    "server",
    "side",
    "status",
    "return",
    "returns",
    "should",
    "store",
    "that",
    "the",
    "their",
    "there",
    "this",
    "use",
    "using",
    "user",
    "users",
    "via",
    "with",
    "would",
}

_TOPIC_KEYWORDS = {
    "auth": {
        "auth",
        "authentication",
        "bearer",
        "cookie",
        "cookies",
        "jwt",
        "login",
        "logout",
        "password",
        "revocation",
        "session",
        "sessions",
        "token",
        "tokens",
    },
    "database": {"acid", "database", "db", "dynamodb", "jsonb", "mongo", "mongodb", "mysql", "postgres", "postgresql", "relational"},
    "checkout": {"cart", "checkout", "delivery", "flow", "payment", "step", "steps"},
    "pii": {"address", "email", "legal", "orders", "pdpa", "pii", "retention", "user_id"},
    "deployment": {"aws", "cloudfront", "deploy", "deployment", "ec2", "ecs", "fly", "railway", "vercel"},
    "retry": {"backoff", "fixed", "interval", "jitter", "linear", "retries", "retry", "stripe"},
    "api_versioning": {"accept", "api", "header", "headers", "path", "url", "version", "versioning", "v1", "v2"},
    "rate_limit": {"authenticated", "limit", "minute", "rate", "req", "requests", "scrapers"},
    "redis": {"cache", "caching", "counter", "counters", "ephemeral", "redis"},
    "monorepo": {"monorepo", "polyrepo", "repository", "shared", "submodules", "types", "workspaces"},
}

_TOPIC_ANCHORS = {
    "auth": {"auth", "authentication", "jwt", "session", "sessions", "token", "tokens", "cookie", "cookies"},
    "database": {"acid", "dynamodb", "mongo", "mongodb", "mysql", "postgres", "postgresql"},
    "checkout": {"cart", "checkout", "delivery", "payment"},
    "pii": {"address", "email", "orders", "pdpa", "pii", "user_id"},
    "deployment": {"aws", "cloudfront", "deploy", "deployment", "ec2", "ecs", "fly", "railway", "vercel"},
    "retry": {"backoff", "jitter", "retries", "retry", "stripe"},
    "api_versioning": {"accept", "header", "headers", "url", "v1", "v2", "version", "versioning"},
    "rate_limit": {"limit", "rate", "req"},
    "redis": {"cache", "caching", "counter", "counters", "redis"},
    "monorepo": {"monorepo", "polyrepo", "submodules", "workspaces"},
}

_MIN_RELEVANCE_SCORE = 30
_MAX_CANDIDATE_DECISIONS = 4

DETAIL_PROMPT = """Expand a contradiction explanation for a GitHub PR comment.

Write 2-3 concise sentences. Include:
- the specific code pattern or identifier that triggered the flag
- what the team originally decided and why
- the severity in plain English

Do not invent facts not present in the inputs."""


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_/-]+", text.lower())
        if (len(token) >= 3 or token in {"db", "jwt", "api"}) and token not in _STOPWORDS
    }


def _topic_hits(terms: set[str]) -> set[str]:
    return {
        topic
        for topic, anchors in _TOPIC_ANCHORS.items()
        if terms & anchors
    }


def _decision_text(decision: dict) -> str:
    fields = [
        decision.get("summary", ""),
        decision.get("rationale", ""),
        decision.get("source_ref", ""),
    ]
    alternatives = decision.get("alternatives_rejected", [])
    if isinstance(alternatives, list):
        fields.extend(str(item) for item in alternatives)
    else:
        fields.append(str(alternatives))
    return " ".join(str(field) for field in fields if field)


def _relevance_score(new_input: str, decision: dict) -> int:
    input_terms = _terms(new_input)
    decision_terms = _terms(_decision_text(decision))
    topic_overlap = _topic_hits(input_terms) & _topic_hits(decision_terms)
    direct_overlap = input_terms & decision_terms

    if not topic_overlap:
        return 0

    score = len(topic_overlap) * 20 + len(direct_overlap)
    for important in ("jwt", "auth", "authentication", "session", "sessions", "postgres", "checkout", "redis", "api"):
        if important in direct_overlap:
            score += 5

    return score


async def find_contradictions(new_input: str, decisions: list[dict]) -> list[dict]:
    relevant_decisions = [
        (decision, score)
        for decision in decisions
        if (score := _relevance_score(new_input, decision)) >= _MIN_RELEVANCE_SCORE
    ]
    relevant_decisions = sorted(
        relevant_decisions,
        key=lambda item: item[1],
        reverse=True,
    )[:_MAX_CANDIDATE_DECISIONS]

    async def check_decision(decision: dict, relevance_score: int) -> dict | None:
        user_message = f"PAST_DECISION: {json.dumps(decision)}\n\nNEW_INPUT: {new_input}"
        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CONTRADICTION_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        result = json.loads(response.choices[0].message.content)
        if result.get("contradicts") is True and result.get("confidence", 0.0) >= 0.7:
            detail_response = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                messages=[
                    {"role": "system", "content": DETAIL_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"PAST_DECISION: {json.dumps(decision)}\n\n"
                            f"NEW_INPUT: {new_input}\n\n"
                            f"CONTRADICTION_RESULT: {json.dumps(result)}"
                        ),
                    },
                ],
            )
            explanation_detail = detail_response.choices[0].message.content or result.get("explanation", "")
            return {
                **result,
                "explanation_detail": explanation_detail,
                "decision": decision,
                "_relevance_score": relevance_score,
            }
        return None

    checked = await asyncio.gather(
        *(check_decision(decision, score) for decision, score in relevant_decisions)
    )
    results = [result for result in checked if result is not None]
    sorted_results = sorted(
        results,
        key=lambda x: (x["confidence"], x["_relevance_score"]),
        reverse=True,
    )
    for result in sorted_results:
        result.pop("_relevance_score", None)
    return sorted_results


async def find_all_contradictions(new_input: str) -> list[dict]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    embedding_resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=new_input,
    )
    embedding = embedding_resp.data[0].embedding

    supabase = create_client(supabase_url, supabase_key)
    result = await asyncio.to_thread(
        lambda: supabase.rpc(
            "match_decisions",
            {"query_embedding": embedding, "match_count": 10},
        ).execute()
    )
    decisions = result.data or []
    return await find_contradictions(new_input, decisions)


def _load_jwt_decision(decisions_path: Path) -> dict:
    decisions = json.loads(decisions_path.read_text())
    for decision in decisions:
        searchable = json.dumps(decision).lower()
        if "jwt" in searchable:
            return decision
    raise ValueError(f"No JWT decision found in {decisions_path}")


async def _demo_check() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    jwt_decision = _load_jwt_decision(repo_root / "data" / "decisions.json")

    session_patch = (repo_root / "data" / "demo-commits" / "001-session-auth.patch").read_text()
    no_violation_patch = (repo_root / "data" / "demo-commits" / "002-no-violation.patch").read_text()

    session_results = await find_contradictions(session_patch, [jwt_decision])
    no_violation_results = await find_contradictions(no_violation_patch, [jwt_decision])

    session_passed = (
        len(session_results) == 1
        and session_results[0].get("contradicts") is True
        and session_results[0].get("severity") == "structural"
    )
    no_violation_passed = no_violation_results == []

    print("001-session-auth.patch:", json.dumps(session_results, indent=2))
    print("PASS" if session_passed else "FAIL")
    print("002-no-violation.patch:", json.dumps(no_violation_results, indent=2))
    print("PASS" if no_violation_passed else "FAIL")

    if not session_passed or not no_violation_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_demo_check())
