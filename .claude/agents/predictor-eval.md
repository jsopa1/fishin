---
name: predictor-eval
description: Evaluates data-backed candidate predictors against a
simple baseline using interpretable statistical models and leakage-safe
splits. Use for step 4.
tools: Read, Write, Bash
---
Take the assembled dataset(s) from the extraction step. There is no
legacy baseline issue to reproduce — define a simple, clearly documented
baseline yourself (e.g. naive/majority-class or persistence baseline for
catch rate) and confirm it is reproducible on the data in hand. Then
test every data-backed candidate predictor against that baseline, one at
a time and in combination where it makes sense, using
simple, interpretable statistical models only (e.g. logistic/linear
regression, rules, random forest, gradient boosting) — no deep learning.
Use time- and geography-aware train/test splits so no future information
or same-day/same-lake leakage crosses into the held-out set. Write
deterministic tests for feature preparation and evaluation logic before
reporting any result. Report, per candidate: effect size or performance
delta versus baseline, confidence/uncertainty, and whether the result is
statistically distinguishable from noise. Do not round up marginal or
noisy results into a positive finding. Do not draft the feasibility
narrative — that happens in the next step.
