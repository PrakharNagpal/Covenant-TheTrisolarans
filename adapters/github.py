# P2 lane — GitHub adapters
import os
import httpx


class LiveGitHubAdapter:
    async def post_commit_comment(self, sha: str, body: str):
        repo = os.getenv("GITHUB_REPO", "")
        token = os.getenv("GITHUB_TOKEN", "")
        url = f"https://api.github.com/repos/{repo}/commits/{sha}/comments"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"token {token}"},
                json={"body": body},
            )
            resp.raise_for_status()


class SeedGitHubAdapter:
    async def post_commit_comment(self, sha: str, body: str):
        print(f"[SeedGitHubAdapter] Would post comment on {sha}:\n{body}")
