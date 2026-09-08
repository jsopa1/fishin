# Fishing Forecast

Fishing Forecast is an evidence-based fishing intelligence project: help anglers make better decisions about when, where, and how to fish.

**Current phase:** V0 — Prediction Feasibility  
**Current objective:** determine whether public data can support a useful, validated fishing-conditions prediction.

Prediction validation comes before product development. This repository contains company memory, research, and a minimal local Head Agent → Research Agent workflow; it does not contain a fishing application.

## Structure

- Root documents: vision, strategy, roadmap, decisions, and operating state
- `agent-system/`: prompts and workflows
- `agent_system/`: executable Python implementation
- `docs/`: research, architecture, operations, and experiments
- `tests/`: offline unit tests

## Local setup

The current OpenHands SDK requires Python 3.12 or later. With Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Copy `.env.example` to `.env` (or set the variables in your shell) before a live run. Never commit `.env`.
