# Lane: P2 backend
import asyncio
import json
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from adapters.github import get_diff, post_commit_comment, verify_github_signature
from api import db

router = APIRouter()

COVENANT_URL = os.getenv("NGROK_URL", "http://localhost:3000")

# Demo cache — used when MODE=DEMO for the known demo commits.
DEMO_CACHE = {
    "session": {
        "contradicts": True,
        "severity": "structural",
        "explanation": "This introduces session-based auth, directly contradicting the Jan 14 JWT decision.",
        "confidence": 0.95,
        "decision": {},
        "diff_summary": "This commit replaces JWT token issuance and bearer-token middleware with server-side session creation, cookies, and session lookup.",
    }
}


def _verify_linear_signature(payload_bytes: bytes, signature: str) -> bool:
    import hashlib
    import hmac

    secret = os.getenv("LINEAR_WEBHOOK_SECRET", "").encode()
    expected = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def _format_date(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%b %d, %Y")
        except ValueError:
            return value
    return "unknown date"


def _summarize_diff(diff: str, contradiction: dict) -> str:
    if contradiction.get("diff_summary"):
        return contradiction["diff_summary"]
    if "session" in diff.lower() and "jwt" in diff.lower():
        return "This commit replaces JWT token handling with server-side session authentication."

    files = []
    for line in diff.splitlines():
        if line.startswith("File: "):
            files.append(line.removeprefix("File: "))
    if files:
        joined = ", ".join(files[:3])
        suffix = " and more" if len(files) > 3 else ""
        return f"This commit changes {joined}{suffix}."
    return "This commit changes code related to the flagged decision."


def _find_jwt_decision(decisions: list[dict]) -> dict:
    for decision in decisions:
        searchable = json.dumps(decision).lower()
        if "jwt" in searchable:
            return decision
    return decisions[0] if decisions else {}


def _is_demo_session_auth(diff: str) -> bool:
    lowered = diff.lower()
    return "session-based authentication" in lowered and "reverts the jwt approach" in lowered


def _is_demo_no_violation(diff: str) -> bool:
    lowered = diff.lower()
    readme_changed = "file: readme.md" in lowered or "diff --git a/readme.md b/readme.md" in lowered
    return readme_changed and "## running locally" in lowered


def format_pr_comment(contradiction: dict, sha: str, diff: str = "") -> str:
    d = contradiction["decision"]
    participants = ", ".join(d.get("participants", []))
    date = _format_date(d.get("created_at"))
    diff_summary = _summarize_diff(diff, contradiction)
    return f"""## 🛡️ Covenant — Promise Check
**This change may break a promise your team made.**
**Past decision** (made on **{date}** by {participants}):
> {d.get("summary", "")}
**Their reasoning:**
> {d.get("rationale", "")}
**What this commit does:**
{diff_summary}
**Why I flagged it ({contradiction.get("severity", "unknown")}):**
{contradiction.get("explanation", "")}
---
*Is this intentional? 👍 to confirm (Covenant updates its priors), 👎 to flag for review.*
[View in Covenant →]({COVENANT_URL}/decisions/{d.get("id", "")})"""


async def _post_slack_reply(channel: str, thread_ts: str, text: str):
    from slack_sdk.web.async_client import AsyncWebClient

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

async def process_push(payload: dict):
    from agent.contradiction import find_contradictions

    sha = payload["after"]
    before = payload["before"]
    diff = await get_diff(before, sha)
    decisions = await db.get_all_decisions()

    if os.getenv("MODE") == "DEMO" and _is_demo_session_auth(diff):
        cached = dict(DEMO_CACHE["session"])
        cached["decision"] = _find_jwt_decision(decisions)
        contradictions = [cached]
    elif os.getenv("MODE") == "DEMO" and _is_demo_no_violation(diff):
        contradictions = []
    else:
        contradictions = await find_contradictions(diff, decisions)

    if contradictions:
        top = contradictions[0]
        body = format_pr_comment(top, sha, diff)
        await post_commit_comment(sha, body)
        await db.insert_alert(top, sha, "commit")


async def _process_slack_message(event: dict):
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions

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
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions

    text = data.get("body", "")
    classification = await classify_decision(text)
    if classification["label"] == "DECISION":
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(text, decisions)
        if contradictions:
            await db.insert_alert(contradictions[0], data.get("id"), "linear")


# ── notion poller (started in main.py startup) ────────────────────────────────

async def notion_poller():
    from notion_client import AsyncClient as NotionClient

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
    signature = req.headers.get("x-hub-signature-256")
    if not verify_github_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not payload.get("commits"):
        return {"ok": True}

    bg.add_task(process_push, payload)
    return {"ok": True}


@router.post("/webhooks/slack")
async def slack_webhook(req: Request, bg: BackgroundTasks):
    payload = await req.json()
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    return {"ok": True}


@router.post("/webhooks/linear")
async def linear_webhook(req: Request, bg: BackgroundTasks):
    return {"ok": True}
