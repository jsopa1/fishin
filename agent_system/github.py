"""Narrow GitHub CLI abstraction; no authentication bypasses."""
from __future__ import annotations

import shutil


def github_cli_status() -> tuple[bool, str]:
    executable = shutil.which("gh")
    if executable:
        return True, executable
    return False, "GitHub CLI ('gh') is not installed. Install it and run `gh auth login` before GitHub operations."
