# Data Science Role

When working on data, modeling, or validation:

## Before Starting

1. Read `COPILOT.md` — especially principles, Python constraints, and testing requirements.
2. Read `DECISIONS.md` decision #002 — we prefer simple models before complex ML.
3. Understand the current hypothesis and what we're trying to predict.

## Data Science Protocol

### Data Preparation

1. **Document data sources** — where did it come from? What's the license? How fresh is it?
2. **Inspect data quality** — missing values, duplicates, outliers, data types.
3. **Create reproducible pipelines** — all data operations must be version-controlled and documented.
4. **No fabrication** — never fill gaps with fabricated values; document missing data instead.
5. **Test for leakage** — ensure training and test data don't leak information.

### Modeling

1. **Start simple** — establish baseline performance with rules or simple statistical models first.
2. **Measure against baseline** — any complex model must beat the baseline significantly.
3. **Use proper train/test/validation splits** — evaluate on held-out data from the past (time-series data requires careful splits).
4. **Document assumptions** — what does the model assume about the data?
5. **Write tests** — validation logic, preprocessing, and model inference must have tests.

### Validation

1. **Report reproducibly** — others should be able to run your analysis and get the same results.
2. **Quantify uncertainty** — confidence intervals, standard errors, or cross-validation scores (not just point estimates).
3. **Check for overfitting** — performance on held-out data vs. training data.
4. **Validate against reality** — do predictions make intuitive sense? Do they align with domain knowledge?

## Python Standards

- All code must be in `agent_system/` or `src/` (no scripts scattered around).
- All meaningful code changes must have tests in `tests/`.
- Use `pytest` for testing; tests run with `python -m pytest`.
- Document code with docstrings; explain *why*, not just *what*.
- Keep dependencies minimal; ask CEO before adding new packages.

## Output

Data science work should result in:

- Reproducible code (PR with tests)
- Documented findings and metrics
- Validation results (accuracy, precision, recall, F1, etc. depending on task)
- Limitations and confidence assessment
- Recommended next steps

---

## Example: Establish Baseline

**Hypothesis:** Weather, seasonality, location, and species contain enough signal to predict fishing conditions better than chance.

**Approach:**
1. Define "good fishing conditions" measurably (e.g., high catch rate on a given day).
2. Collect public weather and fishing data joined by location and date.
3. Build a simple baseline model (e.g., logistic regression on weather features).
4. Evaluate on held-out historical data (past month/season we didn't train on).
5. Report accuracy, precision, recall — compare to a trivial baseline (always predict "good" or "random").

**Success:** If baseline beats random significantly and results make intuitive sense, we can justify more complex modeling.
