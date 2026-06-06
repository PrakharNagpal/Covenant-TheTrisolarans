# P1 lane — contradiction detector
import json
from openai import AsyncOpenAI

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
    results = []
    for decision in decisions:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CONTRADICTION_PROMPT},
                {
                    "role": "user",
                    "content": f"PAST_DECISION: {json.dumps(decision)}\n\nNEW_INPUT: {new_input}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        result = json.loads(resp.choices[0].message.content)
        if result["contradicts"] and result["confidence"] >= 0.7:
            results.append({**result, "decision": decision})
    return sorted(results, key=lambda x: x["confidence"], reverse=True)
