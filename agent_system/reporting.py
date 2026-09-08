"""Small, dependency-free structured reporting for agent runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

VALID_STATUSES = {"success", "failed", "blocked", "skipped"}


@dataclass
class AgentReport:
    agent: str; task: str; objective: str; started: str; finished: str; status: str; result: str
    files_changed: list[str]; tests: list[str]; evidence: list[str]; limitations: list[str]
    recommendation: str; next_action: str

    def validate(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid report status: {self.status}")
        for field in ("agent", "task", "objective", "started", "finished", "result", "recommendation", "next_action"):
            if not getattr(self, field):
                raise ValueError(f"Report field {field!r} must not be empty")

    def write(self, directory: Path) -> Path:
        self.validate()
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = directory / f"{stamp}-{self.agent}.json"
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        return path
