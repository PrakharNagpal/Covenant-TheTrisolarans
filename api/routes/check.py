# Lane: P2 backend
from fastapi import APIRouter
from pydantic import BaseModel

from api import db

router = APIRouter()


class CheckRequest(BaseModel):
    input: str


@router.post("/check")
async def check_contradiction(req: CheckRequest):
    from agent.contradiction import find_contradictions

    decisions = await db.get_all_decisions()
    return await find_contradictions(req.input, decisions)
