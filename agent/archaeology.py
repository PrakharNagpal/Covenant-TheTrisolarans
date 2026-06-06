# P1 lane — agentic archaeology
import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Covenant, the institutional memory for a software team.
A team member is asking about their codebase history and past decisions.

You have tools to search the team's decisions database, Slack messages, and Notion docs.
Use them to find relevant information, then synthesize a clear answer.

When answering:
1. Narrate what was decided, who decided it, when, and why
2. Include rationale and what alternatives were rejected
3. If multiple related decisions exist, chain them chronologically
4. Be warm but precise — never invent details not found in the sources
5. If nothing relevant exists across all sources, say so honestly

Search broadly: if the user asks about "flutter" also search "mobile", "kotlin", "ios".
If the first search returns nothing, try related synonyms before giving up."""

# ── OpenAI tool definitions ───────────────────────────────────────────────────

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_decisions",
            "description": (
                "Search the decisions database for records matching keywords. "
                "Use this to find formal decisions about technology choices, architecture, "
                "processes, etc. Try broad terms and synonyms — for 'flutter' also search "
                "'mobile', 'kotlin', 'ios', 'android'. Returns up to 5 matching decisions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Space-separated keywords to search for.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_slack",
            "description": (
                "Search Slack messages for team discussions related to the question. "
                "Useful for finding the context, debates, and informal decisions made in chat. "
                "Returns up to 10 relevant messages."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in Slack messages.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_notion",
            "description": (
                "Search Notion pages and databases for documentation, decision records, "
                "and project notes. Returns up to 5 relevant Notion records."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for in Notion.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

# ── Keyword expansion aliases ─────────────────────────────────────────────────

_TECH_ALIASES: dict[str, list[str]] = {
    "flutter": ["kotlin", "swift", "react native", "mobile", "android", "ios"],
    "react native": ["flutter", "kotlin", "swift", "mobile", "android", "ios"],
    "swift": ["kotlin", "flutter", "ios", "mobile"],
    "vue": ["react", "angular", "frontend", "javascript"],
    "angular": ["react", "vue", "frontend", "javascript"],
    "mysql": ["postgres", "postgresql", "mongodb", "database"],
    "dynamodb": ["postgres", "postgresql", "database"],
    "graphql": ["rest", "api", "endpoint"],
    "sessions": ["jwt", "auth", "authentication", "token"],
    "session": ["jwt", "auth", "authentication", "token"],
    "firebase": ["supabase", "postgres", "database", "backend"],
}


def _expand_terms(query: str) -> list[str]:
    raw = [t.strip("?.,!") for t in query.lower().split() if len(t) > 2]
    expanded = list(raw)
    for term in raw:
        for alias in _TECH_ALIASES.get(term, []):
            if alias not in expanded:
                expanded.append(alias)
    return expanded


def _score_text(terms: list[str], obj: dict) -> int:
    text = json.dumps(obj).lower()
    return sum(1 for t in terms if t in text)


# ── Tool implementations ──────────────────────────────────────────────────────

async def _tool_search_decisions(query: str) -> str:
    try:
        from api import db
        decisions = await db.get_all_decisions()
    except Exception as exc:
        logger.warning("search_decisions: DB load failed: %s", exc)
        return json.dumps({"error": "Could not access decisions database", "results": []})

    if not decisions:
        return json.dumps({"results": [], "count": 0})

    terms = _expand_terms(query)
    scored = [(d, _score_text(terms, d)) for d in decisions]
    scored = [(d, s) for d, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [d for d, _ in scored[:5]]
    return json.dumps({"results": top, "count": len(top)})


async def _tool_search_slack(query: str) -> str:
    token = os.getenv("SLACK_BOT_TOKEN", "")
    terms = [t.lower().strip("?.,!") for t in query.lower().split() if len(t) > 2]

    if token:
        try:
            from slack_sdk.web import WebClient
            from slack_sdk.errors import SlackApiError

            slack = WebClient(token=token)
            channels_data = await asyncio.to_thread(
                lambda: slack.conversations_list(types="public_channel", limit=50).data
            )
            matching: list[dict] = []
            for channel in channels_data.get("channels", [])[:10]:
                try:
                    hist = await asyncio.to_thread(
                        lambda c=channel: slack.conversations_history(
                            channel=c["id"], limit=200
                        ).data
                    )
                    for msg in hist.get("messages", []):
                        text = (msg.get("text") or "").lower()
                        if any(t in text for t in terms):
                            matching.append({
                                "channel": channel.get("name"),
                                "text": msg.get("text", ""),
                                "ts": msg.get("ts"),
                                "user": msg.get("user"),
                            })
                except SlackApiError:
                    continue

            if matching:
                return json.dumps({"results": matching[:10], "count": len(matching)})
        except Exception as exc:
            logger.warning("search_slack: live API failed: %s", exc)

    # Fall back to local seed export
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "slack_export.json")
    if os.path.exists(seed_path):
        try:
            with open(seed_path) as f:
                messages = json.load(f)
            matching = [
                m for m in messages
                if any(t in (m.get("text") or "").lower() for t in terms)
            ]
            return json.dumps({"results": matching[:10], "count": len(matching)})
        except Exception as exc:
            logger.warning("search_slack: seed fallback failed: %s", exc)

    return json.dumps({"results": [], "count": 0, "note": "Slack not configured"})


async def _tool_search_notion(query: str) -> str:
    if not os.getenv("NOTION_TOKEN") or not os.getenv("NOTION_DATABASE_ID"):
        return json.dumps({"results": [], "count": 0, "note": "Notion not configured"})

    try:
        from adapters.notion import query_notion_decisions
        decisions = await query_notion_decisions()
    except Exception as exc:
        logger.warning("search_notion: query failed: %s", exc)
        return json.dumps({"error": str(exc), "results": []})

    terms = _expand_terms(query)
    scored = [(d, _score_text(terms, d)) for d in decisions]
    scored = [(d, s) for d, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [d for d, _ in scored[:5]]
    return json.dumps({"results": top, "count": len(top)})


async def _execute_tool(name: str, arguments: str) -> str:
    try:
        inputs = json.loads(arguments)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid tool arguments"})

    query = inputs.get("query", "")
    if name == "search_decisions":
        return await _tool_search_decisions(query)
    if name == "search_slack":
        return await _tool_search_slack(query)
    if name == "search_notion":
        return await _tool_search_notion(query)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Keyword fallback (no API key required) ────────────────────────────────────

def _format_date(value: str) -> str:
    if not value:
        return "an unknown date"
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19].rstrip("Z"), fmt.rstrip("Z")).strftime(
                "%B %-d, %Y"
            )
        except ValueError:
            continue
    return value[:10]


def _join_people(participants: list[str]) -> str:
    if not participants:
        return "the team"
    if len(participants) == 1:
        return participants[0]
    return f"{', '.join(participants[:-1])} and {participants[-1]}"


def _sentence_case(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def _format_answer_from_decision(decision: dict) -> str:
    participants = _join_people(decision.get("participants") or [])
    date = _format_date(decision.get("created_at") or decision.get("date") or "")
    summary = decision.get("summary", "")
    rationale = decision.get("rationale", "")
    alternatives = decision.get("alternatives_rejected") or []
    if len(alternatives) == 1:
        alts_str = alternatives[0]
    elif len(alternatives) > 1:
        alts_str = ", ".join(alternatives[:-1]) + f", and {alternatives[-1]}"
    else:
        alts_str = "other approaches"
    return (
        f"On {date}, {participants} decided to {_sentence_case(summary)}. "
        f"They chose this because {_sentence_case(rationale)} "
        f"They considered {alts_str} but went with this approach."
    )


async def _canned_fallback(question: str) -> dict | None:
    try:
        from api import db
        decisions = await db.get_all_decisions()
    except Exception:
        decisions = []

    if not decisions:
        return None

    terms = _expand_terms(question)
    scored = [(d, _score_text(terms, d)) for d in decisions]
    scored = [(d, s) for d, s in scored if s >= 1]
    if not scored:
        return None

    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0][0]
    answer = _format_answer_from_decision(best)
    return {"answer": answer + "\n\nSources: 1 decision from your team ledger."}


# ── Main entry point ──────────────────────────────────────────────────────────

async def answer_archaeology(question: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — using keyword fallback")
        return await _canned_fallback(question) or {
            "answer": "I don't have a record of that decision."
        }

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        messages: list[dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        for _ in range(6):  # max 6 rounds (question + up to 5 tool rounds)
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=_TOOLS,
                tool_choice="auto",
            )

            choice = response.choices[0]
            messages.append(choice.message.model_dump(exclude_none=True))

            if choice.finish_reason == "stop":
                break

            if choice.finish_reason != "tool_calls":
                break

            # Execute all tool calls in parallel
            tool_calls = choice.message.tool_calls or []
            results = await asyncio.gather(
                *[_execute_tool(tc.function.name, tc.function.arguments) for tc in tool_calls]
            )
            for tc, result in zip(tool_calls, results):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        answer = choice.message.content or ""
        return {"answer": answer or "I don't have a record of that decision."}

    except Exception as exc:
        logger.warning("Agentic archaeology failed: %s", exc)
        fallback = await _canned_fallback(question)
        return fallback or {"answer": "I don't have a record of that decision."}


# ── Acceptance test ───────────────────────────────────────────────────────────

async def _run_acceptance() -> None:
    cases = [
        ("Why are we using JWT?", ["jwt", "auth"]),
        ("Why do we use Postgres?", ["postgres", "database"]),
        ("Why did we choose kotlin for mobile?", ["kotlin", "mobile"]),
    ]

    all_passed = True
    for idx, (question, check_terms) in enumerate(cases, start=1):
        result = await answer_archaeology(question)
        answer = result.get("answer", "").lower()
        passed = any(term in answer for term in check_terms)
        all_passed = all_passed and passed
        print(f"{idx}. {'PASS' if passed else 'FAIL'} {question}")
        print(result.get("answer", ""))
        print()

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(_run_acceptance())
