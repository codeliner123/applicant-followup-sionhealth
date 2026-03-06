import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path("/tmp") if os.getenv("VERCEL") else BASE_DIR
UPLOAD_DIR = RUNTIME_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = RUNTIME_DIR / "mail_log.txt"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
DEFAULT_FORM_URL = "https://forms.gle/Bg1xgS1RaC1765HE8"


def append_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def build_email(name: str, recipient_email: str, form_url: str) -> MIMEMultipart:
    subject = "Update on Your Application"
    plain_body = (
        f"Thanks {name}, we had limited openings, so we couldn’t offer a position. "
        f"Here’s a feedback request form: {form_url}"
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#f6f8fb; padding:24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
          <tr>
            <td align="center">
              <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:12px;padding:24px;">
                <tr>
                  <td>
                    <h2 style="margin-top:0;color:#111827;">Application Update</h2>
                    <p style="color:#374151;font-size:16px;line-height:1.6;">
                      Thanks {name}, we had limited openings, so we couldn’t offer a position.
                      Here’s a feedback request form.
                    </p>
                    <div style="text-align:center;margin:32px 0;">
                      <a href="{form_url}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:600;display:inline-block;">
                        Share Feedback Form
                      </a>
                    </div>
                    <p style="color:#6b7280;font-size:13px;">If the button does not work, open this link: {form_url}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL or ""
    message["To"] = recipient_email
    message.attach(MIMEText(plain_body, "plain"))
    message.attach(MIMEText(html_body, "html"))
    return message


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", default_form_url=DEFAULT_FORM_URL)


@app.route("/process", methods=["POST"])
def process_csv():
    form_url = request.form.get("form_url", "").strip()
    dry_run = request.form.get("dry_run") == "on"
    csv_file = request.files.get("csv_file")

    if not csv_file or not csv_file.filename:
        flash("Please upload a CSV file.")
        return redirect(url_for("index"))

    if not form_url:
        flash("Please provide a Google Form URL.")
        return redirect(url_for("index"))

    if not dry_run and (not SENDER_EMAIL or not SENDER_PASSWORD):
        flash("Missing SENDER_EMAIL or SENDER_PASSWORD in .env")
        return redirect(url_for("index"))

    safe_name = secure_filename(csv_file.filename)
    if not safe_name.lower().endswith(".csv"):
        flash("Only CSV files are supported.")
        return redirect(url_for("index"))

    upload_path = UPLOAD_DIR / safe_name
    csv_file.save(upload_path)

    try:
        df = pd.read_csv(upload_path)
    except Exception as exc:
        flash(f"Could not read CSV: {exc}")
        return redirect(url_for("index"))

    required_columns = {"Name", "Email"}
    if not required_columns.issubset(df.columns):
        flash("CSV must contain Name and Email columns.")
        return redirect(url_for("index"))

    df = df[["Name", "Email"]].copy()
    df["Email"] = df["Email"].astype(str).str.strip()
    df["Name"] = df["Name"].astype(str).str.strip()

    total_rows = len(df)
    deduped_df = df.drop_duplicates(subset=["Email"], keep="first")
    duplicate_count = total_rows - len(deduped_df)

    results = []
    sent_count = 0
    failed_count = 0

    smtp = None
    if not dry_run:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)

    try:
        for _, row in deduped_df.iterrows():
            name = row["Name"]
            email = row["Email"]

            if not name or name.lower() == "nan" or not email or email.lower() == "nan":
                failed_count += 1
                error = "Missing Name or Email"
                append_log(f"FAILED | {name} <{email}> | {error}")
                results.append({"name": name, "email": email, "status": "Failed", "error": error})
                continue

            if dry_run:
                results.append({"name": name, "email": email, "status": "Dry Run", "error": "Not sent"})
                append_log(f"DRY-RUN | {name} <{email}> | Validated")
                continue

            try:
                message = build_email(name, email, form_url)
                smtp.sendmail(SENDER_EMAIL, [email], message.as_string())
                sent_count += 1
                append_log(f"SUCCESS | {name} <{email}> | Email sent")
                results.append({"name": name, "email": email, "status": "Sent", "error": ""})
            except Exception as exc:
                failed_count += 1
                append_log(f"FAILED | {name} <{email}> | {exc}")
                results.append({"name": name, "email": email, "status": "Failed", "error": str(exc)})

            time.sleep(1)
    finally:
        if smtp is not None:
            smtp.quit()

    summary = {
        "total_rows": int(total_rows),
        "unique_recipients": int(len(deduped_df)),
        "duplicate_count": int(duplicate_count),
        "sent_count": int(sent_count),
        "failed_count": int(failed_count),
        "dry_run": dry_run,
    }
    session["last_results"] = results
    session["last_summary"] = summary

    append_log(
        f"SUMMARY | total_rows={total_rows}, unique={len(deduped_df)}, duplicates={duplicate_count}, sent={sent_count}, failed={failed_count}, dry_run={dry_run}"
    )

    return redirect(url_for("results"))


@app.route("/results", methods=["GET"])
def results():
    summary = session.get("last_summary")
    results_data = session.get("last_results")
    if not summary:
        flash("No results available yet. Upload a CSV first.")
        return redirect(url_for("index"))
    return render_template("results.html", summary=summary, results=results_data)


@app.route("/log", methods=["GET"])
def show_log():
    if LOG_PATH.exists():
        log_content = LOG_PATH.read_text(encoding="utf-8")
    else:
        log_content = "No log entries yet."
    return render_template("log.html", log_content=log_content)


if __name__ == "__main__":
    app.run(debug=True)
