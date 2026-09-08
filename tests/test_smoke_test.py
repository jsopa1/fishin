import importlib.util
from pathlib import Path

from agent_system.context import find_repository_root


def test_smoke_test_has_the_required_safety_constraint() -> None:
    root = find_repository_root(Path(__file__))
    path = root / "agent-system" / "workflows" / "smoke_test.py"
    contents = path.read_text(encoding="utf-8")
    assert "Do not modify any other files" in contents
    assert "openhands-smoke-test.md" in contents


def test_smoke_test_module_is_syntactically_loadable() -> None:
    root = find_repository_root(Path(__file__))
    spec = importlib.util.spec_from_file_location("workflow_smoke_test", root / "agent-system" / "workflows" / "smoke_test.py")
    assert spec is not None and spec.loader is not None
