# Lane: P2 backend
import json
import os
from copy import deepcopy

from api import db

_jwt_decision: dict | None = None

SESSION_DIFF_SUMMARY = (
    "This commit replaces JWT token issuance and bearer-token middleware with "
    "server-side session creation, cookies, and session lookup."
)


def _is_demo_mode() -> bool:
    return os.getenv("MODE") == "DEMO"


def _find_jwt_decision(decisions: list[dict]) -> dict | None:
    for decision in decisions:
        if "jwt" in json.dumps(decision).lower():
            return decision
    return None


async def load_jwt_decision() -> None:
    global _jwt_decision
    if not _is_demo_mode():
        return

    decisions = await db.get_all_decisions()
    _jwt_decision = _find_jwt_decision(decisions)
    if _jwt_decision:
        print(f"[DEMO CACHE READY] JWT decision {_jwt_decision.get('id')}", flush=True)
    else:
        print("[DEMO CACHE READY] JWT decision not found", flush=True)


async def _jwt_decision_or_load() -> dict:
    global _jwt_decision
    if _jwt_decision is None:
        await load_jwt_decision()
    return _jwt_decision or {}


def _is_no_violation_002(diff: str) -> bool:
    lowered = diff.lower()
    readme_changed = "file: readme.md" in lowered or "diff --git a/readme.md b/readme.md" in lowered
    return readme_changed and "## running locally" in lowered


async def get_cached_contradictions(diff: str) -> list[dict] | None:
    if not _is_demo_mode():
        return None

    lowered = diff.lower()
    if "session" in lowered:
        print("[DEMO CACHE HIT] session-auth contradiction", flush=True)
        return [
            {
                "contradicts": True,
                "severity": "structural",
                "explanation": "This introduces session-based auth, directly contradicting the Jan 14 JWT decision.",
                "confidence": 0.95,
                "decision": deepcopy(await _jwt_decision_or_load()),
                "diff_summary": SESSION_DIFF_SUMMARY,
            }
        ]

    if _is_no_violation_002(diff):
        print("[DEMO CACHE HIT] 002 no-violation", flush=True)
        return []

    return None
