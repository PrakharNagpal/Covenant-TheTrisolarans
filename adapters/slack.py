# Lane: P2 backend
import json
import os
import asyncio

from slack_sdk.web import WebClient


async def post_slack_reply(channel: str, thread_ts: str, text: str):
    slack = WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
    await asyncio.to_thread(
        slack.chat_postMessage,
        channel=channel,
        thread_ts=thread_ts,
        text=text,
    )


async def post_slack_overwrite_prompt(
    channel: str,
    thread_ts: str,
    text: str,
    pending_id: str,
):
    slack = WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
    await asyncio.to_thread(
        slack.chat_postMessage,
        channel=channel,
        thread_ts=thread_ts,
        text=text,
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Yes, replace decision"},
                        "style": "danger",
                        "value": pending_id,
                        "action_id": "covenant_overwrite_yes",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "No, keep old decision"},
                        "value": pending_id,
                        "action_id": "covenant_overwrite_no",
                    },
                ],
            },
        ],
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


def format_slack_overwrite_prompt(contradiction: dict, new_decision: dict) -> str:
    decision = contradiction.get("decision") or {}
    participants = ", ".join(decision.get("participants", []))
    return (
        "Covenant found a conflicting decision.\n\n"
        f"*Existing decision* ({decision.get('created_at', 'unknown date')} by {participants}):\n"
        f"> {decision.get('summary', '')}\n\n"
        f"*New proposed decision:*\n"
        f"> {new_decision.get('summary', '')}\n\n"
        "Do you want to replace the existing decision with this new one?"
    )


class SeedSlackAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "slack_export.json")
        with open(path) as f:
            self._messages = json.load(f)

    def get_messages(self) -> list[dict]:
        return self._messages
