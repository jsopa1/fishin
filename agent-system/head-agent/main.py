"""Compatibility launcher; use `python -m agent_system.head_agent.main`."""
from agent_system.head_agent.main import main

if __name__ == "__main__":
    raise SystemExit(main())
