# Lane: P2 backend
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI
from supabase import create_client

openai_client = AsyncOpenAI()
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


async def embed(text: str) -> list[float]:
    resp = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding


async def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    supabase = create_client(supabase_url, supabase_key)

    with (DATA_DIR / "decisions.json").open() as f:
        decisions = json.load(f)

    with (DATA_DIR / "lineage_links.json").open() as f:
        lineage_links = json.load(f)

    print(f"Seeding {len(decisions)} decisions...")
    decision_rows = []
    for decision in decisions:
        text = f"{decision.get('summary', '')} {decision.get('rationale', '')}"
        embedding = await embed(text)
        decision_rows.append({**decision, "embedding": embedding})
        print(f"  embedded {decision.get('id')} - {decision.get('summary', '')[:60]}")

    supabase.table("decisions").upsert(decision_rows, on_conflict="id").execute()

    print(f"\nSeeding {len(lineage_links)} lineage links...")
    decision_ids = [decision["id"] for decision in decisions]
    supabase.table("lineage_links").delete().in_("decision_id", decision_ids).execute()

    lineage_rows = [
        {
            "decision_id": link["decision_id"],
            "artifact_type": link["artifact_type"],
            "artifact_ref": link["artifact_ref"],
        }
        for link in lineage_links
    ]
    supabase.table("lineage_links").insert(lineage_rows).execute()

    decision_count = (
        supabase.table("decisions")
        .select("id", count="exact")
        .in_("id", decision_ids)
        .execute()
        .count
    )
    lineage_count = (
        supabase.table("lineage_links")
        .select("decision_id", count="exact")
        .in_("decision_id", decision_ids)
        .execute()
        .count
    )

    print("\nSeed complete.")
    print(f"decisions: {decision_count}")
    print(f"lineage_links: {lineage_count}")


if __name__ == "__main__":
    asyncio.run(main())
