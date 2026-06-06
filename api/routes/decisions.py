# Lane: P2 backend
from fastapi import APIRouter

from api import db

router = APIRouter()


@router.get("/decisions")
async def list_decisions():
    return await db.get_all_decisions()


@router.get("/decisions/{decision_id}")
async def get_decision(decision_id: str):
    return await db.get_decision(decision_id)


@router.get("/decisions/{decision_id}/lineage")
async def get_lineage(decision_id: str):
    return await db.get_lineage(decision_id)
