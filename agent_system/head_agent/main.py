"""Minimal Head Agent orchestration, scoped to the first V0 workflow."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from agent_system.context import find_repository_root, load_company_context
from agent_system.reporting import AgentReport
from agent_system.research_agent.main import MissingCredentialsError, run_research_task

V0_TRIGGER = "publicly available data"
V0_TASK = """Research public fishing/catch/effort observation datasets, historical weather/environmental datasets, and whether they can be joined spatially and temporally. Create docs/research/fishing-data-availability.md. Answer the questions in the company objective, cite sources, document limitations, and do not build application or model code."""


def select_task(instruction: str) -> str:
    if "start v0" in instruction.lower() or V0_TRIGGER in instruction.lower():
        return V0_TASK
    return "Review the CEO instruction against current company context. Create only a focused, evidence-based research artifact if appropriate; otherwise explain the blocker in the run report. CEO instruction: " + instruction


def update_state_after_success(root: Path, artifact: Path) -> None:
    state = root / "STATE.md"
    content = state.read_text(encoding="utf-8")
    content = content.replace("## Active Work\n\nNone yet.", "## Active Work\n\nInitial V0 data-availability research completed; Head Agent evaluation is pending CEO review.")
    content = content.replace("## Recent Findings\n\nNone yet.", f"## Recent Findings\n\nResearch artifact created: `{artifact.relative_to(root).as_posix()}`. Findings require CEO review before claims are adopted.")
    content = content.replace("Research public fishing outcome datasets and determine whether sufficient ground-truth data exists.", "Review the V0 data-availability research, choose a target geography/dataset, and validate acquisition reproducibly.")
    state.write_text(content, encoding="utf-8")


def execute(instruction: str, start: Path | None = None) -> AgentReport:
    root = find_repository_root(start)
    context = load_company_context(root)
    task = select_task(instruction)
    started = datetime.now(timezone.utc).isoformat()
    artifact = root / "docs" / "research" / "fishing-data-availability.md"
    try:
        result = run_research_task(root, task, context)
        if "fishing-data-availability" in task and (not artifact.is_file() or not artifact.read_text(encoding="utf-8").strip()):
            raise RuntimeError("Worker completed without the expected non-empty research artifact.")
        if artifact.is_file():
            update_state_after_success(root, artifact)
        status, limitations = "success", []
        files = [artifact.relative_to(root).as_posix()] if artifact.is_file() else []
    except MissingCredentialsError as error:
        status, result, limitations, files = "blocked", str(error), ["Live worker requires an LLM model and API key."], []
    except Exception as error:  # keep an operational report even for SDK/provider failures
        status, result, limitations, files = "failed", str(error), ["Inspect the error and worker run configuration before retrying."], []
    report = AgentReport("head-agent", instruction, task, started, datetime.now(timezone.utc).isoformat(), status, result, files, [], [], limitations, "Review the recorded result and proceed only with evidence.", "Run the V0 data-availability workflow after LLM credentials are configured.")
    report.write(root / "docs" / "operations" / "runs")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Fishing Forecast Head Agent")
    parser.add_argument("instruction", help="Natural-language CEO instruction")
    args = parser.parse_args()
    report = execute(args.instruction)
    print(f"Status: {report.status}\nResult: {report.result}\nNext: {report.next_action}")
    return 0 if report.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
