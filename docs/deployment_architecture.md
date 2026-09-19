# How fishin is deployed in the cloud

![Cloud deployment](diagrams/deployment_architecture.svg)

`DEPLOY.md` is the click-by-click launch checklist. This document is the architecture behind it: what
runs where, how data stays fresh, what breaks first as traffic grows, and what to do about it, in order.

## 1. What runs today

| Piece | Where | Notes |
|---|---|---|
| Web app | **Render** web service (`render.yaml`) | `gunicorn --chdir webapp app:app`, Python 3.12, free plan. Flask serves the pages and one JSON feed. |
| Content database | SQLite file **committed to the repo** (`data/v1/v1_full_run_results.db`, ~25 MB) | Read-mostly. Ships with every deploy, so there is no database server to run. |
| Freshness job | **GitHub Actions**, every 4 hours (`refresh-temperatures.yml`) | Refreshes the ~65 sensor-backed waterbodies and, since #052, one NWS air temperature per quarter-degree cell for spots with no water reading (~60 calls, ~80 s). Verifies the database, commits it, and Render auto-deploys. |
| Tests | GitHub Actions on every push | 741 tests must pass. |
| Data sources | USGS, NOAA NDBC, NWS, WDNR, GBIF | Fetched by the refresh job, or live per visit (weather, regulations). Images are stored in the repo (fetched once from Wikimedia, public-domain only). |
| The user's device | Any modern browser | Ranks spots locally. Preferences, saved spots, last spot and location **never leave the device**, so there is no user database and no login. |

There is deliberately no account system, queue, cache server or separate database. That is why the whole
production footprint is one small web service plus one scheduled job.

## 2. How a request flows

1. The browser loads a page (server-rendered Jinja) and the ~110 KB gzipped `/recommend/feed.json`
   (identical for everyone, ETag-cached, rebuilt only when the data changes).
2. `recommend.js` ranks the feed in the browser using the Profile preferences and, if allowed, location.
3. A spot page adds two live calls made server-side: NWS conditions and WDNR regulations (both cached).
4. Every four hours the refresh job commits a new database; Render redeploys; on start the app rebuilds
   the feed in the background (~17 s) so the first visitor does not wait.

## 3. Gaps found while writing this, and the fixes

These are real, verified in the repo, and worth doing before launch traffic:

1. **Analytics would be wiped every four hours.** The analytics database defaults to a path inside the app
   directory (`FISHIN_USER_DB_PATH`, default `data/v1/user_data.db`, not committed). Render's disk is
   ephemeral and the refresh job redeploys the app every four hours, so page-view and return-visit counts
   reset each time. **Fix:** add a Render persistent disk (e.g. 1 GB mounted at `/var/data`) and set
   `FISHIN_USER_DB_PATH=/var/data/user_data.db`.
2. **Git is the wrong delivery vehicle for a 25 MB database.** The repo is already ~230 MB with 18 database
   commits in three days, and that grows with every refresh. **Fix (next quarter, not urgent):** have the job
   upload the database to object storage (Cloudflare R2 or S3) or a GitHub Release asset, and have the app
   download it on start and on a timer. Keep the last committed copy as a fallback so the app still boots
   with no network. Until then, squash old database history occasionally.
3. **Cold starts.** On the free plan the service sleeps after ~15 minutes idle and takes 30–60 s to wake,
   which reads as "broken" to a first-time visitor from a social post. **Fix:** Starter plan (about $7/month,
   check current pricing) before any launch push.
4. **Do not use `gunicorn --preload`.** The feed warm-up runs in a background thread started at import;
   threads do not survive the fork, so with `--preload` the warm-up silently never runs in the workers.
   Use two plain workers (`--workers 2`); each warms itself, and the lock makes the first feed request wait
   for the build rather than run it twice.
5. **No alerting.** `/healthz` already reads the database and reports `temperatures_refreshed_at`. Point a
   free uptime monitor at it and alert if the timestamp is older than ~12 hours, since a stalled refresh
   degrades quietly to "no data" (by design: readings over 36 h are dropped, not shown stale).

## 4. Recommended path, in order

| Step | What | Cost / effort |
|---|---|---|
| 0 | Deploy the Blueprint (`DEPLOY.md` §1) and enable the refresh workflow (§2) | free, ~15 min |
| 1 | Persistent disk + `FISHIN_USER_DB_PATH` (gap 1) | ~$0.25/GB-month, 10 min |
| 2 | Starter plan (gap 3) and `--workers 2` start command (gap 4) | ~$7/month |
| 3 | Buy a typeable domain (DEPLOY.md §3), put **Cloudflare** (free) in front: TLS, CDN for `/static/*` and the feed, burst protection | domain ~$10–15/year |
| 4 | Uptime monitor on `/healthz` with a freshness alert (gap 5) | free |
| 5 | Move database delivery off git to object storage (gap 2) | small change, ~1 day |
| 6 | Set `FISHIN_SECRET_KEY` from Render's generated value (already in the Blueprint) and confirm no debug mode in production | done in Blueprint |

## 5. Scaling limits, honestly

- The app is read-mostly SQLite with per-process caches, so it scales **up** (bigger instance, more
  workers) far more easily than **out**. One Starter instance comfortably serves a launch-day burst because
  the feed and static files are cacheable at the CDN, and the only per-visit server work is a spot page's
  two cached upstream calls.
- The first thing to strain is the upstream APIs' courtesy limits (NWS, WDNR), not our CPU. Both are cached
  per spot; if traffic grows, lengthen the cache TTL before adding servers.
- If accounts or server-side personalisation are ever added (the product currently promises none), the
  privacy design (#047/#049) would need revisiting first; a real database (Postgres) would then be the
  right step, not more SQLite.

## 6. Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `FISHIN_SECRET_KEY` | Signs the CSRF/session cookie | Generated by `render.yaml` |
| `FISHIN_USER_DB_PATH` | Where analytics and feedback are stored | `data/v1/user_data.db` (**set to the persistent disk**) |
| `FISHIN_NO_WARM` | `1` skips the background feed warm-up (tests, one-off scripts) | unset |
| `PYTHON_VERSION` | Render runtime | `3.12.0` |
