# Lane: P2 backend
import hashlib
import hmac
import json
import os
import re
import uuid
from urllib.parse import parse_qs
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from adapters.github import (
    get_diff,
    get_pull_request_diff,
    post_commit_comment,
    post_pull_request_comment,
    verify_github_signature,
)
from adapters.linear import post_issue_comment
from adapters.slack import (
    format_slack_overwrite_prompt,
    get_slack_user_name,
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
    signature = signature.removeprefix("sha256=").strip()
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


def format_linear_contradiction_comment(contradiction: dict, new_text: str) -> str:
    d = contradiction["decision"]
    participants = ", ".join(d.get("participants", []))
    date = _format_date(d.get("created_at"))
    explanation = (
        contradiction.get("explanation_detail")
        or contradiction.get("contradiction_explanation")
        or contradiction.get("explanation")
        or "This appears to contradict an earlier decision."
    )
    return f"""## Covenant - Promise Check
This Linear update may break a promise your team made.

**Past decision** (made on **{date}** by {participants}):
> {d.get("summary", "")}

**Their reasoning:**
> {d.get("rationale", "")}

**New Linear update:**
> {new_text}

**Why I flagged it ({contradiction.get("severity", "unknown")}):**
{explanation}

[View in Covenant]({COVENANT_URL}/decisions/{d.get("id", "")})"""


def _linear_issue_id(data: dict) -> str | None:
    issue = data.get("issue")
    if isinstance(issue, dict):
        issue_id = issue.get("id")
        if issue_id:
            return issue_id
    return data.get("issueId")


def _linear_actor(data: dict) -> str:
    actor = data.get("creator") or data.get("assignee") or {}
    if isinstance(actor, dict):
        return actor.get("name") or actor.get("displayName") or actor.get("email") or "Linear"
    return "Linear"


def _linear_issue_text(data: dict) -> str:
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    return "\n\n".join(part for part in [title, description] if part)

async def _process_linear_decision_text(
    text: str,
    source_ref: str,
    issue_id: str | None,
    participant: str,
    created_at: str | None,
):
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions

    if not text:
        print(f"[LINEAR WEBHOOK] empty text for {source_ref}; skipping", flush=True)
        return

    decisions = await db.get_all_decisions()
    contradictions = _same_role_tool_contradictions(text, decisions)
    classification = await classify_decision(text)
    print(
        f"[LINEAR WEBHOOK] classified {source_ref} as {classification.get('label')}",
        flush=True,
    )
    if classification["label"] != "DECISION" and not contradictions:
        return

    existing = await db.get_decision_by_source_ref("linear", source_ref)
    if existing:
        print(f"[LINEAR WEBHOOK] already captured {source_ref}", flush=True)
        return

    if not contradictions:
        contradictions = await find_contradictions(text, decisions)

    new_decision = {
        "id": str(uuid.uuid4()),
        "summary": classification.get("extracted_choice") or text[:200],
        "rationale": text,
        "participants": [participant],
        "source": "linear",
        "source_ref": source_ref,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    }

    if not contradictions:
        await db.upsert_decision(new_decision)
        print(
            f"[LINEAR WEBHOOK] inserted {new_decision['id']} from {source_ref}",
            flush=True,
        )
        return

    existing_alert = await db.get_alert_by_source_ref("linear", source_ref)
    if existing_alert:
        print(f"[LINEAR WEBHOOK] already alerted for {source_ref}", flush=True)
        return

    top = contradictions[0]
    await db.insert_alert(top, source_ref, "linear")
    if not issue_id:
        print("[LINEAR WEBHOOK] contradiction found but issue id missing", flush=True)
        return

    body = format_linear_contradiction_comment(top, text)
    try:
        comment_id = await post_issue_comment(issue_id, body)
    except Exception as exc:
        print(f"[LINEAR WEBHOOK] failed to post contradiction comment: {exc}", flush=True)
        return
    print(
        f"[LINEAR WEBHOOK] posted contradiction comment {comment_id or ''}",
        flush=True,
    )


def _parse_tool_role_decision(text: str) -> tuple[str, str] | None:
    normalized = " ".join(text.lower().strip().split())
    normalized = re.sub(
        r"^(no[,\s]+)?(let'?s|we decided to|we should|should|we will|we'll|"
        r"i am going to|we are going to|i want to|no i want to|going to|going with|"
        r"we're using|we are using|we use|we chose|we picked|we agreed on|"
        r"we'll use|we need to use|we should use|we're going to)\s+(use\s+)?",
        "",
        normalized,
    )
    normalized = re.sub(r"^(we|i)\s+", "", normalized)

    patterns = [
        r"^(?:decided to use|use|choose|chose|picked|select|selected)\s+(?P<tool>.+?)\s+(?:as|for)\s+(?:our|the|a|an)?\s*(?P<role>.+)$",
        r"^(?P<tool>.+?)\s+(?:as|for)\s+(?:our\s+|the\s+|a\s+|an\s+)?(?P<role>.+)$",
        r"^(?P<tool>.+?)\s+is\s+(?:our|the|a|an)\s+(?P<role>.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, normalized)
        if not match:
            continue
        tool = match.group("tool").strip()
        role = re.sub(r"\s+", " ", match.group("role").strip())
        role = re.sub(r"^(?:our|the|a|an)\s+", "", role)
        role = re.sub(r"\bagents\b", "agent", role)
        role = re.sub(r"\bcoding assistant\b", "coding agent", role)
        return tool, role
    return None


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
                f"[DECISION] deterministic contradiction: {old_tool} vs {new_tool} for {role}",
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

def _approval_from_text(text: str) -> bool | None:
    normalized = re.sub(r"[^a-z]", "", text.lower())
    if normalized in {"yes", "y", "approve", "approved", "replace", "overwrite"}:
        return True
    if normalized in {"no", "n", "reject", "rejected", "keep", "cancel"}:
        return False
    return None


async def _apply_pending_overwrite_response(pending: dict, approved: bool):
    channel = pending.get("channel")
    thread_ts = pending.get("thread_ts")
    pending_id = pending.get("id")

    if approved:
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


async def _handle_slack_text_approval(event: dict) -> bool:
    approved = _approval_from_text(event.get("text", ""))
    thread_ts = event.get("thread_ts")
    channel = event.get("channel")
    if approved is None or not thread_ts or not channel:
        return False

    pending = await db.get_pending_overwrite_by_thread(channel, thread_ts)
    if not pending:
        return False

    await _apply_pending_overwrite_response(pending, approved)
    return True


async def process_push(payload: dict):
    sha = payload["after"]
    before = payload["before"]
    repo = (payload.get("repository") or {}).get("full_name")
    print(f"[GITHUB PUSH] processing {repo or 'configured repo'} {before}...{sha}", flush=True)
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
        print(f"[GITHUB PUSH] posted commit comment on {sha}", flush=True)
    else:
        print(f"[GITHUB PUSH] no contradictions for {sha}", flush=True)


async def process_pull_request(payload: dict):
    from agent.contradiction import find_contradictions

    action = payload.get("action")
    number = payload.get("number")
    repo = (payload.get("repository") or {}).get("full_name")
    print(f"[GITHUB PR] received action={action} repo={repo} number={number}", flush=True)
    if action not in {"opened", "synchronize", "reopened", "ready_for_review"}:
        print(f"[GITHUB PR] skipped unsupported action={action}", flush=True)
        return

    pull_request = payload.get("pull_request") or {}
    if pull_request.get("draft"):
        print(f"[GITHUB PR] skipped draft PR #{number}", flush=True)
        return

    if not number:
        print("[GITHUB PR] skipped payload with no PR number", flush=True)
        return

    try:
        diff = await get_pull_request_diff(number, repo)
    except Exception as exc:
        print(f"[GITHUB PR] failed to fetch diff for {repo}#{number}: {exc}", flush=True)
        return
    print(f"[GITHUB PR] fetched diff for {repo}#{number}: {len(diff)} chars", flush=True)

    contradictions = await demo_cache.get_cached_contradictions(diff)
    if contradictions is None:
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(diff, decisions)

    if not contradictions:
        print(f"[GITHUB PR] no contradictions for {repo}#{number}; no comment posted", flush=True)
        return

    top = contradictions[0]
    sha = (pull_request.get("head") or {}).get("sha", "")
    body = format_pr_comment(top, sha, diff)
    try:
        await post_pull_request_comment(number, body, repo)
    except Exception as exc:
        print(f"[GITHUB PR] failed to post comment on {repo}#{number}: {exc}", flush=True)
        return

    source_ref = pull_request.get("html_url") or f"{repo or 'github'}#{number}"
    await db.insert_alert(top, source_ref, "github_pr")
    print(f"[GITHUB PR] posted conversation comment on {repo}#{number}", flush=True)


async def process_slack_message(event: dict):
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions
    import uuid

    text = event.get("text", "")
    if "Covenant - Promise Check" in text:
        print("[SLACK DECISION] skipping Covenant-authored message", flush=True)
        return
    if await _handle_slack_text_approval(event):
        return

    source_ref = f"{event.get('channel', '')}/{event.get('ts', '')}"
    classification = await classify_decision(text)
    print(
        f"[SLACK DECISION] classified {source_ref} as {classification.get('label')}",
        flush=True,
    )
    if classification["label"] == "DECISION":
        participant = await get_slack_user_name(event.get("user"))
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
            "participants": [participant],
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

    await _apply_pending_overwrite_response(
        pending,
        action_id == "covenant_overwrite_yes",
    )

async def process_linear_comment(data: dict):
    print(f"[LINEAR WEBHOOK] processing comment {data.get('id', '')}", flush=True)
    text = data.get("body", "")
    if "Covenant - Promise Check" in text:
        print("[LINEAR WEBHOOK] skipping Covenant-authored comment", flush=True)
        return

    try:
        await _process_linear_decision_text(
            text=text,
            source_ref=f"comment/{data.get('id', '')}",
            issue_id=_linear_issue_id(data),
            participant=_linear_actor(data),
            created_at=data.get("createdAt") or data.get("created_at"),
        )
    except Exception as exc:
        print(f"[LINEAR WEBHOOK] failed to process comment: {exc}", flush=True)


async def process_linear_issue(data: dict):
    print(f"[LINEAR WEBHOOK] processing issue {data.get('id', '')}", flush=True)
    try:
        await _process_linear_decision_text(
            text=_linear_issue_text(data),
            source_ref=f"issue/{data.get('id', '')}",
            issue_id=data.get("id"),
            participant=_linear_actor(data),
            created_at=data.get("createdAt") or data.get("created_at"),
        )
    except Exception as exc:
        print(f"[LINEAR WEBHOOK] failed to process issue: {exc}", flush=True)


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/webhooks/github")
async def github_webhook(req: Request, bg: BackgroundTasks):
    payload_bytes = await req.body()
    signature = req.headers.get("x-hub-signature-256")
    event_type = req.headers.get("x-github-event", "")
    if not verify_github_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid GitHub signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if event_type == "pull_request":
        bg.add_task(process_pull_request, payload)
        return {"ok": True}

    if event_type == "push" or payload.get("commits"):
        if payload.get("commits"):
            bg.add_task(process_push, payload)
        return {"ok": True}

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

    payload_type = (payload.get("type") or "").lower()
    action = (payload.get("action") or "").lower()
    print(f"[LINEAR WEBHOOK] received type={payload_type} action={action}", flush=True)

    if payload_type == "comment" and action in {"create", "update"}:
        print("[LINEAR WEBHOOK] comment create/update received", flush=True)
        bg.add_task(process_linear_comment, payload["data"])
    if payload_type == "issue" and action in {"create", "update"}:
        print("[LINEAR WEBHOOK] issue create/update received", flush=True)
        bg.add_task(process_linear_issue, payload["data"])
    return {"ok": True}
