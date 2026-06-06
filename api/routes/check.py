# P2 lane — check route (manual contradiction check)
from fastapi import APIRouter
from pydantic import BaseModel
from agent.contradiction import find_contradictions
from api import db

router = APIRouter()


class CheckRequest(BaseModel):
    text: str


@router.post("/check")
async def check_contradiction(req: CheckRequest):
    decisions = await db.get_all_decisions()
    contradictions = await find_contradictions(req.text, decisions)
    return {"contradictions": contradictions}
