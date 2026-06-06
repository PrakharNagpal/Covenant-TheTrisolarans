# Lane: P2 backend
import hashlib
import hmac
import os

import httpx


def _repo(repo: str | None = None) -> str:
    return repo or os.getenv("GITHUB_REPO", "")


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def verify_github_signature(payload_bytes: bytes, signature: str | None) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def get_diff(before: str, after: str, repo: str | None = None) -> str:
    url = f"https://api.github.com/repos/{_repo(repo)}/compare/{before}...{after}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    patches = []
    for file in data.get("files", []):
        patch = file.get("patch")
        if patch:
            patches.append(f"File: {file['filename']}\n{patch}")
    return "\n\n".join(patches)


async def get_pull_request_diff(number: int, repo: str | None = None) -> str:
    patches = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            url = f"https://api.github.com/repos/{_repo(repo)}/pulls/{number}/files"
            resp = await client.get(
                url,
                headers=_headers(),
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            files = resp.json()
            for file in files:
                patch = file.get("patch")
                if patch:
                    patches.append(f"File: {file['filename']}\n{patch}")
            if len(files) < 100:
                break
            page += 1
    return "\n\n".join(patches)


async def post_commit_comment(sha: str, body: str, repo: str | None = None):
    url = f"https://api.github.com/repos/{_repo(repo)}/commits/{sha}/comments"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers=_headers(),
            json={"body": body},
        )
        resp.raise_for_status()


async def post_pull_request_comment(number: int, body: str, repo: str | None = None):
    url = f"https://api.github.com/repos/{_repo(repo)}/issues/{number}/comments"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers=_headers(),
            json={"body": body},
        )
        resp.raise_for_status()


class LiveGitHubAdapter:
    async def post_commit_comment(self, sha: str, body: str):
        await post_commit_comment(sha, body)

    async def post_pull_request_comment(self, number: int, body: str):
        await post_pull_request_comment(number, body)


class SeedGitHubAdapter:
    async def post_commit_comment(self, sha: str, body: str):
        print(f"[SeedGitHubAdapter] Would post comment on {sha}:\n{body}")

    async def post_pull_request_comment(self, number: int, body: str):
        print(f"[SeedGitHubAdapter] Would post comment on PR #{number}:\n{body}")
