# Lane: P2 backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api import db

router = APIRouter()


class CheckRequest(BaseModel):
    input: str


class NotionPageCheckRequest(BaseModel):
    page_id: str


@router.post("/check")
async def check_contradiction(req: CheckRequest):
    from agent.contradiction import find_contradictions

    decisions = await db.get_all_decisions()
    return await find_contradictions(req.input, decisions)


@router.post("/check-notion-page")
async def check_notion_page(req: NotionPageCheckRequest):
    from agent.contradiction import find_contradictions
    from adapters.notion import get_page_text, append_contradiction_callout
    from api.routes.webhooks import format_notion_contradiction_comment

    from adapters.notion import _covenant_callout_present

    try:
        text, blocks = await get_page_text(req.page_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch page: {exc}")

    if not text.strip():
        return {"text": "", "contradictions": [], "callout_posted": False}

    decisions = await db.get_all_decisions()
    contradictions = await find_contradictions(text, decisions)

    callout_posted = False
    if contradictions:
        decision_id = (contradictions[0].get("decision") or {}).get("id", "")
        if _covenant_callout_present(blocks, decision_id):
            return {"text": text, "contradictions": contradictions, "callout_posted": False, "note": "callout already on page"}
        message = format_notion_contradiction_comment(contradictions[0])
        try:
            await append_contradiction_callout(req.page_id, message)
            callout_posted = True
        except Exception as exc:
            return {"text": text, "contradictions": contradictions, "callout_posted": False, "callout_error": str(exc)}

    return {"text": text, "contradictions": contradictions, "callout_posted": callout_posted}
