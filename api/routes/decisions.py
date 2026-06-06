# P2 lane — decisions routes
from fastapi import APIRouter
from api import db

router = APIRouter()


@router.get("/decisions")
async def list_decisions():
    return await db.get_all_decisions()


@router.get("/decisions/{decision_id}")
async def get_decision(decision_id: str):
    return await db.get_decision_by_id(decision_id)


@router.get("/decisions/{decision_id}/lineage")
async def get_lineage(decision_id: str):
    return await db.get_lineage_for_decision(decision_id)
