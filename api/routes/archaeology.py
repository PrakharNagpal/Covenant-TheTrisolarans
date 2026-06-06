# P2 lane — archaeology route
from fastapi import APIRouter
from pydantic import BaseModel
from agent.archaeology import answer_archaeology

router = APIRouter()


class ArchaeologyRequest(BaseModel):
    question: str


@router.post("/archaeology")
async def archaeology(req: ArchaeologyRequest):
    answer = await answer_archaeology(req.question)
    return {"answer": answer}
