# Agent Execution

Agents execute in the local repository workspace via the OpenHands SDK. The Head Agent loads company documents and durable prompts; the worker receives only its focused task plus that context. Completion is recorded as a structured JSON run report in `docs/operations/runs/`.

The local workflow uses environment variables (`LLM_MODEL`, `LLM_API_KEY`, and optional `LLM_BASE_URL`) rather than source-controlled credentials. The repository holds prompts, reports, decisions, state, and artifacts, making execution inspectable and repeatable.
