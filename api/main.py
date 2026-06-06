# Lane: P2 backend
import os
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api import demo_cache
from adapters.notion import notion_poller
from api.routes import alerts, archaeology, check, decisions, webhooks

app = FastAPI(title="Covenant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decisions.router, prefix="/api")
app.include_router(check.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(archaeology.router, prefix="/api")
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {"ok": True}


@app.on_event("startup")
async def startup():
    await demo_cache.load_jwt_decision()
    if os.getenv("NOTION_MODE") == "LIVE":
        asyncio.create_task(notion_poller())
