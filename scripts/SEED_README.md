<!-- Lane: P2 backend -->

# Covenant Seed Loader — Quick Start

Run this **once tonight** to populate Slack, Notion, and Linear with all seed data.

---

## 1. Install dependencies

```bash
pip install slack-sdk notion-client requests python-dotenv
```

---

## 2. Create accounts and get credentials

### Slack
1. Create a new Slack workspace at slack.com (free)
2. Create a channel called `#eng-decisions`
3. Go to https://api.slack.com/apps → **Create New App** → From scratch
4. Name: `Covenant` · Pick your workspace
5. **OAuth & Permissions** → Add Bot Token Scopes:
   - `channels:history`
   - `chat:write`
   - `chat:write.customize`
   - `users:read`
   - `app_mentions:read`
6. Click **Install to Workspace** → copy the **Bot User OAuth Token** (`xoxb-...`)
7. In Slack, go to `#eng-decisions` → right-click → **View channel details** → copy the channel ID (`C0...` at the bottom)
8. Invite the bot: type `/invite @Covenant` in the channel

### Notion
1. Go to https://www.notion.so/my-integrations → **New Integration**
2. Name: `Covenant` · Pick your workspace · Click Submit
3. Copy the **Internal Integration Secret** (`secret_...`)
4. In Notion, create a new **Database** (full-page) called `Decision Ledger`
5. Add these columns (exact names):
   - `Decision` (Title — already exists)
   - `Rationale` (Text)
   - `Participants` (Text)
   - `Alternatives Rejected` (Text)
   - `Source` (Text)
   - `Decision ID` (Text)
   - `Date` (Date)
   - `Status` (Select — add option: "Active")
6. Open the database → click `...` top right → **Add connections** → select `Covenant`
7. Copy the Database ID from the URL: `notion.so/{workspace}/{DATABASE_ID}?v=...` (32-char string)

### Linear
1. Go to your Linear workspace → **Settings** → **API** → **Create key**
2. Name it `Covenant` → copy the key (`lin_api_...`)
3. Go to **Settings** → **Webhooks** → **New Webhook**
4. URL: put `https://placeholder.ngrok.app/webhooks/linear` for now (update tomorrow morning)
5. Enable events: **Comment**, **Issue**, **Project**
6. Copy the **Webhook signing secret**

---

## 3. Fill in .env

```bash
# Create .env and fill in the required values
```

---

## 4. Run the loader

```bash
# Dry run first — preview without making any calls
python scripts/load_all.py --dry-run

# Load everything
python scripts/load_all.py

# Or load one platform at a time
python scripts/load_all.py --slack-only
python scripts/load_all.py --notion-only
python scripts/load_all.py --linear-only
```

---

## 5. Verify

- **Slack**: open `#eng-decisions` — you should see 20 messages, with contradiction messages threaded under the relevant decision
- **Notion**: open Decision Ledger — you should see 10 rows with all fields filled
- **Linear**: open the Covenant Demo App project — you should see 5 issues with decision comments

---

## 6. Tomorrow morning (before 10am)

1. Start ngrok: `ngrok http 8000 --domain your-reserved-domain.ngrok.app`
2. **Slack**: Go to your app → Event Subscriptions → toggle ON → set URL to `https://your-domain.ngrok.app/webhooks/slack` → subscribe to `message.channels` and `app_mention`
3. **Notion**: No action needed — uses polling, not webhooks
4. **Linear**: Go to Settings → Webhooks → edit URL to `https://your-domain.ngrok.app/webhooks/linear`

---

## Troubleshooting

| Error | Fix |
|---|---|
| `not_in_channel` (Slack) | Run `/invite @Covenant` in the channel |
| `missing_scope` (Slack) | Add the missing scope in OAuth & Permissions and reinstall |
| `object_not_found` (Notion) | Make sure the database is shared with the integration |
| `Unauthorized` (Linear) | Double-check the API key starts with `lin_api_` |
| Slack messages posting but no threading | Contradictions need the source decision to be posted first — order matters |
