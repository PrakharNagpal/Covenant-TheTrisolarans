# P2 lane — seed Supabase with decisions and lineage links
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI
from supabase import create_client

openai_client = AsyncOpenAI()


async def embed(text: str) -> list[float]:
    resp = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding


async def main():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    with open(os.path.join(data_dir, "decisions.json")) as f:
        decisions = json.load(f)

    with open(os.path.join(data_dir, "lineage_links.json")) as f:
        lineage_links = json.load(f)

    print(f"Seeding {len(decisions)} decisions...")
    for decision in decisions:
        text = f"{decision.get('summary', '')} {decision.get('rationale', '')}"
        embedding = await embed(text)
        decision["embedding"] = embedding
        supabase.table("decisions").upsert(decision).execute()
        print(f"  ✅ {decision.get('id')} — {decision.get('summary', '')[:60]}")

    print(f"\nSeeding {len(lineage_links)} lineage links...")
    for link in lineage_links:
        supabase.table("lineage_links").upsert(link).execute()
        print(f"  ✅ {link.get('id')} — {link.get('file_path', '')}")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(main())
