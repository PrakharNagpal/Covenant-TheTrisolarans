# Lane: P2 backend
import json
import os
import asyncio

from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

_user_name_cache: dict[str, str] = {}


def _name_with_at(value: str) -> str:
    value = value.strip()
    if not value or value.startswith("@"):
        return value
    return f"@{value}"


async def get_slack_user_name(user_id: str | None) -> str:
    if not user_id:
        return "unknown"
    if user_id in _user_name_cache:
        return _user_name_cache[user_id]

    token = os.getenv("SLACK_BOT_TOKEN", "")
    if not token:
        return user_id

    slack = WebClient(token=token)
    try:
        response = await asyncio.to_thread(slack.users_info, user=user_id)
    except SlackApiError:
        return user_id

    user = response.get("user") or {}
    profile = user.get("profile") or {}
    username = (
        profile.get("display_name_normalized")
        or profile.get("display_name")
        or user.get("name")
    )
    real_name = (
        profile.get("real_name_normalized")
        or profile.get("real_name")
        or user.get("real_name")
    )
    resolved = _name_with_at(username) if username else real_name or user_id
    _user_name_cache[user_id] = resolved
    return resolved


async def post_slack_reply(channel: str, thread_ts: str, text: str):
    slack = WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
    await asyncio.to_thread(
        slack.chat_postMessage,
        channel=channel,
        thread_ts=thread_ts,
        text=text,
    )


def format_slack_reply(contradiction: dict) -> str:
    decision = contradiction.get("decision") or {}
    participants = ", ".join(decision.get("participants", []))
    date = decision.get("created_at", "unknown date")
    return (
        "Covenant - Promise Check\n"
        "This message may break a promise your team made.\n\n"
        f"Past decision ({date} by {participants}):\n"
        f"> {decision.get('summary', '')}\n\n"
        f"Why I flagged it ({contradiction.get('severity', 'unknown')}):\n"
        f"{contradiction.get('explanation', '')}"
    )


class SeedSlackAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "slack_export.json")
        with open(path) as f:
            self._messages = json.load(f)

    def get_messages(self) -> list[dict]:
        return self._messages
