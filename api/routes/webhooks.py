# P2 lane — webhook handlers (GitHub, Slack, Linear, Notion poller)
import asyncio
import hashlib
import hmac
import json
import os

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from notion_client import AsyncClient as NotionClient
from slack_sdk.web.async_client import AsyncWebClient

from agent.classifier import classify_decision
from agent.contradiction import find_contradictions
from api import db

router = APIRouter()

GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
COVENANT_URL = os.getenv("NGROK_URL", "http://localhost:3000")

# Demo cache — used when MODE=DEMO and diff contains "session"
DEMO_CACHE = {
    "session": {
        "contradicts": True,
        "severity": "structural",
        "explanation": "This introduces session-based auth, directly contradicting the Jan 14 JWT decision.",
        "confidence": 0.95,
        "decision": {},
    }
}


# ── helpers ──────────────────────────────────────────────────────────────────

def _verify_github_signature(payload_bytes: bytes, signature: str) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    expected = "sha256=" + hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_linear_signature(payload_bytes: bytes, signature: str) -> bool:
    secret = os.getenv("LINEAR_WEBHOOK_SECRET", "").encode()
    expected = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


async def _get_diff(before: str, after: str) -> str:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/compare/{before}...{after}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        data = resp.json()
        patches = []
        for file in data.get("files", []):
            if "patch" in file:
                patches.append(f"File: {file['filename']}\n{file['patch']}")
        return "\n\n".join(patches)


async def _post_commit_comment(sha: str, body: str):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{sha}/comments"
    async with httpx.AsyncClient() as client:
        await client.post(
            url,
            headers={"Authorization": f"token {GITHUB_TOKEN}"},
            json={"body": body},
        )


def _format_pr_comment(contradiction: dict) -> str:
    d = contradiction["decision"]
    participants = ", ".join(d.get("participants", []))
    date = d.get("created_at", "unknown date")
    if hasattr(date, "strftime"):
        date = date.strftime("%b %d, %Y")
    return f"""## 🛡️ Covenant — Promise Check

**This change may break a promise your team made.**

**Past decision** (made on **{date}** by {participants}):
> {d.get("summary", "")}

**Their reasoning:**
> {d.get("rationale", "")}

**Why I flagged it ({contradiction.get("severity", "unknown")}):**
{contradiction.get("explanation", "")}

---
*Is this intentional? 👍 to confirm (Covenant updates its priors), 👎 to flag for review.*

[View in Covenant →]({COVENANT_URL}/decisions/{d.get("id", "")})"""


async def _post_slack_reply(channel: str, thread_ts: str, text: str):
    slack = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
    await slack.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)


def _format_slack_reply(contradiction: dict) -> str:
    d = contradiction["decision"]
    return (
        f"⚠️ *Covenant alert* — this may contradict a past decision:\n"
        f"> *{d.get('summary', '')}*\n"
        f"Severity: `{contradiction.get('severity')}` | "
        f"Confidence: {contradiction.get('confidence', 0):.0%}\n"
        f"{contradiction.get('explanation', '')}"
    )


# ── background tasks ─────────────────────────────────────────────────────────

async def _process_push(payload: dict):
    sha = payload["after"]
    before = payload["before"]
    diff = await _get_diff(before, sha)

    if os.getenv("MODE") == "DEMO" and "session" in diff.lower():
        decisions = await db.get_all_decisions()
        cached = dict(DEMO_CACHE["session"])
        cached["decision"] = decisions[0] if decisions else {}
        contradictions = [cached]
    else:
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(diff, decisions)

    if contradictions:
        top = contradictions[0]
        body = _format_pr_comment(top)
        await _post_commit_comment(sha, body)
        await db.insert_alert(top, sha, "commit")


async def _process_slack_message(event: dict):
    text = event.get("text", "")
    classification = await classify_decision(text)
    if classification["label"] == "DECISION":
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(text, decisions)
        if contradictions:
            reply = _format_slack_reply(contradictions[0])
            await _post_slack_reply(event["channel"], event["ts"], reply)
            await db.insert_alert(contradictions[0], event["ts"], "slack")


async def _process_linear_comment(data: dict):
    text = data.get("body", "")
    classification = await classify_decision(text)
    if classification["label"] == "DECISION":
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(text, decisions)
        if contradictions:
            await db.insert_alert(contradictions[0], data.get("id"), "linear")


# ── notion poller (started in main.py startup) ────────────────────────────────

async def notion_poller():
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN", ""))
    while True:
        try:
            results = await notion.databases.query(database_id=os.getenv("NOTION_DATABASE_ID", ""))
            for row in results["results"]:
                props = row["properties"]
                decision = {
                    "id": row["id"],
                    "summary": props["Decision"]["title"][0]["plain_text"] if props.get("Decision", {}).get("title") else "",
                    "rationale": props["Rationale"]["rich_text"][0]["plain_text"] if props.get("Rationale", {}).get("rich_text") else "",
                    "participants": [p.strip() for p in props["Participants"]["rich_text"][0]["plain_text"].split(",")] if props.get("Participants", {}).get("rich_text") else [],
                    "source": "notion",
                    "created_at": row["created_time"],
                }
                await db.upsert_decision(decision)
        except Exception as e:
            print(f"Notion poll error: {e}")
        await asyncio.sleep(60)


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/webhooks/github")
async def github_webhook(req: Request, bg: BackgroundTasks):
    payload_bytes = await req.body()
    sig = req.headers.get("x-hub-signature-256", "")
    if not _verify_github_signature(payload_bytes, sig):
        raise HTTPException(status_code=401)

    payload = json.loads(payload_bytes)
    if "commits" not in payload:
        return {"ok": True}

    bg.add_task(_process_push, payload)
    return {"ok": True}


@router.post("/webhooks/slack")
async def slack_webhook(req: Request, bg: BackgroundTasks):
    payload = await req.json()

    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    if payload.get("type") == "event_callback":
        event = payload["event"]
        if event.get("type") == "message" and not event.get("subtype"):
            bg.add_task(_process_slack_message, event)

    return {"ok": True}


@router.post("/webhooks/linear")
async def linear_webhook(req: Request, bg: BackgroundTasks):
    body = await req.body()
    sig = req.headers.get("linear-signature", "")
    if not _verify_linear_signature(body, sig):
        raise HTTPException(status_code=401)

    payload = json.loads(body)
    if payload.get("type") == "Comment" and payload.get("action") == "create":
        bg.add_task(_process_linear_comment, payload["data"])

    return {"ok": True}
