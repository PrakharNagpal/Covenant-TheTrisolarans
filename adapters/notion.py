# P2 lane — Notion adapter (reads from seed decisions file)
import json
import os


class SeedNotionAdapter:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "decisions.json")
        with open(path) as f:
            self._decisions = json.load(f)

    def get_decisions(self) -> list[dict]:
        return self._decisions
