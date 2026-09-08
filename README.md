# Fishing Forecast

Fishing Forecast is an evidence-based fishing intelligence project: help anglers make better decisions about when, where, and how to fish.

**Current phase:** V0 — Prediction Feasibility  
**Current objective:** determine whether public data can support a useful, validated fishing-conditions prediction.

**Prediction validation comes before product development.** This repository contains company memory, core utilities, and validation work—not a consumer application.

---

## How the Company Operates

- **CEO** sets high-level objectives and approves major decisions
- **Copilot** (you, in GitHub) executes disciplined work through GitHub
- **GitHub** is the durable source of truth: repository, issues, PRs, commits, and docs
- **Issues** are the work queue
- **PRs** are employee deliverables (code, research, docs)
- **STATE.md** tracks current status, blockers, findings, and recommended next action

See [COPILOT.md](COPILOT.md) for the complete operating manual.

---

## Repository Structure

**Company Memory:**
- `VISION.md` — long-term mission and philosophy
- `PROJECT.md` — current objectives and constraints
- `STRATEGY.md` — high-level strategy
- `ROADMAP.md` — planned phases (V0, V1, V2, etc.)
- `GOALS.md` — specific measurable goals for current phase
- `STATE.md` — current status, active work, blockers, findings, next action
- `DECISIONS.md` — architectural and strategic decisions with rationale
- `AGENTS.md` — company constitution and operating principles
- `COPILOT.md` — operating manual for Copilot agent

**Specialized Roles:**
- `agent-roles/` — lightweight guidance for research, data science, engineering, QA, and documentation

**Code:**
- `agent_system/` — core utilities (context loading, repository discovery)
- `src/` — (reserved for fishing-forecast-specific code when it exists)
- `tests/` — unit tests for all code

**Infrastructure:**
- `.github/workflows/` — GitHub Actions automation (future)
- `pyproject.toml` — Python project config

---

## Getting Started

### Prerequisites

Python 3.12 or later.

### Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Run Tests

```powershell
python -m pytest
```

### Understanding Company Memory

Before starting work, read these in order:

1. `VISION.md` — understand the mission
2. `COPILOT.md` — understand how Copilot operates
3. `STATE.md` — understand current status and next action
4. `PROJECT.md`, `STRATEGY.md`, `GOALS.md` — understand current objectives
5. `DECISIONS.md` — understand why current decisions were made
6. Relevant role guide in `agent-roles/` — guidance for specialized work

---

## What's Deliberately NOT Built Yet

- No fishing application or UI
- No production infrastructure
- No real-time prediction service
- No user database or accounts
- No paid APIs or services
- No complex data pipelines
- No custom agent orchestration framework

All of these come *after* V0 proves the prediction is valuable.

---

## Principles

1. **Evidence over speculation** — never fabricate data or claim accuracy without proof
2. **Validate before productizing** — prove the prediction is feasible
3. **Prefer free/open data** — no paid services without CEO approval
4. **Prefer simple approaches** — use the simplest model that works
5. **Reproducibility** — all results must be reproducible with public data
6. **Tests are required** — code changes must include tests
7. **Small focused changes** — prefer targeted work over giant rewrites

See `COPILOT.md` for complete operating principles.

---

## For New Contributors

1. Read `COPILOT.md` — especially if you're implementing work
2. Read `STATE.md` — understand what's currently happening
3. Pick a GitHub Issue or discuss with CEO
4. Follow the work protocol in `COPILOT.md`
5. Open a focused PR with tests and documentation

---

## Making a Decision or Escalating

Copilot (you) has autonomy on routine technical work.

For major decisions, see the "CEO Approval Required" section in [COPILOT.md](COPILOT.md).

---

## Recommended Reading

- Start here: [COPILOT.md](COPILOT.md) — operating manual
- Understand the company: [VISION.md](VISION.md), [PROJECT.md](PROJECT.md), [STRATEGY.md](STRATEGY.md)
- Understand current status: [STATE.md](STATE.md)
- Understand current phase: [GOALS.md](GOALS.md)
- Understand decisions: [DECISIONS.md](DECISIONS.md)
- For specialized work: `agent-roles/RESEARCH.md`, `agent-roles/DATA_SCIENCE.md`, `agent-roles/ENGINEERING.md`, `agent-roles/QA.md`, `agent-roles/DOCUMENTATION.md`
