"""
Register a Notion webhook subscription so Notion sends page-update events
to /webhooks/notion.

Usage:
    python scripts/register_notion_webhook.py

Requires in .env:
    NOTION_TOKEN            — your integration's internal token
    RENDER_EXTERNAL_URL     — set automatically by Render in production
    NGROK_URL               — fallback for local dev
"""
import asyncio
import os

from dotenv import load_dotenv
from notion_client import AsyncClient as NotionClient

load_dotenv()


async def main():
    token = os.getenv("NOTION_TOKEN", "")
    # RENDER_EXTERNAL_URL is injected automatically by Render; fall back to ngrok for local dev
    base_url = (
        os.getenv("RENDER_EXTERNAL_URL")
        or os.getenv("NGROK_URL")
        or "http://localhost:8000"
    ).rstrip("/")

    if not token:
        raise SystemExit("NOTION_TOKEN is not set in .env")

    webhook_url = f"{base_url}/webhooks/notion"
    notion = NotionClient(auth=token)

    print(f"Registering Notion webhook → {webhook_url}")
    try:
        result = await notion.request(
            method="POST",
            path="webhooks",
            body={
                "url": webhook_url,
                "subscriptions": [
                    {"type": "page", "actions": ["created", "updated"]},
                    {"type": "block", "actions": ["created", "updated"]},
                ],
            },
        )
        print("Registered successfully:")
        print(f"  id:  {result.get('id')}")
        print(f"  url: {result.get('url')}")
        print()
        print("No signing secret is used — all incoming requests are accepted.")
    except Exception as exc:
        print(f"Failed to register webhook: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
