# Lane: P2 backend
from fastapi import APIRouter, Query

from api import db

router = APIRouter()


@router.get("/alerts")
async def get_alerts(since: str | None = Query(default=None)):
    return await db.get_alerts(since)
