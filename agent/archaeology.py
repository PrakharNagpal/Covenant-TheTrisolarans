# P1 lane — archaeology RAG
import json
import os
from openai import AsyncOpenAI
from supabase import create_client

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
        canned_path = os.path.join(os.path.dirname(__file__), "..", "data", "archaeology_canned.json")
        try:
            with open(canned_path) as f:
                _CANNED_FALLBACK = json.load(f)
        except FileNotFoundError:
            _CANNED_FALLBACK = []
    return _CANNED_FALLBACK


def _canned_fallback(question: str) -> str | None:
    for entry in _load_canned():
        keywords = entry.get("keywords", [])
        if any(k.lower() in question.lower() for k in keywords):
            return entry.get("answer")
    return None


async def answer_archaeology(question: str) -> str:
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    embedding_resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=question,
    )
    question_embedding = embedding_resp.data[0].embedding

    try:
        result = supabase.rpc(
            "match_decisions",
            {"query_embedding": question_embedding, "match_count": 5},
        ).execute()
        relevant_decisions = result.data or []
    except Exception:
        fallback = _canned_fallback(question)
        if fallback:
            return fallback
        relevant_decisions = []

    if not relevant_decisions:
        fallback = _canned_fallback(question)
        if fallback:
            return fallback

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
    return resp.choices[0].message.content
