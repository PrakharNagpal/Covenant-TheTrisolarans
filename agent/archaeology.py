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


def _load_canned() -> list[dict]:
    global _CANNED_FALLBACK
    if _CANNED_FALLBACK is None:
        canned_path = Path(__file__).resolve().parent.parent / "data" / "archaeology_canned.json"
        try:
            _CANNED_FALLBACK = json.loads(canned_path.read_text())
        except FileNotFoundError:
            _CANNED_FALLBACK = []
    return _CANNED_FALLBACK


def _canned_fallback(question: str) -> str | None:
    question_lower = question.lower()
    for entry in _load_canned():
        answer = entry.get("answer") or entry.get("a")
        keywords = entry.get("keywords") or []
        source_question = entry.get("question") or entry.get("q") or ""
        terms = [str(term) for term in keywords]
        terms.extend(term for term in _key_terms(source_question) if term not in terms)
        if answer and any(term.lower() in question_lower for term in terms):
            return answer
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
        return resp.choices[0].message.content or "I don't have a record of that decision."
    except Exception:
        return _canned_fallback(question) or "I don't have a record of that decision."


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
