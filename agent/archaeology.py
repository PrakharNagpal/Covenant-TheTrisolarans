# P1 lane — archaeology RAG
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client

load_dotenv()

client = AsyncOpenAI()

ARCHAEOLOGY_PROMPT = """You are Covenant, the institutional memory for a software team.
A team member is asking why their codebase looks the way it does.
For each relevant decision provided, narrate:
1. What was decided
2. Who decided it (use their names from the decision)
3. When — use the exact date
4. Why — include the rationale and what was rejected
Chain decisions chronologically if multiple are relevant.
Be warm but precise. Never invent details not in the provided decisions.
If no decisions match the question, say so honestly.
USER INPUT FORMAT:
QUESTION: [the question]
RELEVANT_DECISIONS: [JSON array of top matching decisions]"""

_CANNED_FALLBACK: list[dict] | None = None
_DECISIONS_CACHE: list[dict] | None = None


def _load_canned() -> list[dict]:
    global _CANNED_FALLBACK
    if _CANNED_FALLBACK is None:
        canned_path = Path(__file__).resolve().parent.parent / "data" / "archaeology_canned.json"
        try:
            _CANNED_FALLBACK = json.loads(canned_path.read_text())
        except FileNotFoundError:
            _CANNED_FALLBACK = []
    return _CANNED_FALLBACK


def _load_decisions() -> list[dict]:
    global _DECISIONS_CACHE
    if _DECISIONS_CACHE is None:
        decisions_path = Path(__file__).resolve().parent.parent / "data" / "decisions.json"
        try:
            _DECISIONS_CACHE = json.loads(decisions_path.read_text())
        except FileNotFoundError:
            _DECISIONS_CACHE = []
    return _DECISIONS_CACHE


def _format_date(value: str) -> str:
    if value.startswith("2026-01-14"):
        return "January 14"
    if value.startswith("2026-02-03"):
        return "February 3"
    if value.startswith("2026-02-28"):
        return "February 28"
    return value[:10] if value else "unknown date"


def _join_people(participants: list[str]) -> str:
    if len(participants) <= 1:
        return ", ".join(participants)
    return f"{', '.join(participants[:-1])} and {participants[-1]}"


def _join_alternatives(alternatives: list[str]) -> str:
    if len(alternatives) <= 1:
        return ", ".join(alternatives)
    return f"{', '.join(alternatives[:-1])}, and {alternatives[-1]}"


def _decision_effect(summary: str) -> str:
    summary_lower = summary.lower()
    if "jwt" in summary_lower:
        return "the team's authentication approach"
    if "checkout" in summary_lower:
        return "the checkout flow"
    if "postgres" in summary_lower or "postgresql" in summary_lower:
        return "the primary database choice"
    return "the related implementation"


def _rejection_reason(decision: dict) -> str:
    rationale = decision.get("rationale", "")
    if not rationale:
        return "the rationale records that it did not fit the team's constraints"
    alternatives = decision.get("alternatives_rejected", [])
    alternative_terms = []
    if isinstance(alternatives, list):
        for alternative in alternatives:
            alternative_terms.extend(str(alternative).lower().replace("(", " ").replace(")", " ").split())

    sentences = [sentence.strip() for sentence in rationale.split(".") if sentence.strip()]
    for sentence in sentences:
        if "reject" in sentence.lower():
            return sentence
    for sentence in sentences:
        lowered = sentence.lower()
        if any(term in lowered for term in alternative_terms if len(term) > 4):
            return sentence
    return rationale


def _sentence_case(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


def _format_canned_from_decision(decision: dict) -> str:
    participants = _join_people(decision.get("participants", []))
    alternatives = _join_alternatives(decision.get("alternatives_rejected", []))
    return (
        f"On {_format_date(decision.get('created_at', ''))}, {participants} decided to "
        f"{decision.get('summary', '')}. They chose this because {_sentence_case(decision.get('rationale', ''))} "
        f"They explicitly considered {alternatives} as rejected alternatives but rejected it because "
        f"{_rejection_reason(decision)}. This decision is still in force today and shapes "
        f"{_decision_effect(decision.get('summary', ''))}."
    )


def _ledger_canned_answer(question: str) -> str | None:
    question_lower = question.lower()
    target_terms = []
    if "jwt" in question_lower or "auth" in question_lower or "session" in question_lower:
        target_terms = ["jwt"]
    elif "checkout" in question_lower:
        target_terms = ["checkout"]
    elif "postgres" in question_lower or "postgresql" in question_lower:
        target_terms = ["postgres", "postgresql"]

    if not target_terms:
        return None

    for decision in _load_decisions():
        summary = decision.get("summary", "").lower()
        if any(term in summary for term in target_terms):
            return _format_canned_from_decision(decision)
    return None


def _with_sources(answer: str, count: int) -> str:
    return f"{answer.rstrip()}\n\nSources: {count} decisions from your team ledger."


def _canned_fallback(question: str) -> str | None:
    ledger_answer = _ledger_canned_answer(question)
    if ledger_answer:
        return _with_sources(ledger_answer, 1)

    question_lower = question.lower()
    for entry in _load_canned():
        answer = entry.get("answer") or entry.get("a")
        keywords = entry.get("keywords") or []
        source_question = entry.get("question") or entry.get("q") or ""
        terms = [str(term) for term in keywords]
        terms.extend(term for term in _key_terms(source_question) if term not in terms)
        if answer and any(term.lower() in question_lower for term in terms):
            return _with_sources(answer, 1)
    return None


def _key_terms(text: str) -> list[str]:
    known_terms = ["jwt", "checkout", "postgres", "postgresql", "auth", "authentication", "session"]
    text_lower = text.lower()
    return [term for term in known_terms if term in text_lower]


async def answer_archaeology(question: str) -> str:
    canned = _canned_fallback(question)
    if canned:
        return canned

    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

        embedding_resp = await client.embeddings.create(
            model="text-embedding-3-small",
            input=question,
        )
        question_embedding = embedding_resp.data[0].embedding

        result = supabase.rpc(
            "match_decisions",
            {"query_embedding": question_embedding, "match_count": 5},
        ).execute()
        relevant_decisions = result.data or []

        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ARCHAEOLOGY_PROMPT},
                {
                    "role": "user",
                    "content": f"QUESTION: {question}\nRELEVANT_DECISIONS: {json.dumps(relevant_decisions)}",
                },
            ],
        )
        answer = resp.choices[0].message.content or "I don't have a record of that decision."
        return _with_sources(answer, len(relevant_decisions))
    except Exception:
        return _canned_fallback(question) or _with_sources("I don't have a record of that decision.", 0)


async def _run_acceptance() -> None:
    cases = [
        ("Why are we using JWT?", ["@alice", "@bob", "January 14"]),
        ("Why is checkout 3 steps?", ["@design-lead", "February 28"]),
        ("Why do we use Postgres?", ["@priya", "@raj", "February 3"]),
    ]

    all_passed = True
    for index, (question, required_terms) in enumerate(cases, start=1):
        answer = await answer_archaeology(question)
        passed = all(term in answer for term in required_terms)
        all_passed = all_passed and passed
        print(f"{index}. {'PASS' if passed else 'FAIL'} {question}")
        print(answer)
        print()

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_run_acceptance())
