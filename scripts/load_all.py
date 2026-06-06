# Lane: P2 backend
"""
load_all.py — Covenant seed loader
===================================
Loads all seed data into Slack, Notion, and Linear from the local JSON files.
Run this ONCE tonight before the hackathon.

Usage:
    pip install slack-sdk notion-client requests python-dotenv
    python scripts/load_all.py

Required environment variables (create a .env file at the project root):
    SLACK_BOT_TOKEN=xoxb-...
    SLACK_CHANNEL_ID=C0XXXXXXXXX      # ID of #eng-decisions channel
    NOTION_TOKEN=secret_...
    NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    LINEAR_API_KEY=lin_api_...

What it does:
    1. Slack   — posts all 20 messages from slack_export.json into #eng-decisions
                 with correct threading (contradictions posted as replies)
    2. Notion  — creates all 10 decisions as rows in the Decision Ledger database
    3. Linear  — creates 1 project, 5 issues (one per decision area), and adds
                 decisions as comments on the relevant issue

Run with --dry-run to preview without making any API calls.
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── Dependency check ────────────────────────────────────────────
def check_deps():
    missing = []
    for pkg in ["slack_sdk", "notion_client", "requests", "dotenv"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-").replace("dotenv", "python-dotenv"))
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}")
        sys.exit(1)

check_deps()

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from notion_client import Client as NotionClient
import requests

load_dotenv()

# ── Config ───────────────────────────────────────────────────────
SEED_DIR      = Path(__file__).resolve().parent.parent / "data"
DECISIONS_F   = SEED_DIR / "decisions.json"
SLACK_F       = SEED_DIR / "slack_export.json"

SLACK_TOKEN   = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID", "")
NOTION_TOKEN  = os.getenv("NOTION_TOKEN", "")
NOTION_DB_ID  = os.getenv("NOTION_DATABASE_ID", "")
LINEAR_KEY    = os.getenv("LINEAR_API_KEY", "")

# ── Argument parsing ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Covenant seed loader")
parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
parser.add_argument("--slack-only",  action="store_true")
parser.add_argument("--notion-only", action="store_true")
parser.add_argument("--linear-only", action="store_true")
args = parser.parse_args()

DRY = args.dry_run
DO_SLACK  = args.slack_only  or (not args.notion_only and not args.linear_only)
DO_NOTION = args.notion_only or (not args.slack_only  and not args.linear_only)
DO_LINEAR = args.linear_only or (not args.slack_only  and not args.notion_only)

# ── Helpers ──────────────────────────────────────────────────────
def load_json(path):
    with open(path) as f:
        return json.load(f)

def fmt(text, color=None):
    codes = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m",
             "blue": "\033[94m", "bold": "\033[1m", "reset": "\033[0m"}
    if color and color in codes:
        return f"{codes[color]}{text}{codes['reset']}"
    return text

def log(msg, color=None):
    print(fmt(msg, color))

def sep(title):
    print(f"\n{fmt('─' * 60, 'blue')}")
    print(fmt(f"  {title}", "bold"))
    print(fmt('─' * 60, 'blue'))

# ── Validate env vars ────────────────────────────────────────────
def validate():
    errors = []
    if DO_SLACK:
        if not SLACK_TOKEN:  errors.append("SLACK_BOT_TOKEN is missing")
        if not SLACK_CHANNEL: errors.append("SLACK_CHANNEL_ID is missing")
    if DO_NOTION:
        if not NOTION_TOKEN:  errors.append("NOTION_TOKEN is missing")
        if not NOTION_DB_ID:  errors.append("NOTION_DATABASE_ID is missing")
    if DO_LINEAR:
        if not LINEAR_KEY:    errors.append("LINEAR_API_KEY is missing")
    if errors:
        log("\nMissing environment variables:", "red")
        for e in errors:
            log(f"  ✗ {e}", "red")
        log("\nCreate a .env file next to load_all.py with these values.", "yellow")
        sys.exit(1)

# ════════════════════════════════════════════════════════════════
#  SLACK LOADER
# ════════════════════════════════════════════════════════════════
def load_slack():
    sep("Slack — Loading messages into #eng-decisions")

    messages = load_json(SLACK_F)
    client   = WebClient(token=SLACK_TOKEN)

    # Group: base messages first, then replies
    base_messages  = [m for m in messages if not m.get("_is_contradiction")]
    contradictions = [m for m in messages if m.get("_is_contradiction")]

    # Map decision_id → slack thread_ts (so contradictions thread under the right message)
    thread_map = {}   # decision_id → ts of the decision message

    log(f"\nPosting {len(base_messages)} base messages...", "yellow")

    for i, msg in enumerate(base_messages):
        classification = msg.get("_classification", "NOISE")
        decision_id    = msg.get("_decision_id")

        # Format the message text with a classification label
        label_emoji = {"DECISION": "🟢", "DISCUSSION": "🔵", "NOISE": "⚪"}.get(classification, "⚪")
        text = f"{label_emoji} {msg['text']}"

        if DRY:
            log(f"  [DRY] Would post: {text[:80]}...", "yellow")
            if decision_id:
                thread_map[decision_id] = f"fake_ts_{i}"
            continue

        try:
            resp = client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=text,
                username=msg.get("user", "team"),
            )
            ts = resp["ts"]
            log(f"  ✓ [{classification}] {msg['text'][:60]}...")
            if decision_id:
                thread_map[decision_id] = ts
            time.sleep(0.5)  # avoid rate limits
        except SlackApiError as e:
            log(f"  ✗ Failed to post: {e.response['error']}", "red")

    log(f"\nPosting {len(contradictions)} contradictions as replies...", "yellow")

    for msg in contradictions:
        contradicts_id = msg.get("_contradicts_decision_id")
        thread_ts = thread_map.get(contradicts_id)

        # Format with contradiction warning
        text = f"🔴 *Proposed change:* {msg['text']}"

        if DRY:
            log(f"  [DRY] Would reply to thread {contradicts_id}: {text[:80]}...", "yellow")
            continue

        try:
            kwargs = {
                "channel": SLACK_CHANNEL,
                "text": text,
                "username": msg.get("user", "team"),
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts  # reply in thread

            resp = client.chat_postMessage(**kwargs)
            log(f"  ✓ [CONTRADICTION] {msg['text'][:60]}...")
            time.sleep(0.5)
        except SlackApiError as e:
            log(f"  ✗ Failed to post contradiction: {e.response['error']}", "red")

    if not DRY:
        log(f"\n✓ Slack done — {len(messages)} messages loaded into channel", "green")
    else:
        log(f"\n[DRY RUN] Would have posted {len(messages)} messages to Slack", "yellow")


# ════════════════════════════════════════════════════════════════
#  NOTION LOADER
# ════════════════════════════════════════════════════════════════
def load_notion():
    sep("Notion — Loading 10 decisions into Decision Ledger database")

    decisions = load_json(DECISIONS_F)
    notion    = NotionClient(auth=NOTION_TOKEN)

    log(f"\nCreating {len(decisions)} decision rows...", "yellow")

    for decision in decisions:
        # Format participants as a comma-separated string
        participants_str = ", ".join(decision.get("participants", []))
        alternatives_str = " | ".join(decision.get("alternatives_rejected", []))

        # Parse the date
        created_at = decision.get("created_at", "2026-01-01T00:00:00Z")

        if DRY:
            log(f"  [DRY] Would create row: {decision['summary'][:60]}...", "yellow")
            continue

        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties={
                    # Title column
                    "Decision": {
                        "title": [{"text": {"content": decision["summary"]}}]
                    },
                    # Rich text columns
                    "Rationale": {
                        "rich_text": [{"text": {"content": decision["rationale"]}}]
                    },
                    "Participants": {
                        "rich_text": [{"text": {"content": participants_str}}]
                    },
                    "Alternatives Rejected": {
                        "rich_text": [{"text": {"content": alternatives_str}}]
                    },
                    "Source": {
                        "rich_text": [{"text": {"content": decision.get("source", "slack")}}]
                    },
                    "Decision ID": {
                        "rich_text": [{"text": {"content": decision["id"]}}]
                    },
                    # Date column
                    "Date": {
                        "date": {"start": created_at.replace("Z", "+00:00")}
                    },
                    # Status (Notion built-in status field)
                    "Status": {
                        "status": {"name": "In progress"}
                    },
                }
            )
            log(f"  ✓ Created: {decision['summary'][:60]}...")
            time.sleep(0.3)  # notion rate limits
        except Exception as e:
            log(f"  ✗ Failed to create row: {str(e)[:100]}", "red")

    if not DRY:
        log(f"\n✓ Notion done — {len(decisions)} decisions loaded into database", "green")
    else:
        log(f"\n[DRY RUN] Would have created {len(decisions)} Notion rows", "yellow")


# ════════════════════════════════════════════════════════════════
#  LINEAR LOADER
# ════════════════════════════════════════════════════════════════
LINEAR_API = "https://api.linear.app/graphql"

def linear_query(query, variables=None):
    resp = requests.post(
        LINEAR_API,
        headers={"Authorization": LINEAR_KEY, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}}
    )
    data = resp.json()
    if "errors" in data:
        raise Exception(f"Linear API error: {data['errors']}")
    return data["data"]

def get_linear_team_id():
    data = linear_query("{ teams { nodes { id name } } }")
    teams = data["teams"]["nodes"]
    if not teams:
        raise Exception("No Linear teams found. Create a team first.")
    return teams[0]["id"]

def create_linear_project(team_id, name, description):
    data = linear_query("""
        mutation CreateProject($teamId: String!, $name: String!, $description: String) {
            projectCreate(input: {
                teamIds: [$teamId]
                name: $name
                description: $description
            }) {
                success
                project { id name }
            }
        }
    """, {"teamId": team_id, "name": name, "description": description})
    return data["projectCreate"]["project"]["id"]

def create_linear_issue(team_id, project_id, title, description):
    data = linear_query("""
        mutation CreateIssue($teamId: String!, $projectId: String!, $title: String!, $description: String) {
            issueCreate(input: {
                teamId: $teamId
                projectId: $projectId
                title: $title
                description: $description
            }) {
                success
                issue { id title }
            }
        }
    """, {"teamId": team_id, "projectId": project_id,
          "title": title, "description": description})
    return data["issueCreate"]["issue"]["id"]

def create_linear_comment(issue_id, body):
    data = linear_query("""
        mutation CreateComment($issueId: String!, $body: String!) {
            commentCreate(input: { issueId: $issueId, body: $body }) {
                success
                comment { id }
            }
        }
    """, {"issueId": issue_id, "body": body})
    return data["commentCreate"]["comment"]["id"]

# Issue groups: each issue covers 2 decisions
ISSUE_GROUPS = [
    {
        "title": "Authentication & Security",
        "description": "Tracks decisions around auth strategy, token management, and security policies.",
        "decision_ids": [
            "d1a2b3c4-0001-4000-a000-000000000001",  # JWT
            "d1a2b3c4-0004-4000-a000-000000000004",  # no PII in orders
        ]
    },
    {
        "title": "Data Layer & Storage",
        "description": "Tracks decisions around database choice, caching, and data architecture.",
        "decision_ids": [
            "d1a2b3c4-0002-4000-a000-000000000002",  # Postgres
            "d1a2b3c4-0009-4000-a000-000000000009",  # Redis scope
        ]
    },
    {
        "title": "Product & UX",
        "description": "Tracks product design decisions including checkout flow and user experience.",
        "decision_ids": [
            "d1a2b3c4-0003-4000-a000-000000000003",  # 3-step checkout
        ]
    },
    {
        "title": "Infrastructure & Deployment",
        "description": "Tracks infrastructure, deployment strategy, and operational decisions.",
        "decision_ids": [
            "d1a2b3c4-0005-4000-a000-000000000005",  # Vercel + Railway
            "d1a2b3c4-0010-4000-a000-000000000010",  # monorepo
        ]
    },
    {
        "title": "API Design & Reliability",
        "description": "Tracks API design standards, retry logic, and rate limiting decisions.",
        "decision_ids": [
            "d1a2b3c4-0006-4000-a000-000000000006",  # exponential backoff
            "d1a2b3c4-0007-4000-a000-000000000007",  # URL versioning
            "d1a2b3c4-0008-4000-a000-000000000008",  # rate limiting
        ]
    },
]

def format_comment_for_decision(decision):
    participants = ", ".join(decision.get("participants", []))
    alternatives = "\n".join([f"  - {a}" for a in decision.get("alternatives_rejected", [])])
    date_str = decision.get("created_at", "")[:10]
    return f"""## Decision recorded — {date_str}

**{decision['summary']}**

**Participants:** {participants}

**Rationale:**
{decision['rationale']}

**Alternatives rejected:**
{alternatives}

**Source:** {decision.get('source', 'slack')} | **ID:** `{decision['id']}`

---
*This comment was seeded by the Covenant load_all.py script.*"""


def load_linear():
    sep("Linear — Creating project, issues, and decision comments")

    decisions    = load_json(DECISIONS_F)
    decisions_by_id = {d["id"]: d for d in decisions}

    if DRY:
        log(f"\n[DRY] Would create 1 project, {len(ISSUE_GROUPS)} issues, "
            f"and {len(decisions)} comments", "yellow")
        for group in ISSUE_GROUPS:
            log(f"  [DRY] Issue: {group['title']}", "yellow")
            for did in group["decision_ids"]:
                d = decisions_by_id.get(did)
                if d:
                    log(f"    [DRY] Comment: {d['summary'][:60]}...", "yellow")
        return

    try:
        log("\nFetching Linear team...", "yellow")
        team_id = get_linear_team_id()
        log(f"  ✓ Team ID: {team_id}")

        log("\nCreating project: Covenant Demo App...", "yellow")
        project_id = create_linear_project(
            team_id,
            "Covenant Demo App",
            "Demo application used to showcase the Covenant autonomous decision enforcement agent. "
            "Issues track decision areas; comments on each issue are the actual team decisions."
        )
        log(f"  ✓ Project created: {project_id}")
        time.sleep(0.5)

        for group in ISSUE_GROUPS:
            log(f"\n  Creating issue: {group['title']}...", "yellow")
            issue_id = create_linear_issue(
                team_id, project_id,
                group["title"],
                group["description"]
            )
            log(f"    ✓ Issue created: {issue_id}")
            time.sleep(0.5)

            for decision_id in group["decision_ids"]:
                decision = decisions_by_id.get(decision_id)
                if not decision:
                    log(f"    ✗ Decision not found: {decision_id}", "red")
                    continue
                comment_body = format_comment_for_decision(decision)
                create_linear_comment(issue_id, comment_body)
                log(f"    ✓ Comment: {decision['summary'][:55]}...")
                time.sleep(0.3)

        log(f"\n✓ Linear done — 1 project, {len(ISSUE_GROUPS)} issues, "
            f"{len(decisions)} decision comments loaded", "green")

    except Exception as e:
        log(f"\n✗ Linear error: {e}", "red")
        log("Make sure LINEAR_API_KEY is valid and your workspace has at least 1 team.", "yellow")


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
def main():
    log(fmt("\n⚡ Covenant Seed Loader", "bold"))
    log("=" * 60)

    if DRY:
        log(fmt("  DRY RUN — no API calls will be made", "yellow"))

    validate()

    log(f"\nSeed files:")
    log(f"  decisions.json   — {len(load_json(DECISIONS_F))} decisions")
    log(f"  slack_export.json — {len(load_json(SLACK_F))} messages")

    if DO_SLACK:
        load_slack()
    if DO_NOTION:
        load_notion()
    if DO_LINEAR:
        load_linear()

    log(fmt("\n✓ All done. Your platforms are seeded and ready.", "green"))
    log(fmt("\nNext steps:", "bold"))
    if DO_SLACK:
        log("  Slack:  Go to #eng-decisions in your workspace. All messages should be there.")
        log("          Tomorrow morning: enable Event Subscriptions pointing at {ngrok}/webhooks/slack")
    if DO_NOTION:
        log("  Notion: Open your Decision Ledger database. 10 rows should be visible.")
        log("          Add NOTION_TOKEN + NOTION_DATABASE_ID to .env. No webhook needed — uses polling.")
    if DO_LINEAR:
        log("  Linear: Open the Covenant Demo App project. 5 issues with decision comments.")
        log("          Tomorrow morning: update webhook URL to {ngrok}/webhooks/linear")

if __name__ == "__main__":
    main()
