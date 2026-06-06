# Lane: P2 backend
import asyncio
import os
from typing import Any, Callable

from supabase import Client, create_client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        _client = create_client(url, key)
    return _client


async def _run_sync(fn: Callable[[], Any]) -> Any:
    return await asyncio.to_thread(fn)


async def get_all_decisions() -> list[dict]:
    result = await _run_sync(lambda: get_client().table("decisions").select("*").execute())
    return result.data or []


async def upsert_decision(decision: dict):
    await _run_sync(lambda: get_client().table("decisions").upsert(decision).execute())


async def insert_alert(contradiction: dict, source_ref: str, source: str):
    decision = contradiction.get("decision") or {}
    message = contradiction.get("message") or contradiction.get("explanation")
    alert = {
        "decision_id": decision.get("id") or contradiction.get("decision_id"),
        "severity": contradiction.get("severity"),
        "source": source,
        "source_ref": source_ref,
        "message": message,
        "status": "open",
        "contradiction_explanation": contradiction.get("explanation"),
    }
    await _run_sync(lambda: get_client().table("alerts").insert(alert).execute())


async def get_alerts(since: str | None = None) -> list[dict]:
    def query():
        builder = get_client().table("alerts").select("*").order("created_at", desc=True)
        if since:
            builder = builder.gte("created_at", since)
        return builder.execute()

    result = await _run_sync(query)
    return result.data or []


async def get_decision(decision_id: str) -> dict | None:
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
