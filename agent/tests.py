# P1 lane — agent acceptance test suite
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.archaeology import answer_archaeology
from agent.classifier import classify_decision
from agent.contradiction import find_contradictions


def _print_result(name: str, passed: bool, detail: str) -> bool:
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
    return passed


async def _run_classifier_cases() -> list[bool]:
    cases = [
        ("classifier JWT decision", "Let's go with JWT — stateless, works for mobile", "DECISION", lambda r: r.get("confidence", 0) > 0.8),
        ("classifier bare SQL directive", "use SQL for database", "DECISION", lambda r: r.get("extracted_choice") == "SQL for database"),
        ("classifier JWT discussion", "Should we use JWT or sessions?", "DISCUSSION", lambda r: True),
        ("classifier lunch noise", "Lunch anyone?", "NOISE", lambda r: True),
        ("classifier Postgres decision", "We're going with Postgres over MongoDB", "DECISION", lambda r: True),
        ("classifier Redis discussion", "What about Redis for caching?", "DISCUSSION", lambda r: True),
    ]

    results = []
    for name, text, expected_label, extra_check in cases:
        result = await classify_decision(text)
        passed = result.get("label") == expected_label and extra_check(result)
        results.append(_print_result(name, passed, json.dumps(result)))
    return results


async def _run_contradiction_cases() -> list[bool]:
    repo_root = Path(__file__).resolve().parent.parent
    decisions = json.loads((repo_root / "data" / "decisions.json").read_text())
    jwt_decision = next(decision for decision in decisions if "jwt" in json.dumps(decision).lower())

    session_patch = (repo_root / "data" / "demo-commits" / "001-session-auth.patch").read_text()
    no_violation_patch = (repo_root / "data" / "demo-commits" / "002-no-violation.patch").read_text()

    session_results = await find_contradictions(session_patch, [jwt_decision])
    session_passed = (
        len(session_results) == 1
        and session_results[0].get("contradicts") is True
        and session_results[0].get("severity") == "structural"
    )

    no_violation_results = await find_contradictions(no_violation_patch, [jwt_decision])
    no_violation_passed = no_violation_results == []

    return [
        _print_result("contradiction session auth patch", session_passed, json.dumps(session_results)),
        _print_result("contradiction no-violation patch", no_violation_passed, json.dumps(no_violation_results)),
    ]


async def _run_archaeology_cases() -> list[bool]:
    cases = [
        ("archaeology JWT", "Why are we using JWT?", ["@alice", "@bob", "January 14"]),
        ("archaeology checkout", "Why is checkout 3 steps?", ["@design-lead", "February 28"]),
        ("archaeology Postgres", "Why do we use Postgres?", ["@priya", "@raj", "February 3"]),
    ]

    results = []
    for name, question, required_terms in cases:
        answer = await answer_archaeology(question)
        passed = all(term in answer for term in required_terms)
        results.append(_print_result(name, passed, answer.splitlines()[0]))
    return results


async def main() -> None:
    results = []
    results.extend(await _run_classifier_cases())
    results.extend(await _run_contradiction_cases())
    results.extend(await _run_archaeology_cases())

    passed = sum(1 for result in results if result)
    total = len(results)
    print(f"\n{passed}/{total} passed")

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
