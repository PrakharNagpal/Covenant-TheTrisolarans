# Lane: P2 backend
import hashlib
import hmac
import json
import os
import re
from urllib.parse import parse_qs
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from adapters.github import get_diff, post_commit_comment, verify_github_signature
from adapters.slack import (
    format_slack_overwrite_prompt,
    post_slack_overwrite_prompt,
    post_slack_reply,
)
from api import db, demo_cache

router = APIRouter()

COVENANT_URL = os.getenv("NGROK_URL", "http://localhost:3000")


def _verify_linear_signature(payload_bytes: bytes, signature: str) -> bool:
    secret = os.getenv("LINEAR_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
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
{contradiction.get("explanation_detail") or contradiction.get("contradiction_explanation") or contradiction.get("explanation", "")}
---
*Is this intentional? 👍 to confirm (Covenant updates its priors), 👎 to flag for review.*
[View in Covenant →]({COVENANT_URL}/decisions/{d.get("id", "")})"""


def _parse_tool_role_decision(text: str) -> tuple[str, str] | None:
    normalized = " ".join(text.lower().strip().split())
    normalized = re.sub(r"^(let'?s|we decided to|we will|we'll|i am going to|we are going to)\s+use\s+", "", normalized)
    match = re.match(r"(?P<tool>.+?)\s+as\s+(?:our|the|a|an)\s+(?P<role>.+)$", normalized)
    if not match:
        return None
    return match.group("tool").strip(), match.group("role").strip()


def _same_role_tool_contradictions(
    text: str,
    decisions: list[dict],
) -> list[dict]:
    parsed = _parse_tool_role_decision(text)
    if not parsed:
        return []

    new_tool, role = parsed
    for decision in decisions:
        existing = _parse_tool_role_decision(decision.get("summary", ""))
        if not existing:
            existing = _parse_tool_role_decision(decision.get("rationale", ""))
        if not existing:
            continue

        old_tool, old_role = existing
        if old_role == role and old_tool != new_tool:
            print(
                f"[SLACK DECISION] deterministic contradiction: {old_tool} vs {new_tool} for {role}",
                flush=True,
            )
            return [
                {
                    "contradicts": True,
                    "severity": "structural",
                    "explanation": (
                        f"This chooses {new_tool} as our {role}, contradicting the earlier "
                        f"decision to use {old_tool} as our {role}."
                    ),
                    "confidence": 0.99,
                    "decision": decision,
                }
            ]
    return []


# ── background tasks ─────────────────────────────────────────────────────────

async def process_push(payload: dict):
    sha = payload["after"]
    before = payload["before"]
    diff = await get_diff(before, sha)

    contradictions = await demo_cache.get_cached_contradictions(diff)
    if contradictions is None:
        from agent.contradiction import find_contradictions

        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(diff, decisions)

    if contradictions:
        top = contradictions[0]
        body = format_pr_comment(top, sha, diff)
        await post_commit_comment(sha, body)
        await db.insert_alert(top, sha, "commit")


async def process_slack_message(event: dict):
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions
    import uuid

    text = event.get("text", "")
    source_ref = f"{event.get('channel', '')}/{event.get('ts', '')}"
    classification = await classify_decision(text)
    print(
        f"[SLACK DECISION] classified {source_ref} as {classification.get('label')}",
        flush=True,
    )
    if classification["label"] == "DECISION":
        decisions = await db.get_all_decisions()
        contradictions = _same_role_tool_contradictions(text, decisions)
        if not contradictions:
            contradictions = await find_contradictions(text, decisions)

        created_at = datetime.now(timezone.utc).isoformat()
        if event.get("ts"):
            try:
                created_at = datetime.fromtimestamp(
                    float(event["ts"]),
                    tz=timezone.utc,
                ).isoformat()
            except ValueError:
                pass

        new_decision = {
            "id": str(uuid.uuid4()),
            "summary": classification.get("extracted_choice") or text[:200],
            "rationale": text,
            "participants": [event.get("user", "unknown")],
            "source": "slack",
            "source_ref": source_ref,
            "created_at": created_at,
        }
        existing = await db.get_decision_by_source_ref("slack", source_ref)
        if existing:
            print(f"[SLACK DECISION] already captured {source_ref}", flush=True)
        elif contradictions:
            pending_id = str(uuid.uuid4())
            contradiction_decision_ids = [
                contradiction["decision"]["id"]
                for contradiction in contradictions
                if contradiction.get("decision", {}).get("id")
            ]
            await db.create_pending_overwrite(
                pending_id=pending_id,
                source="slack",
                source_ref=source_ref,
                channel=event["channel"],
                thread_ts=event["ts"],
                new_decision=new_decision,
                contradiction_decision_ids=contradiction_decision_ids,
            )
            print(
                f"[SLACK DECISION] not inserted because contradiction was found for {source_ref}",
                flush=True,
            )
            prompt = format_slack_overwrite_prompt(contradictions[0], new_decision)
            await post_slack_overwrite_prompt(
                event["channel"],
                event["ts"],
                prompt,
                pending_id,
            )
        else:
            await db.upsert_decision(new_decision)
            print(
                f"[SLACK DECISION] inserted {new_decision['id']} from {source_ref}",
                flush=True,
            )

        if contradictions:
            await db.insert_alert(contradictions[0], event["ts"], "slack")


async def process_slack_interaction(payload: dict):
    actions = payload.get("actions") or []
    if not actions:
        return

    action = actions[0]
    pending_id = action.get("value")
    action_id = action.get("action_id")
    if not pending_id or action_id not in {"covenant_overwrite_yes", "covenant_overwrite_no"}:
        return

    pending = await db.get_pending_overwrite(pending_id)
    channel = pending.get("channel") if pending else payload.get("channel", {}).get("id")
    thread_ts = pending.get("thread_ts") if pending else payload.get("message", {}).get("ts")

    if not pending:
        if channel and thread_ts:
            await post_slack_reply(
                channel,
                thread_ts,
                "Covenant could not find that pending decision request. It may have already been handled.",
            )
        return

    if action_id == "covenant_overwrite_yes":
        await db.delete_decisions(pending.get("contradiction_decision_ids") or [])
        await db.upsert_decision(pending["new_decision"])
        await db.delete_pending_overwrite(pending_id)
        await post_slack_reply(
            channel,
            thread_ts,
            "Covenant replaced the conflicting decision and added the new decision to the ledger.",
        )
        return

    await db.delete_pending_overwrite(pending_id)
    await post_slack_reply(
        channel,
        thread_ts,
        "Covenant kept the existing decision. The new contradictory decision was not added.",
    )


async def process_linear_comment(data: dict):
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions

    print(f"[LINEAR WEBHOOK] processing comment {data.get('id', '')}", flush=True)
    text = data.get("body", "")
    classification = await classify_decision(text)
    if classification["label"] == "DECISION":
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(text, decisions)
        if contradictions:
            await db.insert_alert(contradictions[0], data.get("id"), "linear")


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
    content_type = req.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = parse_qs((await req.body()).decode())
        payload = json.loads(form.get("payload", ["{}"])[0])
        bg.add_task(process_slack_interaction, payload)
        return {"ok": True}

    payload = await req.json()
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}
    if payload.get("type") == "event_callback":
        event = payload["event"]
        if event.get("type") == "message" and not event.get("subtype"):
            bg.add_task(process_slack_message, event)
    return {"ok": True}


@router.post("/webhooks/linear")
async def linear_webhook(req: Request, bg: BackgroundTasks):
    payload_bytes = await req.body()
    signature = req.headers.get("linear-signature", "")
    if not _verify_linear_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid Linear signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if payload.get("type") == "Comment" and payload.get("action") == "create":
        print("[LINEAR WEBHOOK] comment create received", flush=True)
        bg.add_task(process_linear_comment, payload["data"])
    return {"ok": True}
