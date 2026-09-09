# Decisions

## 001 — Validate before productizing

We will validate the fishing prediction before building a polished consumer application.

## 002 — No assumption that ML is necessary

We will use the simplest model that performs well. Potential approaches include rules, statistical models, logistic regression, random forest, gradient boosting, and other ML. An LLM is not automatically the prediction model.

## 003 — $0 initial budget

Prefer free APIs, open datasets, open-source software, and free infrastructure.

## 004 — Human approval for major decisions

Agents may research, implement, test, and document. The CEO approves major product, architecture, financial, and strategic decisions.

## 005 — Evidence over appearances

The system must never represent an arbitrary score as scientifically validated.

## 006 — GitHub/Copilot as operating model instead of autonomous agents

The company operates via GitHub as the durable source of truth, with CEO setting objectives and Copilot executing disciplined work through GitHub Issues and PRs.

**Rationale:**
- GitHub is widely understood and provides version control, audit trail, and durable memory
- Human-in-the-loop model (CEO → Issues → Copilot → PRs → Approval → Merge) reduces risk of autonomous mistakes
- PR review and CEO approval gates ensure major decisions are visible and approved
- Moving away from OpenHands SDK simplifies dependencies and reduces framework lock-in
- Copilot executes focused, evidence-based work following lightweight role definitions (RESEARCH.md, DATA_SCIENCE.md, ENGINEERING.md, QA.md, DOCUMENTATION.md)
- No separate autonomous agent orchestration framework—Copilot is the single execution engine

## 007 — V0 pilot geography: southeast Wisconsin / Lake Michigan

The V0 prediction-feasibility pilot is scoped to southeast Wisconsin, starting with:

- **Lake Michigan** (Milwaukee/Racine/Kenosha nearshore waters)
- **Lake Winnebago** (Winnebago County)
- **Pewaukee Lake** (Waukesha County)
- **Delavan Lake** (Walworth County)
- **Geneva Lake** (Walworth County)

Counties in scope: Milwaukee, Waukesha, Racine, Kenosha, Walworth, Winnebago.

**Rationale:**
- Concentrates limited $0-budget data-gathering effort on a small, well-instrumented region rather than spreading thin nationally
- Southeast Wisconsin has strong public data coverage (USGS gauges, NOAA/Great Lakes buoy and weather data, WDNR fishing/stocking records) to test the feasibility hypothesis
- Lake Michigan and inland lakes together give both a large-lake and small-lake test case within one pilot
- Out of scope for V0: any other state, region, or water body not listed above; expansion is a future-phase decision requiring CEO approval
