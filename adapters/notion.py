# Lane: P2 backend
import asyncio
import hashlib
import hmac
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
        "source_ref": row.get("url") or row.get("id"),
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


async def poll_meeting_pages_once() -> None:
    """Check each page in NOTION_WATCHED_PAGES for contradictions and post callouts."""
    from agent.contradiction import find_contradictions
    from api.routes.webhooks import format_notion_contradiction_comment

    raw = os.getenv("NOTION_WATCHED_PAGES", "").strip()
    if not raw:
        return

    page_ids = [p.strip() for p in raw.split(",") if p.strip()]
    decisions = await db.get_all_decisions()

    for page_id in page_ids:
        try:
            text = await get_page_text(page_id)
        except Exception as exc:
            print(f"[NOTION PAGE POLLER] failed to fetch {page_id}: {exc}", flush=True)
            continue

        if not text.strip():
            continue

        contradictions = await find_contradictions(text, decisions)
        if not contradictions:
            continue

        top = contradictions[0]
        decision_id = (top.get("decision") or {}).get("id", "")
        # Include a short hash of the page text so new content produces a new key
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
        source_ref = f"notion/{page_id}/{decision_id}/{text_hash}"

        existing = await db.get_alert_by_source_ref("notion", source_ref)
        if existing:
            continue

        await db.insert_alert(top, source_ref, "notion")
        message = format_notion_contradiction_comment(top)
        try:
            await append_contradiction_callout(page_id, message)
            print(f"[NOTION PAGE POLLER] posted callout on {page_id}", flush=True)
        except Exception as exc:
            print(f"[NOTION PAGE POLLER] failed to post callout on {page_id}: {exc}", flush=True)


async def notion_poller():
    while True:
        try:
            await poll_notion_once()
        except Exception as exc:
            print(f"[NOTION POLLER] error: {exc}", flush=True)
        try:
            await poll_meeting_pages_once()
        except Exception as exc:
            print(f"[NOTION PAGE POLLER] error: {exc}", flush=True)
        await asyncio.sleep(30)


_TEXT_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "to_do",
    "toggle",
    "quote",
}


async def get_page_text(page_id: str) -> str:
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN", ""))
    response = await notion.blocks.children.list(block_id=page_id)
    texts = []
    for block in response.get("results", []):
        block_type = block.get("type")
        if block_type not in _TEXT_BLOCK_TYPES:
            continue
        content = block.get(block_type, {})
        text = _plain_text(content.get("rich_text"))
        if text:
            texts.append(text)
    return "\n".join(texts)


async def append_contradiction_callout(page_id: str, message: str) -> None:
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN", ""))
    await notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": message[:2000]},
                        }
                    ],
                    "icon": {"type": "emoji", "emoji": "⚠️"},
                    "color": "red_background",
                },
            }
        ],
    )


def verify_notion_signature(payload_bytes: bytes, signature: str) -> bool:
    secret = os.getenv("NOTION_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False
    hex_sig = signature.removeprefix("sha256=").strip()
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(hex_sig, expected)


class SeedNotionAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "decisions.json")
        with open(path) as f:
            self._decisions = json.load(f)

    def get_decisions(self) -> list[dict]:
        return self._decisions
