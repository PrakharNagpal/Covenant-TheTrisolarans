# P1 lane — contradiction detector
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

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


async def find_contradictions(new_input: str, decisions: list[dict]) -> list[dict]:
    async def check_decision(decision: dict) -> dict | None:
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
            return {**result, "decision": decision}
        return None

    checked = await asyncio.gather(*(check_decision(decision) for decision in decisions))
    results = [result for result in checked if result is not None]
    return sorted(results, key=lambda x: x["confidence"], reverse=True)


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
