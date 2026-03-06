# Recruitment Rejection Email Tool

Flask app for uploading a candidate CSV (`Name`, `Email`) and sending personalized rejection emails with a feedback form button.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file from `.env.example` and set:
   - `SENDER_EMAIL`
   - `SENDER_PASSWORD` (Gmail app password)
4. Run:
   ```bash
   flask --app app run --debug
   ```

## Features

- Dark-mode glassmorphism dashboard with CSV + Google Form input.
- Dry-run mode for validation without sending.
- CSV processing with `pandas`.
- Deduplication by email.
- Skips and logs rows with missing `Name` or `Email`.
- Sends multipart (plain + HTML) emails via Gmail SMTP (`smtp.gmail.com:587` + `starttls`).
- 1-second delay between send attempts.
- `mail_log.txt` with timestamped success/failure entries.
- Results page with summary + per-recipient status table.
- Inline log viewer.


## Vercel Deployment

- The app is serverless-compatible and automatically uses `/tmp` for uploads and `mail_log.txt` when running on Vercel (`VERCEL` env detected).
- Deploy with this repository root; `vercel.json` maps all routes to `app.py` using the modern `functions` config (no legacy `builds`).
- Python is pinned via `.python-version` to match Vercel runtime resolution.
- Configure environment variables in Vercel project settings:
  - `SENDER_EMAIL`
  - `SENDER_PASSWORD`
  - `FLASK_SECRET_KEY`


## Add your provided credentials

1. Create `.env` in the project root (already done locally in this environment):
   ```env
   SENDER_EMAIL=your-gmail@gmail.com
   SENDER_PASSWORD=your-16-digit-app-password
   FLASK_SECRET_KEY=your-random-secret
   ```
2. Keep `.env` out of git (this repo now includes `.gitignore` for that).
3. For Vercel, set the same keys in **Project Settings → Environment Variables**:
   - `SENDER_EMAIL`
   - `SENDER_PASSWORD`
   - `FLASK_SECRET_KEY`


## What you need to do (your end)

1. In Vercel project settings, add environment variables:
   - `SENDER_EMAIL`
   - `SENDER_PASSWORD`
   - `FLASK_SECRET_KEY` (use a strong random value, not `xoxo`)
2. Trigger a redeploy from Vercel dashboard (**Deployments → Redeploy**) or push this branch.
3. After deploy, open `/health` on your Vercel URL to verify the function is running.
4. Upload a CSV with columns `Name,Email` and run **Dry run** first, then send.

### Generate a strong Flask secret key

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```


## Troubleshooting: Vercel says `secure-filename` cannot be resolved

If Vercel logs show an error like `your project depends on secure-filename`, that deployment is building an **older commit/branch**.

This branch uses Werkzeug's built-in helper and does **not** depend on `secure-filename`:
- import: `from werkzeug.utils import secure_filename`
- requirements: only Flask, pandas, python-dotenv

### What to do in Vercel

1. Open your Vercel project → **Deployments**.
2. Select the failed deployment and confirm the **Source commit SHA**.
3. Redeploy after pushing/merging the latest commit from this branch to `main`.
4. In **Project Settings → Git**, ensure Production Branch is `main` (or whichever branch you intend).
5. In **Project Settings → Environment Variables**, set:
   - `SENDER_EMAIL`
   - `SENDER_PASSWORD`
   - `FLASK_SECRET_KEY`
6. Verify with `https://<your-domain>/health` after deployment.
