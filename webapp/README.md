# V1 Review — Web App

Hosted version of `ui/v1_review_app.py` (the local .exe review tool). Same
data (`data/v1/v1_full_run_results.db`), same data-access module
(`ui/v1_review_data.py`, imported directly, not duplicated), same
evidentiary discipline — narrative text, temperature source/tier, and
disclosed threshold disputes are shown exactly as stored.

## Run locally

```bash
pip install -r webapp/requirements.txt
python webapp/app.py
```

Then open http://127.0.0.1:5000/. This runs Flask's built-in dev server —
fine for local use, **not for public exposure** (its debugger allows
arbitrary code execution if reached from outside). For any public-facing
run (including a quick local demo tunnel), use a real WSGI server instead,
e.g.:

```bash
pip install waitress   # Windows-friendly; gunicorn works the same way on Linux/Mac
python -c "from waitress import serve; import sys; sys.path.insert(0,'webapp'); import app; serve(app.app, host='127.0.0.1', port=5000)"
```

## Deploy to Render (recommended — free tier, simplest path)

This repo includes `render.yaml` at the root, which Render reads
automatically as a Blueprint. Deployment requires one manual step that
only the repo owner can do (account creation/GitHub authorization isn't
something that can be automated on someone else's behalf):

1. Go to https://render.com and sign up (free — GitHub login is easiest).
2. Click **New > Blueprint**, and select the `jsopa1/fishin` repository.
   Render will detect `render.yaml` automatically.
3. Click **Apply** / **Deploy**. Render will run
   `pip install -r webapp/requirements.txt` then start
   `gunicorn --chdir webapp app:app --bind 0.0.0.0:$PORT`.
4. Once deployed, Render gives you a permanent URL like
   `https://fishin-v1-review.onrender.com`.

The app reads `data/v1/v1_full_run_results.db` directly from the deployed
repo checkout — no separate database service needed. To refresh the data
after re-running `analysis/v1_full_run.py`, commit and push the updated
`.db` file; Render (if auto-deploy is left on, the default) redeploys
automatically.

**Free-tier note:** Render's free web services spin down after a period
of inactivity and take ~30-60 seconds to wake back up on the next
request — normal for a free tier, not a bug.
