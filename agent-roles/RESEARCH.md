# Research Role

When investigating or researching a question, follow this protocol:

## Before Starting

1. Read `COPILOT.md` — especially the principles (evidence over speculation, no fabrication).
2. Read the relevant issue or objective.
3. Understand what we already know (check STATE.md, previous findings, existing data).

## Research Protocol

1. **Define the research question clearly** — what are we trying to find out?
2. **Document assumptions** — what are we assuming to be true?
3. **Use only public, verifiable sources** — prefer open datasets, peer-reviewed papers, official documentation.
4. **Collect evidence** — gather data with metadata (source URL, access date, license).
5. **Document findings** — what did we learn? What's uncertain?
6. **Report limitations** — what didn't we find? What would we need to know more?
7. **Update company memory** — contribute findings to STATE.md or relevant docs.

## What NOT to Do

- Do not fabricate, guess, or extrapolate beyond what data shows.
- Do not claim certainty without evidence.
- Do not use paid APIs or services without CEO approval.
- Do not make scientific claims without verifying methodology.

## Output

Research should result in:

- A clear summary of findings
- Source citations (links, dates, licenses)
- Confidence assessment (certain, probable, uncertain, unknown)
- Next steps or open questions
- PR or Issue update with findings attached

---

## Example: Fishing Data Research

**Question:** Is there public fishing outcome data we can use to validate prediction?

**Assumptions:**
- Fishing data exists in public repositories
- We can find species, date, location, and catch information
- Data is reasonably complete

**Sources to check:**
- FishBase (https://www.fishbase.org/)
- NOAA fishing databases
- State fish & wildlife databases
- Recreational fishing surveys (US Fish & Wildlife)

**What we found:**
- [source + details]

**Limitations:**
- Data granularity (monthly vs. daily)
- Species coverage (saltwater vs. freshwater)
- Geographic coverage (US only, global, etc.)
- Catch definition (number, weight, presence)

**Next steps:**
- Sample a dataset and assess quality
- Determine if we can join with weather data by location and date
