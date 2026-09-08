# Engineering Role

When implementing features, fixes, or infrastructure:

## Before Starting

1. Read `COPILOT.md` — principles, testing requirements, and PR protocol.
2. Read `DECISIONS.md` — especially decision #003 (minimal dependencies) and #004 (CEO approval).
3. Understand what you're building and why.

## Code Quality Standards

### Structure

- All Python code lives in `agent_system/` or `src/` directories.
- Write focused modules with clear responsibility.
- Use type hints where helpful (not required for prototyping, but preferred).
- Follow Python naming conventions (snake_case for functions/variables, PascalCase for classes).

### Testing

- Unit tests for all new code in `tests/`.
- Tests must pass before opening PR: `python -m pytest`.
- Aim for meaningful test coverage (focus on logic, not line count).
- Tests should verify behavior, not implementation details.
- Test docstrings explain *what* the test verifies.

### Documentation

- Docstrings on functions/classes explain purpose and parameters.
- README.md stays current with setup/run instructions.
- Complex logic gets comments explaining *why*, not *what*.
- No dead code; delete rather than comment-out.

### Dependencies

- Minimize dependencies; always ask why before adding a package.
- Prefer standard library and lightweight packages.
- Never add LLM provider APIs, HTTP clients, or agent frameworks without CEO approval.
- Keep Python version requirement in `pyproject.toml` realistic.

## Code Review Self-Check

Before opening a PR:

- [ ] Code follows standards above
- [ ] Tests pass: `python -m pytest`
- [ ] No dead code or commented-out code
- [ ] No credentials or secrets in code
- [ ] Docstrings explain purpose and params
- [ ] PR description clearly states *what* changed and *why*
- [ ] Related GitHub Issue is linked
- [ ] No unnecessary files (e.g., `.pyc`, `__pycache__`, `.env`)

## Working with Existing Code

- **Preserve working code** — don't refactor unless you have a clear reason.
- **Minimal changes** — fix the specific issue, don't rewrite the whole module.
- **Backward compatibility** — if changing an API, document changes and update call sites.
- **Run existing tests** — ensure you don't break what's already working.

## Python & Dependencies

**Allowed (already in project):**
- pytest (testing)
- setuptools (packaging)

**Only add new packages if:**
- They directly support fishing-forecast work (data acquisition, modeling, etc.)
- CEO approves the addition
- They're lightweight and well-maintained

**Never add:**
- OpenHands SDK/tools (deprecated for this model)
- LLM provider APIs (unless needed for the actual product)
- Heavy frameworks without clear justification

---

## Example: Add New Data Source

1. **Create** `agent_system/data/sources/weather.py` — module to fetch weather data.
2. **Write tests** in `tests/test_weather.py` — mock external API, test data parsing.
3. **Update** `README.md` if setup instructions change.
4. **Open PR** with:
   - What data source was added
   - How to use it
   - Test coverage
   - Any limitations or caveats
5. **Get CEO approval** if adding a new external dependency or paid service.
