# fishin — V0 Pilot: Southeastern Wisconsin & Lake Michigan

## Mission
Run the full V0 pipeline autonomously, start to finish, without stopping
for confirmation between steps. Only stop at the final gate below.

## Scope
- Southeastern Wisconsin inland lakes
- Wisconsin waters of Lake Michigan
Outcome data: WDNR creel survey reports (PDFs). Lake Michigan predictors
can use NOAA CO-OPS/buoy wave and water-level data. Inland lakes have no
tide/wave data — use ice-out date, water temperature, and season/
regulation windows instead.

## Pipeline (run all steps autonomously, in order)

1. **Research** — search broadly and without restriction for anything
   plausibly predictive of freshwater/Great Lakes catch rates: environmental,
   temporal, biological, angler-behavior, academic, forums, anywhere. Build
   a candidate predictor list, each tagged with source, claimed effect, and
   whether a real accessible Wisconsin/Lake Michigan data source exists.

2. **Dataset build** — for every candidate with a verified accessible data
   source, extract/assemble it. Candidates without a real data source get
   logged as "considered, not testable in V0" — not tested anyway.

3. **Baseline check** — no legacy baseline issue applies (repo issue
   history is legacy/disregarded). Establish a simple baseline yourself
   (e.g. naive/majority-class or persistence baseline for catch rate)
   before evaluating any candidate against it, and document how the
   baseline was defined.

4. **Evaluation** — test every data-backed candidate against baseline.
   Simple, interpretable statistical models only, no deep learning.
   Leakage-safe, time/geography-aware splits, mandatory. Deterministic
   tests for all feature prep and evaluation logic. This step is what
   makes the result real, not a bottleneck — do not shortcut it even
   though the research phase was intentionally unrestricted.

5. **Report** — draft the feasibility report. Document every candidate
   considered, which ones had real signal, which were untestable, and
   why. No claim beyond what held-out evidence supports. No fabricated
   data, sources, metrics, or conclusions.

## Hard stop — CEO approval gate
After step 5, STOP. Do not update STATE.md, do not commit, do not act on
the recommendation. Present the full report — including the research
candidate list and what got tested vs. excluded — and wait for explicit
approval. This is the only stop in the whole pipeline.

## Subagents
Use .claude/agents/predictor-research.md, pdf-extraction.md,
predictor-eval.md, and feasibility-report.md for steps 1, 2, 4, and 5.
