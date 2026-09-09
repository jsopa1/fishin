# V1 Web App Polish Report

Status: honest, criterion-by-criterion account of one thorough iteration pass
through the 7 polish criteria — not a summary that rounds up. Every "met"
claim below is backed by a concrete check (a test, a measurement, or a
verified live request), not an assertion. Completed within 1 of the
15-iteration budget: each criterion was worked, a real issue was usually
found, fixed, and re-verified before moving to the next, matching the
required process.

---

## 1. Visual/UX — **Met**

Two real overflow bugs were found (not assumed-fine) by measuring actual
`document.body.scrollWidth` vs `clientWidth` in a real browser at 375px
(mobile), 768px (tablet), and 1280px (desktop), not by eyeballing
screenshots alone:

- **Table overflow on mobile**: the results table on Browse/Failures
  forced the whole page to scroll horizontally (`scrollWidth` 567 vs
  `clientWidth` 375). Fixed by wrapping each table in a `.table-scroll`
  container with `overflow-x: auto`, so only the table scrolls, not the
  page. Verified fixed: `scrollWidth` now equals `clientWidth` (375/375)
  on the same real query.
- **Long text/URL overflow on the detail page**: a real 58-character
  waterbody name ("Rush River (Middle section — St. Croix Co. line to Hwy
  10)") and long temperature-source URLs forced `scrollWidth` to 429 and
  412 respectively. Fixed with `overflow-wrap: anywhere` on the `<h1>`,
  the metadata `<dl>`, the narrative block, and species cards. Verified
  fixed on the same real record (375/375).
- A fix to the table-overflow CSS initially also widened the small
  Summary-page stat tables (a real regression, caught immediately by
  re-checking that page) — scoped the `min-width` rule to
  `.table-scroll table` only, verified both pages clean afterward.

Edge cases verified against real stored records: the longest name in the
database (58 chars), a `no_data` waterbody (Lake Monona), a stocking-only
caveat (screenshotted), and the disputed-threshold record (Big Moon Lake).
All render without overflow at all three tested widths.

## 2. Functional correctness — **Met**

Every filter and combination was tested against the real 2,296-row
database, not just the happy path: name, county, species, tier
individually and combined (2- and 3-way), case-insensitive county
matching, no-match cases for each filter, and an invalid tier value. All
returned correct results with no errors.

One real bug found and fixed: unescaped `%` and `_` characters in
search input were being interpreted as SQL `LIKE` wildcards instead of
literal characters (e.g., searching `"50%"` would match `"50" + anything`
rather than requiring a literal `%`). Not a security issue — queries were
already parameterized — but a real correctness gap. Fixed with a
`_like_pattern()` escaping helper (`ESCAPE '\'` in SQL) applied to all
four `LIKE` clauses (waterbody search × name/county/species,
failures search × waterbody/species). Two new regression tests added and
passing (`test_percent_sign_in_query_treated_as_literal_not_wildcard`,
`test_underscore_in_query_treated_as_literal_not_single_char_wildcard`).

## 3. Error handling — **Met**

Three real gaps found and fixed, verified with both manual requests and
new automated tests (`WebAppErrorHandlingTests`, 5 tests):

- **Invalid `tier` value** (e.g. a hand-edited URL) silently returned "0
  results" with no explanation. Fixed: falls back to "all" and shows a
  visible note ("... is not a recognized presence tier -- showing all
  tiers instead"), confirmed to still show real results, not an empty
  page.
- **Missing database** (a genuine failed-data-load scenario, tested by
  patching `find_db_path` to point at a nonexistent file — not by
  touching the real database) previously produced a silent, unexplained
  empty page on every route. Fixed: every route now returns HTTP 503 with
  a clear "results database is currently unavailable" message.
- **Missing query parameters** on `/waterbody` (e.g. a malformed or
  truncated link) now returns 400 with a clear message instead of
  whatever `None`/`None` would have produced.
- Added a global 404 handler (styled, on-brand, confirmed to contain no
  "Traceback" or "werkzeug" text) and a 500 handler that never surfaces a
  stack trace to the user.

XSS was checked directly: a `<script>` tag submitted as a search term is
confirmed HTML-escaped in the reflected input value (Jinja2's
autoescaping), not executed.

## 4. Performance — **Met**

Measured directly against the real, full 2,296-row database (3 runs each,
minimum and average reported), not estimated:

| Page | Min | Avg |
|---|---|---|
| Home | 4ms | 18ms |
| Browse, no filter (2,296 rows) | 56ms | 64ms |
| Browse, `tier=stocking_only` (2,245 rows, capped at 500 shown) | 113ms | 119ms |
| Browse, species filter | 70ms | 73ms |
| Summary (multiple aggregate queries) | 41ms | 47ms |
| Failures | 12ms | 17ms |
| Waterbody detail | 7ms | 12ms |

All well under 150ms — no page or query required optimization; nothing
was "noted as slow" without being profiled, because nothing was slow.

## 5. Honesty/framing — **Met, re-verified**

Re-checked (not assumed carried-over from the prior session) via a
targeted grep of every template for risky language ("predict", "catch
rate", "score", "will bite", etc.). Every instance of "prediction" either
explicitly negates a catch-rate claim or refers to the underlying
physiology-vs-temperature comparison record (the same terminology already
used throughout this project's database schema and the .exe tool — kept
consistent rather than renamed mid-project). The homepage's "What this is
— and isn't" section, the omnipresent disclaimer banner on every page, and
the disputed-Muskellunge-threshold text were all re-confirmed present and
unaltered by this polish pass's CSS/error-handling changes.

## 6. Accessibility basics — **Met**

- **Color contrast**: computed WCAG contrast ratios for every real
  foreground/background color pair in the stylesheet. One failure found:
  the stocking-only tag color (`#8a6d00` on `#fff3cd`) measured 4.44:1,
  just under the 4.5:1 AA threshold for normal-size text. Fixed to
  `#7a5f00` (5.47:1). All other pairs already cleared 4.5:1 (lowest
  remaining: 4.92:1).
- **Alt text**: the site has no `<img>` elements at all (verified by
  grep) — the only graphical element is an emoji used as inline text,
  which doesn't require alt text. Nothing to fix.
- **Keyboard navigation**: verified programmatically that all 516
  interactive elements on a real results page (nav links, form fields,
  every waterbody row link) are genuinely focusable
  (`element.focus()` → `document.activeElement === element` for all of
  them), and confirmed no CSS anywhere suppresses the browser's default
  focus outline (`outline: none` does not appear in the stylesheet).

## 7. Attribution — **Met, re-verified**

Re-confirmed the WDNR/USGS/NWS attribution text from the prior session's
Part 3 research survived this pass's template edits unchanged, and
renders correctly on every page (present in `base.html`'s footer,
included in every template). Wording still matches what was actually
checked: USGS's own recommended "courtesy of" public-domain credit
format, NWS's public-domain/no-endorsement terms, and WDNR's fair-use/
non-commercial framing.

---

## Deployment

Redeployed the polished local server, verified live end-to-end against
the same public URL used for the prior session's demo
(`https://epinions-sir-studying-events.trycloudflare.com` — a temporary,
account-less Cloudflare tunnel; see the note in the previous session's
report about why a permanent Render deployment still requires one manual,
non-automatable account-creation step from the repo owner). Re-ran the
exact verification suite against the live URL after redeployment: home
page, the Devils Lake dedup fix, the full disputed-Muskellunge-threshold
text, the new invalid-tier graceful-degradation message, a 404 with no
stack trace, the Summary page's total (2,296, matching
`docs/v1_full_run_report.md` exactly), and the attribution footer — all
confirmed correct on the live public URL, not just locally.

## Test suite

177 tests passing project-wide (26 new/updated this session: 2 LIKE-escaping
regression tests + 5 new error-handling tests, plus updates to existing
assertions where behavior intentionally changed).

## What was NOT done (explicitly out of scope, not overlooked)

Per the hard limits: no new functionality was added beyond what these 7
criteria required. No maps, habitat data, or other V2-shaped features were
touched. The underlying prediction/physiology logic
(`analysis/v1_conditions_biology_forecast.py`'s threshold matching,
temperature-source resolution, and species-presence tiering, and
`analysis/v1_full_run.py`) was **not** modified in this session — those
files were untouched. `ui/v1_review_data.py` **was** touched, but only its
search/filter SQL-building helpers (the `LIKE`-escaping fix in Criterion
2) — a browsing/search-correctness fix, not a change to any prediction
result, threshold, or tier already stored in the database.
