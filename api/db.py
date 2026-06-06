# P2 lane — Supabase database helpers
import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    return _client


async def get_all_decisions() -> list[dict]:
    result = get_client().table("decisions").select("*").execute()
    return result.data or []


async def get_decision_by_id(decision_id: str) -> dict | None:
    result = get_client().table("decisions").select("*").eq("id", decision_id).single().execute()
    return result.data


async def get_lineage_for_decision(decision_id: str) -> list[dict]:
    result = get_client().table("lineage_links").select("*").eq("decision_id", decision_id).execute()
    return result.data or []


async def upsert_decision(decision: dict):
    get_client().table("decisions").upsert(decision).execute()


async def insert_alert(contradiction: dict, source_ref: str, source_type: str):
    alert = {
        "decision_id": contradiction["decision"].get("id"),
        "severity": contradiction.get("severity"),
        "explanation": contradiction.get("explanation"),
        "confidence": contradiction.get("confidence"),
        "source_ref": source_ref,
        "source_type": source_type,
    }
    get_client().table("alerts").insert(alert).execute()


async def get_alerts_since(since: str) -> list[dict]:
    result = (
        get_client()
        .table("alerts")
        .select("*")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
