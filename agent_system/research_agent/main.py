"""Research worker with a deliberately small local OpenHands integration."""
from __future__ import annotations

import os
from pathlib import Path


class MissingCredentialsError(RuntimeError):
    """Raised before any LLM call when local configuration is incomplete."""


def require_llm_credentials() -> dict[str, str | None]:
    missing = [name for name in ("LLM_MODEL", "LLM_API_KEY") if not os.getenv(name)]
    if missing:
        raise MissingCredentialsError(
            "Missing required LLM configuration: " + ", ".join(missing) +
            ". Copy .env.example to .env, set environment variables, then retry."
        )
    return {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "base_url": os.getenv("LLM_BASE_URL")}


def run_research_task(root: Path, task: str, context: dict[str, str]) -> str:
    """Run a local OpenHands conversation and return a concise completion marker.

    Imports remain here so offline tests and status commands never require the SDK.
    """
    config = require_llm_credentials()
    try:
        from openhands.sdk import Agent, Conversation, LLM, Tool
        from openhands.tools.file_editor import FileEditorTool
        from openhands.tools.task_tracker import TaskTrackerTool
        from openhands.tools.terminal import TerminalTool
    except ImportError as error:
        raise RuntimeError("OpenHands packages are not installed. Activate .venv and run `pip install -e .[dev]`.") from error

    llm = LLM(model=config["model"], api_key=config["api_key"], base_url=config["base_url"])
    agent = Agent(llm=llm, tools=[
        Tool(name=TerminalTool.name), Tool(name=FileEditorTool.name), Tool(name=TaskTrackerTool.name),
    ])
    prompt = (root / "agent-system" / "prompts" / "research-agent.md").read_text(encoding="utf-8")
    supplied_context = "\n\n".join(f"## {name}\n{text}" for name, text in context.items())
    conversation = Conversation(agent=agent, workspace=str(root))
    conversation.send_message(f"{prompt}\n\n# Company context\n{supplied_context}\n\n# Assigned task\n{task}")
    conversation.run()
    return "OpenHands worker completed its local conversation."
