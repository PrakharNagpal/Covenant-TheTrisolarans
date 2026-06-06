# P1 lane — decision classifier
import asyncio
import json

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

client = AsyncOpenAI()

SYSTEM_PROMPT = """You classify messages from team communication channels. Output exactly one of:
- DECISION: the message commits the team to a specific course of action
- DISCUSSION: the message explores options without committing
- NOISE: off-topic, social, or operational

A message is DECISION if it contains commitment language ("we'll go with", "let's use", "decided", "we chose", "we're using") AND names a specific choice.
A message is DISCUSSION if it raises options without committing ("should we consider", "leaning toward", "what about", "what if").

Output JSON only, no other text:
{"label": "DECISION"|"DISCUSSION"|"NOISE", "confidence": 0.0-1.0, "extracted_choice": "..."}"""


async def classify_decision(text: str, context: list[str] = []) -> dict:
    context_str = "\n".join(context[-2:]) if context else ""
    user_content = f"Context:\n{context_str}\n\nMessage:\n{text}" if context_str else text

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
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
