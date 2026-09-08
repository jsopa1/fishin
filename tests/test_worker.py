import pytest

from agent_system.research_agent.main import MissingCredentialsError, require_llm_credentials


def test_missing_llm_credentials_is_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(MissingCredentialsError, match="LLM_MODEL"):
        require_llm_credentials()
