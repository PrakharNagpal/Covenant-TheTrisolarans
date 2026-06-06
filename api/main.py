# P2 lane — FastAPI entry point
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import decisions, check, alerts, archaeology, webhooks

app = FastAPI(title="Covenant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    if os.getenv("NOTION_MODE", "LIVE") == "LIVE":
        from api.routes.webhooks import notion_poller
        asyncio.create_task(notion_poller())
