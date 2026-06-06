# P2 lane — Slack adapter (reads from seed export)
import json
import os


class SeedSlackAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "slack_export.json")
        with open(path) as f:
            self._messages = json.load(f)

    def get_messages(self) -> list[dict]:
        return self._messages
