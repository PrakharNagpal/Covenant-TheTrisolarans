# P2 lane — alerts route
from fastapi import APIRouter, Query
from api import db

router = APIRouter()


@router.get("/alerts")
async def get_alerts(since: str = Query(default="1970-01-01T00:00:00Z")):
    return await db.get_alerts_since(since)
