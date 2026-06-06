# Lane: P2 backend
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ArchaeologyRequest(BaseModel):
    question: str


@router.post("/archaeology")
async def archaeology(req: ArchaeologyRequest):
    from agent.archaeology import answer_archaeology

    return await answer_archaeology(req.question)
