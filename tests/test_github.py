from agent_system.github import github_cli_status


def test_github_cli_detection_returns_actionable_message() -> None:
    installed, detail = github_cli_status()
    assert isinstance(installed, bool)
    assert detail
