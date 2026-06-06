# Lane: P2 backend
import asyncio
import json
import os

from notion_client import AsyncClient as NotionClient

from api import db


def _plain_text(items: list[dict] | None) -> str:
    return "".join(item.get("plain_text", "") for item in (items or [])).strip()


def _title(prop: dict | None) -> str:
    return _plain_text((prop or {}).get("title"))


def _rich_text(prop: dict | None) -> str:
    return _plain_text((prop or {}).get("rich_text"))


def _participants(prop: dict | None) -> list[str]:
    text = _rich_text(prop)
    return [part.strip() for part in text.split(",") if part.strip()]


def row_to_decision(row: dict) -> dict:
    props = row.get("properties", {})
    return {
        "id": row["id"],
        "summary": _title(props.get("Decision")),
        "rationale": _rich_text(props.get("Rationale")),
        "participants": _participants(props.get("Participants")),
        "source": "notion",
        "created_at": row.get("created_time"),
    }


async def query_notion_decisions() -> list[dict]:
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN", ""))
    database_id = os.getenv("NOTION_DATABASE_ID", "")
    response = await notion.databases.query(database_id=database_id)
    return [row_to_decision(row) for row in response.get("results", [])]


async def poll_notion_once() -> int:
    decisions = await query_notion_decisions()
    for decision in decisions:
        await db.upsert_decision(decision)
    print(f"[NOTION POLLER] successful query; upserted {len(decisions)} decisions", flush=True)
    return len(decisions)


async def notion_poller():
    while True:
        try:
            await poll_notion_once()
        except Exception as exc:
            print(f"[NOTION POLLER] error: {exc}", flush=True)
        await asyncio.sleep(60)


class SeedNotionAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "decisions.json")
        with open(path) as f:
            self._decisions = json.load(f)

    def get_decisions(self) -> list[dict]:
        return self._decisions
