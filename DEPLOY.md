# Deploying fishin

Everything in this repo is deploy-ready. What is left needs a person with
account access, which is why it is written out step by step rather than
automated.

Current state: the app has only ever run from a temporary Cloudflare
quick-tunnel pointed at a laptop, which dies when the machine sleeps. That
is the single thing standing between this and real users.

---

## 1. Deploy the web app (~10 minutes)

`render.yaml` is already correct and the app has been verified to boot
under Render's exact start command (`gunicorn --chdir webapp app:app`).

1. Sign in at [render.com](https://render.com) with the GitHub account
   that owns `jsopa1/fishin`.
2. **New → Blueprint**, pick the `fishin` repo. Render reads
   `render.yaml` and fills everything in.
3. Confirm. First build takes 2-3 minutes.

There is nothing to configure: no environment variables, no secrets, no
database to provision. The SQLite file ships in the repo, and the app only
ever reads it.

**Check it worked** — visit `/healthz`. A healthy deploy returns:

```json
{"status": "ok", "waterbodies": 2296, "temperatures_refreshed_at": "..."}
```

That endpoint reads the database rather than just proving the process
started, so a 200 means the app is genuinely serving real data.

### Free-tier caveat worth knowing

Render's free web services spin down after ~15 minutes idle, so the first
visit after a quiet period takes 30-60 seconds to respond. For a launch
post that sends a burst of traffic at once this is mostly invisible; for
steady trickle traffic it is the main reason to move to the paid tier.

---

## 2. Turn on automatic temperature refresh (~2 minutes)

Water temperature is the only data here that ages in hours, and stale
readings are not cosmetic: during testing one gauge moved 17.0°C → 12.1°C
over 43 hours, a bigger shift than the width of some spawning windows.

`.github/workflows/refresh-temperatures.yml` handles this on a four-hour
schedule, because Render's free tier has no scheduler. It refreshes the 65
sensor-backed waterbodies, verifies the database is still sane, and
commits it back — which triggers Render's auto-deploy.

1. Go to the repo's **Actions** tab and enable workflows if prompted.
2. Open **Refresh water temperatures** → **Run workflow** to confirm it
   works once by hand.
3. Check the run log: expect `Checked 65 | updated 65 | failures 0`.

The workflow needs no secrets — it uses the built-in `GITHUB_TOKEN`.

---

## 3. Point a domain at it (needs a purchase)

`fishin` is not a searchable name — it cannot be spelled reliably from
hearing it, and it competes with every other fishing app for the word.
Before spending attention on launch posts, get a name someone can type
after hearing it once.

Once purchased: Render → your service → **Settings → Custom Domains**,
add the domain and copy the DNS records it gives you to your registrar.
TLS is issued automatically.

---

## 4. Before posting anywhere public

- [ ] `/healthz` returns `"status": "ok"` on the real URL
- [ ] The refresh workflow has completed at least one successful run
- [ ] Paste the URL into the [Facebook sharing debugger](https://developers.facebook.com/tools/debug/)
      and confirm the share card renders — the launch channels are all
      link-card surfaces, and a bare link reads as spam there
- [ ] Open a spot page on an actual phone, not a resized browser window
- [ ] Decide what the "Report a problem" link should point at. It
      currently opens a GitHub issue, which is fine for technical users
      and a dead end for everyone else

---

## What is still genuinely missing

Honest list, so none of this is discovered publicly:

- **No analytics.** If users arrive, you will learn nothing about what
  they did. Adding this needs an account and a privacy decision, so it
  was deliberately left to you.
- **No privacy policy or terms.** Worth an hour with someone qualified
  before a public launch rather than a judgement call made at 2am.
- **Fishing regulations are absent.** Bag limits, length limits and
  season dates are the most-wanted thing this app does not have, and the
  one place WDNR's own free Fishing Finder genuinely beats it on
  substance.
- **No bait or technique guidance.** This is the real moat (nobody else
  ties lure choice to cited physiology) and it is a research task, not an
  engineering one.
