# P2 lane — adapter factory, reads MODE env vars and returns correct adapter
import os


def get_github_adapter():
    from adapters.github import LiveGitHubAdapter, SeedGitHubAdapter
    return LiveGitHubAdapter() if os.getenv("GITHUB_MODE", "SEED") == "LIVE" else SeedGitHubAdapter()


def get_slack_adapter():
    from adapters.slack import SeedSlackAdapter
    return SeedSlackAdapter()


def get_notion_adapter():
    from adapters.notion import SeedNotionAdapter
    return SeedNotionAdapter()
