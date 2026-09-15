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
   `render.yaml` and fills everything in, including a freshly generated
   `FISHIN_SECRET_KEY` — nothing to type in by hand.
3. Confirm. First build takes 2-3 minutes.

There is nothing else to configure: no database to provision, no manual
secrets. The content SQLite file ships in the repo, and the app only
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

## 3. Attach a persistent disk before real signups (~5 minutes)

Skip this step and the app itself works fine — but every account, logged
catch, and feedback submission will be **silently destroyed** on the next
scheduled redeploy (step 2 triggers one roughly every 4 hours). Do this
before telling anyone to create an account, not after.

Why: `webapp/user_data.py` deliberately keeps accounts/catches/feedback in
a *separate* SQLite file from the content database, specifically so the
temperature-refresh Action doesn't overwrite them. That separation solves
half the problem — but Render's free tier has no persistent disk by
default, so that separate file still only exists on the current
container's local storage, gone on every redeploy regardless.

1. Render → your service → **Disks** → **Add Disk**. A small disk (1 GB
   is overkill for this) is enough — this is Render's cheapest paid
   add-on, not the free tier.
2. Mount it at, e.g., `/var/data`.
3. Add an environment variable: `FISHIN_USER_DB_PATH` = `/var/data/user_data.db`.
4. Redeploy. Confirm by creating a test account, then manually
   redeploying again (**Manual Deploy → Deploy latest commit**) — log
   back in with that test account afterward to confirm it survived.

If you'd rather not pay for a disk yet, that's a reasonable call — just
don't advertise the account/catch-log feature publicly until this is
done. Everything else in the app (conditions, species, regulations, the
anonymous localStorage "Save this spot" bookmark) works with no account
and isn't affected either way.

---

## 4. Point a domain at it (needs a purchase)

`fishin` is not a searchable name — it cannot be spelled reliably from
hearing it, and it competes with every other fishing app for the word.
Before spending attention on launch posts, get a name someone can type
after hearing it once.

Once purchased: Render → your service → **Settings → Custom Domains**,
add the domain and copy the DNS records it gives you to your registrar.
TLS is issued automatically.

---

## 5. Before posting anywhere public

- [ ] `/healthz` returns `"status": "ok"` on the real URL
- [ ] The refresh workflow has completed at least one successful run
- [ ] If accounts are going live, step 3's disk is attached and verified
      to survive a redeploy
- [ ] Paste the URL into the [Facebook sharing debugger](https://developers.facebook.com/tools/debug/)
      and confirm the share card renders — the launch channels are all
      link-card surfaces, and a bare link reads as spam there
- [ ] Open a spot page on an actual phone, not a resized browser window
- [ ] Try "Add to Home Screen" on that phone — `/manifest.json` and the
      icons are already wired up
- [ ] Read `/privacy` and `/terms` once yourself — both are a drafted
      starting point, not reviewed by a professional; decide whether
      that's good enough for this launch's scale

---

## What is still genuinely missing

Honest list, so none of this is discovered publicly:

- **The name.** See step 4.
- **A persistent disk for accounts.** See step 3 — the one infrastructure
  gap that can cause real, silent data loss if skipped.
- **Password-reset email.** No email-sending infrastructure exists, so a
  forgotten password currently has no recovery path. Needs a
  transactional email provider (Postmark, SES, Resend — a real account
  you'd create) before this is safe to rely on at any real scale.
- **Real legal review** of `/privacy` and `/terms`. Both describe the
  app's actual behavior accurately, but neither has been reviewed by a
  qualified professional.
