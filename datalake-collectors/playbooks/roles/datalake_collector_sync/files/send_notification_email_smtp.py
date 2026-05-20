import argparse
import csv
import io
import json
import smtplib
import sys
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json_file(path: Path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def build_csv_attachment(processing_results) -> MIMEApplication:
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)

    writer.writerow(
        [
            "Sıra No",
            "Sunucu Adı",
            "Device Role",
            "Lokasyon",
            "Site",
            "Tenant",
            "Sahiplik",
            "IP Adresi",
            "İşlem Durumu",
            "Açıklama/Hata Sebebi",
            "Zaman Damgası",
        ]
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status_order = {"eklenemedi": 1, "eklendi": 2, "güncellendi": 3, "güncel": 4}
    sorted_results = sorted(
        processing_results,
        key=lambda x: status_order.get(str(x.get("status", "")).lower(), 5),
    )

    status_tr_map = {
        "EKLENDI": "EKLENDİ",
        "GÜNCELLENDI": "GÜNCELLENDİ",
        "GÜNCEL": "GÜNCEL",
        "EKLENEMEDI": "EKLENEMEDI",
    }

    for idx, result in enumerate(sorted_results, 1):
        hostname = result.get("hostname", "N/A")
        device_role = result.get("device_role", "N/A")
        location = result.get("location", "N/A")
        site = result.get("site", "N/A")
        tenant = result.get("tenant", "N/A")
        ownership = result.get("ownership", "N/A")
        ip_addr = result.get("ip", "N/A")
        status = str(result.get("status", "N/A")).upper()
        reason = result.get("reason", "-")

        status_tr = status_tr_map.get(status, status)

        writer.writerow(
            [
                idx,
                hostname,
                device_role,
                location,
                site,
                tenant,
                ownership,
                ip_addr,
                status_tr,
                reason,
                timestamp,
            ]
        )

    csv_bytes = csv_buffer.getvalue().encode("utf-8-sig")
    attachment = MIMEApplication(csv_bytes, _subtype="csv")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename="zabbix_entegrasyon_detay.csv",
    )
    print(f"INFO: CSV attachment created with {len(sorted_results)} records")
    return attachment


def build_message(
    subject: str,
    from_addr: str,
    to_addrs: list[str],
    text_content: str,
    html_content: str,
    processing_results,
) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)

    alt = MIMEMultipart("alternative")
    msg.attach(alt)

    part_text = MIMEText(text_content, "plain", "utf-8")
    part_html = MIMEText(html_content, "html", "utf-8")
    alt.attach(part_text)
    alt.attach(part_html)

    csv_attachment = build_csv_attachment(processing_results)
    msg.attach(csv_attachment)

    return msg


def send_mail(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    from_addr: str,
    to_addrs: list[str],
    msg: MIMEMultipart,
) -> None:
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=120)
    server.set_debuglevel(0)

    try:
        if smtp_user and smtp_pass:
            try:
                server.starttls()
            except Exception:
                # STARTTLS not supported, continue without it
                pass
            server.login(smtp_user, smtp_pass)

        server.sendmail(from_addr, to_addrs, msg.as_string())
        print("SUCCESS: Email sent successfully with CSV attachment")
    finally:
        server.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send Zabbix-NetBox integration report email with CSV attachment."
    )
    parser.add_argument("--smtp-host", required=True)
    parser.add_argument("--smtp-port", required=True, type=int)
    parser.add_argument("--smtp-user", nargs="?", default="", const="")
    parser.add_argument("--smtp-pass", nargs="?", default="", const="")
    parser.add_argument("--from-addr", required=True)
    parser.add_argument("--recipients", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--results-file", required=True)
    parser.add_argument("--html-file", required=True)
    parser.add_argument("--text-file", required=True)
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()

        to_addrs = [addr.strip() for addr in args.recipients.split(",") if addr.strip()]
        if not to_addrs:
            print("ERROR: No valid recipients provided")
            return 1

        results = load_json_file(Path(args.results_file))
        html_content = load_text_file(Path(args.html_file))
        text_content = load_text_file(Path(args.text_file))

        msg = build_message(
            subject=args.subject,
            from_addr=args.from_addr,
            to_addrs=to_addrs,
            text_content=text_content,
            html_content=html_content,
            processing_results=results,
        )

        send_mail(
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            smtp_user=args.smtp_user,
            smtp_pass=args.smtp_pass,
            from_addr=args.from_addr,
            to_addrs=to_addrs,
            msg=msg,
        )
        return 0
    except smtplib.SMTPException as exc:
        print(f"SMTP ERROR: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to send email: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

