import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json

_client: Any | None = None
_demo_decisions: list[dict] | None = None
_demo_lineage: list[dict] | None = None
_demo_alerts: list[dict] = []
_demo_pending_overwrites: dict[str, dict] = {}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _is_demo_mode() -> bool:
    return os.getenv("MODE") == "DEMO" or not (
        os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY")
    )


def _load_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    return json.loads(path.read_text())


def _load_demo_decisions() -> list[dict]:
    global _demo_decisions
    if _demo_decisions is None:
        _demo_decisions = _load_json("decisions.json")
    return _demo_decisions


def _load_demo_lineage() -> list[dict]:
    global _demo_lineage
    if _demo_lineage is None:
        _demo_lineage = _load_json("lineage_links.json")
    return _demo_lineage


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _demo_alert_from_contradiction(
    contradiction: dict,
    source_ref: str,
    source: str,
) -> dict:
    decision = contradiction.get("decision") or {}
    return {
        "id": f"demo-alert-{len(_demo_alerts) + 1}",
        "decision_id": decision.get("id") or contradiction.get("decision_id"),
        "severity": contradiction.get("severity", "structural"),
        "source": source,
        "source_ref": source_ref,
        "message": contradiction.get("message")
        or contradiction.get("explanation")
        or "A contradiction was detected.",
        "status": "open",
        "contradiction_explanation": contradiction.get("explanation"),
        "created_at": _now_iso(),
        "decision": decision or None,
    }


def get_client() -> Any:
    global _client
    if _client is None:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        _client = create_client(url, key)
    return _client


async def _run_sync(fn: Callable[[], Any]) -> Any:
    return await asyncio.to_thread(fn)


async def get_all_decisions() -> list[dict]:
    if _is_demo_mode():
        return _load_demo_decisions()

    result = await _run_sync(lambda: get_client().table("decisions").select("*").execute())
    return result.data or []


async def upsert_decision(decision: dict):
    if _is_demo_mode():
        decisions = _load_demo_decisions()
        decision_id = decision.get("id")
        for index, existing in enumerate(decisions):
            if existing.get("id") == decision_id:
                decisions[index] = {**existing, **decision}
                return
        decisions.append(decision)
        return

    await _run_sync(lambda: get_client().table("decisions").upsert(decision).execute())


async def delete_decisions(decision_ids: list[str]):
    if not decision_ids:
        return

    if _is_demo_mode():
        decisions = _load_demo_decisions()
        decisions[:] = [
            decision
            for decision in decisions
            if decision.get("id") not in set(decision_ids)
        ]
        return

    await _run_sync(
        lambda: get_client().table("decisions").delete().in_("id", decision_ids).execute()
    )


async def get_decision_by_source_ref(source: str, source_ref: str) -> dict | None:
    if _is_demo_mode():
        return next(
            (
                decision
                for decision in _load_demo_decisions()
                if decision.get("source") == source
                and decision.get("source_ref") == source_ref
            ),
            None,
        )

    result = await _run_sync(
        lambda: get_client()
        .table("decisions")
        .select("*")
        .eq("source", source)
        .eq("source_ref", source_ref)
        .maybe_single()
        .execute()
    )
    if result is None:
        return None
    return result.data


async def create_pending_overwrite(
    pending_id: str,
    source: str,
    source_ref: str,
    channel: str,
    thread_ts: str,
    new_decision: dict,
    contradiction_decision_ids: list[str],
):
    pending = {
        "id": pending_id,
        "source": source,
        "source_ref": source_ref,
        "channel": channel,
        "thread_ts": thread_ts,
        "new_decision": new_decision,
        "contradiction_decision_ids": contradiction_decision_ids,
    }

    if _is_demo_mode():
        _demo_pending_overwrites[pending_id] = pending
        return

    await _run_sync(
        lambda: get_client()
        .table("pending_decision_overwrites")
        .upsert(pending, on_conflict="id")
        .execute()
    )


async def get_pending_overwrite(pending_id: str) -> dict | None:
    if _is_demo_mode():
        return _demo_pending_overwrites.get(pending_id)

    result = await _run_sync(
        lambda: get_client()
        .table("pending_decision_overwrites")
        .select("*")
        .eq("id", pending_id)
        .maybe_single()
        .execute()
    )
    return result.data if result else None


async def get_pending_overwrite_by_thread(channel: str, thread_ts: str) -> dict | None:
    if _is_demo_mode():
        matches = [
            pending
            for pending in _demo_pending_overwrites.values()
            if pending.get("channel") == channel and pending.get("thread_ts") == thread_ts
        ]
        return matches[-1] if matches else None

    result = await _run_sync(
        lambda: get_client()
        .table("pending_decision_overwrites")
        .select("*")
        .eq("channel", channel)
        .eq("thread_ts", thread_ts)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


async def delete_pending_overwrite(pending_id: str):
    if _is_demo_mode():
        _demo_pending_overwrites.pop(pending_id, None)
        return

    await _run_sync(
        lambda: get_client()
        .table("pending_decision_overwrites")
        .delete()
        .eq("id", pending_id)
        .execute()
    )


async def insert_alert(contradiction: dict, source_ref: str, source: str):
    if _is_demo_mode():
        _demo_alerts.insert(
            0,
            _demo_alert_from_contradiction(contradiction, source_ref, source),
        )
        return

    decision = contradiction.get("decision") or {}
    message = contradiction.get("message") or contradiction.get("explanation")
    contradiction_explanation = (
        contradiction.get("explanation_detail")
        or contradiction.get("contradiction_explanation")
        or contradiction.get("explanation")
        or message
    )
    alert = {
        "decision_id": decision.get("id") or contradiction.get("decision_id"),
        "severity": contradiction.get("severity"),
        "source": source,
        "source_ref": source_ref,
        "message": message,
        "status": "open",
        "contradiction_explanation": contradiction_explanation,
    }
    await _run_sync(lambda: get_client().table("alerts").insert(alert).execute())


async def get_alert_by_source_ref(source: str, source_ref: str) -> dict | None:
    if _is_demo_mode():
        return next(
            (
                alert
                for alert in _demo_alerts
                if alert.get("source") == source
                and alert.get("source_ref") == source_ref
            ),
            None,
        )

    result = await _run_sync(
        lambda: get_client()
        .table("alerts")
        .select("*")
        .eq("source", source)
        .eq("source_ref", source_ref)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


async def get_alerts(since: str | None = None) -> list[dict]:
    if _is_demo_mode():
        if not since:
            return _demo_alerts

        try:
            seen_at = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            return _demo_alerts

        return [
            alert
            for alert in _demo_alerts
            if datetime.fromisoformat(alert["created_at"]) >= seen_at
        ]

    def query():
        builder = get_client().table("alerts").select("*").order("created_at", desc=True)
        if since:
            builder = builder.gte("created_at", since)
        return builder.execute()

    result = await _run_sync(query)
    return result.data or []


async def get_decision(decision_id: str) -> dict | None:
    if _is_demo_mode():
        return next(
            (
                decision
                for decision in _load_demo_decisions()
                if decision.get("id") == decision_id
            ),
            None,
        )

    result = await _run_sync(
        lambda: get_client()
        .table("decisions")
        .select("*")
        .eq("id", decision_id)
        .maybe_single()
        .execute()
    )
    return result.data


async def get_lineage(decision_id: str) -> list[dict]:
    if _is_demo_mode():
        return [
            link
            for link in _load_demo_lineage()
            if link.get("decision_id") == decision_id
        ]

    result = await _run_sync(
        lambda: get_client()
        .table("lineage_links")
        .select("*")
        .eq("decision_id", decision_id)
        .execute()
    )
    return result.data or []


get_decision_by_id = get_decision
get_lineage_for_decision = get_lineage
get_alerts_since = get_alerts
