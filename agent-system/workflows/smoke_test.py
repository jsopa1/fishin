"""Live, credential-gated proof that an OpenHands worker can make one safe edit."""
from __future__ import annotations

import sys
from pathlib import Path

from agent_system.context import find_repository_root, load_company_context
from agent_system.research_agent.main import MissingCredentialsError, run_research_task

TASK = "Read PROJECT.md and STATE.md. Create docs/operations/openhands-smoke-test.md. Explain the current project objective, current phase, and next recommended action. Do not modify any other files."


def run(start: Path | None = None) -> bool:
    root = find_repository_root(start)
    target = root / "docs" / "operations" / "openhands-smoke-test.md"
    try:
        run_research_task(root, TASK, load_company_context(root))
    except MissingCredentialsError as error:
        print(f"SKIPPED: {error}")
        return False
    if not target.is_file() or not target.read_text(encoding="utf-8").strip():
        raise RuntimeError("Smoke test failed: expected non-empty docs/operations/openhands-smoke-test.md")
    print("SUCCESS: OpenHands safely created the smoke-test artifact.")
    return True


if __name__ == "__main__":
    sys.exit(0 if run() else 2)
