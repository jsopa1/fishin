# Head Agent Architecture

`CEO → Head Agent → OpenHands Worker → GitHub Repository`

The CEO gives a natural-language instruction. The Head Agent reads the repository’s durable company memory, selects a bounded task, supplies the relevant context and prompt to an OpenHands Research Worker, evaluates the resulting artifact, records a small structured run report, updates `STATE.md` when appropriate, and reports back.

The repository is the source of truth; GitHub is the future durable collaboration surface. This is intentionally the smallest viable autonomous-company architecture: a local workspace, prompts, one worker type, structured reports, and no service infrastructure.
