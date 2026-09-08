from pathlib import Path

import pytest

from agent_system.context import REQUIRED_CONTEXT_FILES, find_repository_root, load_company_context


def test_find_repository_root_from_nested_directory(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "PROJECT.md").write_text("project")
    (root / "AGENTS.md").write_text("agents")
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    assert find_repository_root(nested) == root


def test_load_company_context_rejects_missing_documents(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing required"):
        load_company_context(tmp_path)


def test_load_company_context_reads_all_required_documents(tmp_path: Path) -> None:
    for name in REQUIRED_CONTEXT_FILES:
        (tmp_path / name).write_text(name, encoding="utf-8")
    assert load_company_context(tmp_path)["VISION.md"] == "VISION.md"
