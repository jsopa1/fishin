---
name: pdf-extraction
description: Extracts and assembles datasets from WDNR creel survey PDFs
and other verified public data sources (NOAA CO-OPS/buoy, ice-out, water
temperature) for candidates identified in research. Use for step 2.
tools: WebFetch, Read, Write, Bash
---
Take the candidate predictor list from the research step. For every
candidate marked as having a real, accessible data source for
southeastern Wisconsin or Lake Michigan, fetch or download the source
(WDNR creel survey PDFs, NOAA CO-OPS/buoy data, ice-out records, water
temperature series) and extract it into a clean, structured dataset
(e.g. CSV/parquet) with clear provenance for each row (source URL/file,
retrieval date, lake or station). Preserve outcome data (catch rates)
exactly as reported in creel surveys — do not infer or estimate values
the source does not state. Any candidate whose claimed data source turns
out not to be real, accessible, or specific enough on inspection gets
reclassified as "considered, not testable in V0" and is not force-fit
into the dataset. Do not evaluate or model anything — that happens in a
later step. Output the assembled dataset(s) plus a manifest of what was
extracted from where, and the updated candidate list showing which
became testable and which did not.
