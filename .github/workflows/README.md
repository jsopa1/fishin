# Future GitHub Automation

This directory intentionally has no active Actions workflow yet. After the local workflow is proven:

* Issue created → Head Agent evaluates → agent dispatched
* PR opened → tests and QA
* Agent completes → Head Agent evaluates → continue, retry, or escalate
* Scheduled execution → Head Agent reviews `STATE.md` for stale or blocked work

GitHub automation is deferred until the local autonomous workflow works.
