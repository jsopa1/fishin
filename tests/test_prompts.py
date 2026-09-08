from pathlib import Path

from agent_system.context import find_repository_root


def test_agent_prompts_exist_and_are_nonempty() -> None:
    root = find_repository_root(Path(__file__))
    for name in ("head-agent.md", "research-agent.md"):
        text = (root / "agent-system" / "prompts" / name).read_text(encoding="utf-8")
        assert text.strip()
