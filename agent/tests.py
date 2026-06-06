# P1 lane — agent test suite
import asyncio
from agent.classifier import classify_decision
from agent.contradiction import find_contradictions


async def test_classifier():
    cases = [
        ("Let's go with JWT — stateless, works for mobile", "DECISION"),
        ("Should we use JWT or sessions?", "DISCUSSION"),
        ("Lunch anyone?", "NOISE"),
        ("We're going with Postgres over MongoDB", "DECISION"),
        ("What about Redis for caching?", "DISCUSSION"),
    ]
    for text, expected_label in cases:
        result = await classify_decision(text)
        status = "✅" if result["label"] == expected_label else "❌"
        print(f"{status} [{expected_label}] '{text[:50]}' → {result}")
    print("Classifier tests done.\n")


async def test_contradiction():
    jwt_decision = {
        "summary": "We will use JWT for session authentication — stateless, works for mobile clients.",
        "rationale": "JWT is stateless, eliminating server-side session storage. It works seamlessly across mobile and web clients.",
        "alternatives_rejected": "Server-side sessions were rejected due to scaling overhead.",
    }
    session_diff = """
+++ b/auth.js
+const session = require('express-session');
+app.use(session({ secret: 'abc', resave: false, saveUninitialized: true }));
"""
    no_violation_diff = """
+++ b/auth.js
+// verify JWT token on each request
+const decoded = jwt.verify(token, process.env.JWT_SECRET);
"""
    r1 = await find_contradictions(session_diff, [jwt_decision])
    status = "✅" if r1 and r1[0]["contradicts"] else "❌"
    print(f"{status} session diff should contradict JWT decision → {r1[0] if r1 else 'no result'}")

    r2 = await find_contradictions(no_violation_diff, [jwt_decision])
    status = "✅" if not r2 else "❌"
    print(f"{status} no-violation diff should NOT contradict → {r2}")
    print("Contradiction tests done.\n")


if __name__ == "__main__":
    asyncio.run(test_classifier())
    asyncio.run(test_contradiction())
