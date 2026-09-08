"""Repository discovery and durable company-context loading."""
from __future__ import annotations

from pathlib import Path

REQUIRED_CONTEXT_FILES = (
    "VISION.md", "PROJECT.md", "STRATEGY.md", "ROADMAP.md", "GOALS.md",
    "STATE.md", "DECISIONS.md", "AGENTS.md",
)


def find_repository_root(start: Path | None = None) -> Path:
    """Find a directory containing the required durable project documents."""
    candidate = (start or Path.cwd()).resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / "PROJECT.md").is_file() and (directory / "AGENTS.md").is_file():
            return directory
    raise FileNotFoundError("Could not find Fishing Forecast repository root (PROJECT.md and AGENTS.md required).")


def load_company_context(root: Path) -> dict[str, str]:
    missing = [name for name in REQUIRED_CONTEXT_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing required company context files: " + ", ".join(missing))
    return {name: (root / name).read_text(encoding="utf-8") for name in REQUIRED_CONTEXT_FILES}
