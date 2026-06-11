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
    """Classify + store new decisions from watched pages, then check for contradictions."""
    import uuid
    from datetime import datetime, timezone
    from agent.classifier import classify_decision
    from agent.contradiction import find_contradictions
    from api.routes.webhooks import format_notion_contradiction_comment

    raw = os.getenv("NOTION_WATCHED_PAGES", "").strip()
    if not raw:
        return

    page_ids = [p.strip() for p in raw.split(",") if p.strip()]

    for page_id in page_ids:
        try:
            text, blocks = await get_page_text(page_id)
        except Exception as exc:
            print(f"[NOTION PAGE POLLER] failed to fetch {page_id}: {exc}", flush=True)
            continue

        if not text.strip():
            continue

        # ── 1. Store new decisions from individual blocks ─────────────────────
        new_blocks = []
        for block in blocks:
            block_type = block.get("type")
            if block_type not in _TEXT_BLOCK_TYPES:
                continue
            block_text = _plain_text(block.get(block_type, {}).get("rich_text"))
            if not block_text.strip():
                continue
            block_id = block.get("id", "")
            source_ref = f"notion-page/{page_id}/{block_id}"
            existing = await db.get_decision_by_source_ref("notion", source_ref)
            if not existing:
                new_blocks.append((block_text, source_ref))

        if new_blocks:
            classifications = await asyncio.gather(
                *(classify_decision(bt) for bt, _ in new_blocks)
            )
            for (block_text, source_ref), classification in zip(new_blocks, classifications):
                if classification.get("label") == "DECISION":
                    new_decision = {
                        "id": str(uuid.uuid4()),
                        "summary": classification.get("extracted_choice") or block_text[:200],
                        "rationale": block_text,
                        "participants": [],
                        "source": "notion",
                        "source_ref": source_ref,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    await db.upsert_decision(new_decision)
                    print(f"[NOTION PAGE POLLER] stored decision: {new_decision['summary'][:60]}", flush=True)

        # ── 2. Check full page text for contradictions ────────────────────────
        decisions = await db.get_all_decisions()
        contradictions = await find_contradictions(text, decisions)
        if not contradictions:
            continue

        top = contradictions[0]
        decision_id = (top.get("decision") or {}).get("id", "")

        if _covenant_callout_present(blocks, decision_id):
            continue

        source_ref = f"notion/{page_id}/{decision_id}"
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


async def get_page_blocks(page_id: str) -> list[dict]:
    notion = NotionClient(auth=os.getenv("NOTION_TOKEN", ""))
    response = await notion.blocks.children.list(block_id=page_id)
    blocks = response.get("results", [])

    all_blocks: list[dict] = []
    for block in blocks:
        all_blocks.append(block)
        if block.get("has_children"):
            child_blocks = await get_page_blocks(block["id"])
            all_blocks.extend(child_blocks)

    return all_blocks


def _covenant_callout_present(blocks: list[dict], decision_id: str) -> bool:
    """Return True if the page already has a Covenant callout for this decision."""
    for block in blocks:
        if block.get("type") != "callout":
            continue
        callout_text = _plain_text(block.get("callout", {}).get("rich_text"))
        if "Covenant" in callout_text and decision_id in callout_text:
            return True
    return False


async def get_page_text(page_id: str) -> tuple[str, list[dict]]:
    blocks = await get_page_blocks(page_id)
    texts = []
    for block in blocks:
        block_type = block.get("type")
        if block_type not in _TEXT_BLOCK_TYPES:
            continue
        content = block.get(block_type, {})
        text = _plain_text(content.get("rich_text"))
        if text:
            texts.append(text)
    return "\n".join(texts), blocks


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
