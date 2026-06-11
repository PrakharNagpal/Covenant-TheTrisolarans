"""
Register a Notion webhook subscription so Notion sends page-update events
to /webhooks/notion.

Usage:
    python scripts/register_notion_webhook.py
    RENDER_EXTERNAL_URL=https://covenant-thetrisolarans.onrender.com python scripts/register_notion_webhook.py
"""
import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

NOTION_API = "https://api.notion.com/v1"


async def main():
    token = os.getenv("NOTION_TOKEN", "")
    base_url = (
        os.getenv("RENDER_EXTERNAL_URL")
        or os.getenv("NGROK_URL")
        or "http://localhost:8000"
    ).rstrip("/")

    if not token:
        raise SystemExit("NOTION_TOKEN is not set in .env")

    webhook_url = f"{base_url}/webhooks/notion"
    print(f"Registering Notion webhook → {webhook_url}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API}/webhooks",
            headers=headers,
            json={
                "url": webhook_url,
                "subscriptions": [
                    {"type": "page", "actions": ["created", "updated"]},
                    {"type": "block", "actions": ["created", "updated"]},
                ],
            },
        )

    print(f"Status: {response.status_code}")
    data = response.json()

    if response.is_success:
        print(f"Registered successfully:")
        print(f"  id:  {data.get('id')}")
        print(f"  url: {data.get('url')}")
    else:
        print(f"Failed: {data}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
