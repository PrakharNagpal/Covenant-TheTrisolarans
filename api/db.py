import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json

_client: Any | None = None
_demo_decisions: list[dict] | None = None
_demo_lineage: list[dict] | None = None
_seed_lineage_keys: set[tuple[str | None, str | None]] | None = None
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


def _load_seed_lineage_keys() -> set[tuple[str | None, str | None]]:
    global _seed_lineage_keys
    if _seed_lineage_keys is None:
        _seed_lineage_keys = {
            (link.get("decision_id"), link.get("artifact_ref"))
            for link in _load_json("lineage_links.json")
        }
    return _seed_lineage_keys


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slack_source_url(source_ref: str) -> str:
    if "/" not in source_ref:
        return source_ref

    channel, ts = source_ref.split("/", 1)
    compact_ts = ts.replace(".", "")
    workspace_url = os.getenv("SLACK_WORKSPACE_URL", "").rstrip("/")
    if workspace_url:
        return f"{workspace_url}/archives/{channel}/p{compact_ts}"

    team_id = os.getenv("SLACK_TEAM_ID", "")
    if team_id:
        return f"https://app.slack.com/client/{team_id}/{channel}/thread/{channel}-{compact_ts}"

    return source_ref


def _source_artifact(
    decision_id: str,
    source: str | None,
    source_ref: str,
    row_id: str,
    note: str | None = None,
) -> dict:
    normalized_source = (source or "source").lower()
    artifact_ref = source_ref
    artifact_type = normalized_source
    source_name = normalized_source.replace("_", " ").title()

    if "slack" in normalized_source:
        artifact_type = "slack_message"
        artifact_ref = _slack_source_url(source_ref)
        source_name = "Slack message"
    elif "notion" in normalized_source:
        artifact_type = "notion_page"
        source_name = "Notion page"
    elif "linear" in normalized_source:
        artifact_type = "linear"
        source_name = "Linear update"
    elif "github_pr" in normalized_source:
        artifact_type = "github_pr"
        source_name = "GitHub PR"
    elif "github" in normalized_source or "commit" in normalized_source:
        artifact_type = "github"
        source_name = "GitHub source"

    return {
        "id": row_id,
        "decision_id": decision_id,
        "artifact_type": artifact_type,
        "artifact_ref": artifact_ref,
        "source_ref": source_ref,
        "note": note or f"Original decision source: {source_name}.",
    }


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


async def insert_lineage_links(decision_id: str | None, links: list[dict]):
    if not decision_id or not links:
        return

    rows = [
        {
            "decision_id": decision_id,
            "artifact_type": link.get("artifact_type") or link.get("type") or "artifact",
            "artifact_ref": link.get("artifact_ref") or link.get("target") or "",
            "note": link.get("note"),
        }
        for link in links
        if link.get("artifact_ref") or link.get("target")
    ]
    if not rows:
        return

    if _is_demo_mode():
        lineage = _load_demo_lineage()
        existing_refs = {
            (link.get("decision_id"), link.get("artifact_ref"))
            for link in lineage
        }
        for row in rows:
            key = (row["decision_id"], row["artifact_ref"])
            if key in existing_refs:
                continue
            lineage.append(
                {
                    "id": f"demo-lineage-{len(lineage) + 1}",
                    **row,
                    "created_at": _now_iso(),
                }
            )
            existing_refs.add(key)
        return

    def insert_missing():
        client = get_client()
        for row in rows:
            existing = (
                client.table("lineage_links")
                .select("id")
                .eq("decision_id", row["decision_id"])
                .eq("artifact_ref", row["artifact_ref"])
                .limit(1)
                .execute()
            )
            if existing.data:
                continue
            client.table("lineage_links").insert(row).execute()

    await _run_sync(insert_missing)


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
    return result.data if result else None


async def get_lineage(decision_id: str) -> list[dict]:
    decision = await get_decision(decision_id)

    if _is_demo_mode():
        links = [
            link
            for link in _load_demo_lineage()
            if link.get("decision_id") == decision_id
        ]
        if decision and decision.get("source_ref"):
            links.insert(
                0,
                _source_artifact(
                    decision_id,
                    decision.get("source"),
                    decision["source_ref"],
                    f"{decision_id}-source",
                ),
            )
        for alert in _demo_alerts:
            if alert.get("decision_id") != decision_id or not alert.get("source_ref"):
                continue
            links.append(
                _source_artifact(
                    decision_id,
                    alert.get("source") or "alert",
                    alert["source_ref"],
                    f"{alert.get('id')}-source",
                    alert.get("message") or alert.get("contradiction_explanation"),
                )
            )
        return links

    def query_lineage():
        client = get_client()
        lineage_result = (
            client.table("lineage_links")
            .select("*")
            .eq("decision_id", decision_id)
            .order("created_at", desc=False)
            .execute()
        )
        alert_result = (
            client.table("alerts")
            .select("*")
            .eq("decision_id", decision_id)
            .order("created_at", desc=False)
            .execute()
        )
        return lineage_result.data or [], alert_result.data or []

    lineage_rows, alert_rows = await _run_sync(query_lineage)
    seed_lineage_keys = _load_seed_lineage_keys()
    links = [
        link
        for link in lineage_rows
        if (link.get("decision_id"), link.get("artifact_ref")) not in seed_lineage_keys
    ]

    if decision and decision.get("source_ref"):
        links.insert(
            0,
            _source_artifact(
                decision_id,
                decision.get("source"),
                decision["source_ref"],
                f"{decision_id}-source",
            ),
        )

    existing_refs = {link.get("artifact_ref") for link in links}
    for alert in alert_rows:
        source_ref = alert.get("source_ref")
        if not source_ref:
            continue
        artifact = _source_artifact(
            decision_id,
            alert.get("source") or "alert",
            source_ref,
            f"{alert.get('id')}-source",
            alert.get("message") or alert.get("contradiction_explanation"),
        )
        if artifact["artifact_ref"] in existing_refs:
            continue
        links.append(artifact)
        existing_refs.add(artifact["artifact_ref"])

    return links


get_decision_by_id = get_decision
get_lineage_for_decision = get_lineage
get_alerts_since = get_alerts
