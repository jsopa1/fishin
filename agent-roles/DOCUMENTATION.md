# Documentation Role

When writing, updating, or organizing documentation:

## Before Starting

1. Read `COPILOT.md` — documentation is part of the product.
2. Understand who the audience is (CEO, new contributors, future self).
3. Check what documentation already exists to avoid duplication.

## Documentation Standards

### Company Memory Files

These are the source of truth and must stay current:

- **VISION.md** — long-term mission and philosophy (rarely changes)
- **PROJECT.md** — current objectives and constraints
- **STRATEGY.md** — high-level approach
- **ROADMAP.md** — planned phases
- **GOALS.md** — specific measurable goals for current phase
- **DECISIONS.md** — architectural and strategic decisions with rationale
- **STATE.md** — current status, blockers, findings, next action
- **AGENTS.md** — company constitution and operating principles
- **COPILOT.md** — operating manual for Copilot agent (you)

**Keep these in sync with reality.** If something changes, update STATE.md immediately.

### README.md

The entry point for the repository. Should answer:

1. What is Fishing Forecast?
2. Current phase and objective.
3. How the company operates (GitHub + Copilot model).
4. How to set up the repo and run code/tests.
5. Where to find company memory and guidelines.
6. What is deliberately NOT being built yet.

Keep it concise—refer to detailed docs rather than making README huge.

### Code Documentation

- **Docstrings** — explain purpose, parameters, return value, and *why* the function exists.
- **Comments** — explain *why* non-obvious logic exists, not what obvious code does.
- **Examples** — for complex functions, include usage examples.

### Issue Descriptions

When creating or updating GitHub Issues:

- **Title** — concise, action-oriented
- **Description** — what needs to be done? Why? What's the success criteria?
- **Acceptance Criteria** — how will we know it's done?
- **Links** — reference related issues, docs, or decisions

### PR Descriptions

- **What changed** — clear summary of modifications
- **Why** — link to the issue or objective; explain the rationale
- **Evidence** — test results, metrics, validation
- **Limitations** — what's not covered, known issues, recommendations

## What NOT to Do

- Don't document hypotheticals or "might do someday" — focus on current reality.
- Don't fabricate findings or claim certainty without evidence.
- Don't leave documentation out of sync with code.
- Don't create dozens of documentation files; consolidate into company-memory files.
- Don't delete historical documentation (decisions, findings) to "clean up."

## Organization

Documentation lives in these locations:

- **Root docs** — VISION.md, PROJECT.md, STRATEGY.md, ROADMAP.md, GOALS.md, STATE.md, DECISIONS.md, AGENTS.md, COPILOT.md, README.md
- **Agent roles** — `agent-roles/` — this file and sibling role guides
- **Code docstrings** — explain Python modules, functions, classes
- **GitHub Issues & PRs** — capture work and decisions in motion
- **Comments in code** — explain *why*, not *what*

## Updating STATE.md

After any meaningful work or decision:

1. Update "current objective" if it changed
2. Add completed work to "completed work" section (if tracking)
3. Add blockers if any emerged
4. Record important findings
5. Note pending decisions
6. Always include "recommended next action"

STATE.md is the source of truth for project status.

---

## Example: Refactor Documentation

**Task:** Migrate from OpenHands agent architecture to GitHub/Copilot model.

**Changes:**
- Create COPILOT.md — new operating manual
- Create agent-roles/ — lightweight role definitions
- Update README.md — describe new model
- Update STATE.md — note refactor completion
- Update DECISIONS.md — document architectural decision

**Review:**
- Do all files accurately describe current reality?
- Are all old references to deprecated infrastructure removed?
- Is the new model clear to someone reading docs for the first time?
- Are all links still valid?
