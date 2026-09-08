from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_system.reporting import AgentReport


def report(status: str = "success") -> AgentReport:
    now = datetime.now(timezone.utc).isoformat()
    return AgentReport("worker", "task", "objective", now, now, status, "result", [], [], [], [], "recommend", "next")


def test_report_validates_and_writes(tmp_path: Path) -> None:
    path = report().write(tmp_path)
    assert path.is_file()
    assert '"agent": "worker"' in path.read_text(encoding="utf-8")


def test_report_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="Invalid report status"):
        report("unknown").validate()
