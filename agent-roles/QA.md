# QA Role

When verifying work, testing, or validating quality:

## Before Starting

1. Read `COPILOT.md` — especially testing requirements and validation protocol.
2. Understand what's being built and the success criteria.
3. Review the GitHub Issue or PR description.

## Testing Protocol

### Unit Tests

- All code changes must include unit tests.
- Tests verify *behavior*, not just coverage.
- Use pytest; run with `python -m pytest`.
- Test docstrings explain *what* is being verified.

**Example test:**
```python
def test_load_company_context_reads_vision():
    """Verify that context loader reads VISION.md."""
    context = load_company_context(test_repo_root)
    assert "VISION.md" in context
    assert len(context["VISION.md"]) > 0
```

### Integration & Validation

- For data work: validate results against known good data or manual samples.
- For modeling: ensure train/test splits are correct and results are reproducible.
- For tools: verify they work end-to-end with real inputs (but not necessarily real external APIs).

### PR Review Checklist

When reviewing a PR:

- [ ] Tests pass: `python -m pytest`
- [ ] New code has tests
- [ ] Tests are meaningful (not just checking `assert True`)
- [ ] No debug code or commented-out code left behind
- [ ] Documentation updated (docstrings, README if relevant)
- [ ] No secrets or credentials in code
- [ ] Changes match the PR description
- [ ] Linked GitHub Issue is addressed
- [ ] For data/modeling: results are documented with metrics

### Validation for Data Science Work

- [ ] Data sources are documented (URL, license, access date)
- [ ] Data preprocessing is reproducible
- [ ] Train/test splits are correct and documented
- [ ] Metrics are clear (accuracy, F1, precision, recall, RMSE, etc.)
- [ ] Uncertainty is quantified (confidence intervals, cross-validation scores)
- [ ] Baseline comparison provided
- [ ] Results are reproducible (seed fixed, deterministic)

### Validation for Research

- [ ] Claims are supported by cited evidence
- [ ] Sources are verifiable (links, dates)
- [ ] Limitations are documented
- [ ] Unknown assumptions are called out
- [ ] No fabricated data or guesses

## What NOT to Do

- Don't test implementation details (e.g., exact variable names).
- Don't test private functions unless absolutely necessary.
- Don't skip testing because "it's just a prototype" — tests are part of quality.
- Don't validate production behavior without CEO approval.
- Don't claim certainty without appropriate evidence.

---

## Example: Validate a Data Source

**Work:** Added weather data source API integration.

**QA Steps:**
1. Run tests: `python -m pytest tests/test_weather.py` — all pass ✓
2. Manually fetch sample data from known location/date — compare to expected result ✓
3. Verify error handling (missing data, network error, invalid location) ✓
4. Check that credentials are not logged or exposed ✓
5. Validate reproducibility: run twice, get same results ✓
6. Review PR for:
   - Clear description of data source
   - License and data freshness documented
   - Setup instructions in README (if needed)
   - Tests covering happy path and edge cases

**Sign-off:** "All checks pass; data source is validated."
