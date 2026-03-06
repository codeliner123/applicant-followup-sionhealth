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
- Deploy with this repository root; `vercel.json` routes all requests to the Flask app entrypoint.
- Configure environment variables in Vercel project settings:
  - `SENDER_EMAIL`
  - `SENDER_PASSWORD`
  - `FLASK_SECRET_KEY`
