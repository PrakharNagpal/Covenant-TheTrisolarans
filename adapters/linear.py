# Lane: P2 backend
import os

import httpx


LINEAR_API = "https://api.linear.app/graphql"


def _headers() -> dict[str, str]:
    token = os.getenv("LINEAR_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    return headers


async def linear_query(query: str, variables: dict | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LINEAR_API,
            headers=_headers(),
            json={"query": query, "variables": variables or {}},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("errors"):
        raise RuntimeError(f"Linear API error: {data['errors']}")
    return data.get("data") or {}


async def post_issue_comment(issue_id: str, body: str) -> str | None:
    data = await linear_query(
        """
        mutation CreateComment($issueId: String!, $body: String!) {
            commentCreate(input: { issueId: $issueId, body: $body }) {
                success
                comment { id }
            }
        }
        """,
        {"issueId": issue_id, "body": body},
    )
    comment_create = data.get("commentCreate") or {}
    comment = comment_create.get("comment") or {}
    return comment.get("id")
