import argparse
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send reconciliation report email.")
    parser.add_argument("--smtp-host", required=True)
    parser.add_argument("--smtp-port", required=True, type=int)
    parser.add_argument("--smtp-user", default="")
    parser.add_argument("--smtp-pass", default="")
    parser.add_argument("--from-addr", required=True)
    parser.add_argument("--recipients", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--results-file", required=True)
    parser.add_argument("--html-file", required=True)
    parser.add_argument("--text-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipients = [item.strip() for item in args.recipients.split(",") if item.strip()]
    if not recipients:
        print("ERROR: recipients are required")
        return 1

    html_body = load_text(args.html_file)
    text_body = load_text(args.text_file)

    message = MIMEMultipart("alternative")
    message["Subject"] = args.subject
    message["From"] = args.from_addr
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    smtp = smtplib.SMTP(args.smtp_host, args.smtp_port, timeout=60)
    try:
        if args.smtp_user and args.smtp_pass:
            try:
                smtp.starttls()
            except Exception:
                pass
            smtp.login(args.smtp_user, args.smtp_pass)
        smtp.sendmail(args.from_addr, recipients, message.as_string())
        print("SUCCESS: report email sent")
    finally:
        smtp.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
