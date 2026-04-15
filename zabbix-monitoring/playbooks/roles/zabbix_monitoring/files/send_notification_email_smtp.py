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


def _host_metadata_columns(row: dict) -> list:
    """Report columns from analysis JSON (location, contact, tenant, interface_ip, proxy_group_name, host_templates)."""
    return [
        row.get("location", "") or "",
        row.get("contact", "") or "",
        row.get("tenant", "") or "",
        row.get("interface_ip", "") or "",
        row.get("proxy_group_name", "") or "",
        row.get("host_templates", "") or "",
    ]


def build_csv_attachment(analysis_results: dict) -> MIMEApplication:
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)

    writer.writerow(
        [
            "Sıra No",
            "Host Adı",
            "Location",
            "Contact",
            "Tenant",
            "Arayüz IP",
            "Proxy Grubu",
            "Host Templates",
            "İtem Adı",
            "Bağlantı Skoru (%)",
            "İtem Durumu",
            "Host Durumu",
            "Zaman Damgası",
        ]
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_idx = 1

    status_order = {"critical": 1, "warning": 2, "no_data": 3, "healthy": 4}
    problematic_items = analysis_results.get("problematic_items", [])
    sorted_items = sorted(
        problematic_items,
        key=lambda x: status_order.get(str(x.get("status", "")).lower(), 5),
    )

    item_status_tr_map = {
        "critical": "KRİTİK",
        "warning": "UYARI",
        "healthy": "SAĞLIKLI",
        "no_data": "VERİ YOK",
    }
    host_status_tr_map = {
        "all_critical": "TAMAMEN KRİTİK",
        "partial": "KISMİ SORUN",
        "all_ok": "TAMAM",
    }

    for item in sorted_items:
        host_name = item.get("host_name") or item.get("hostname", "N/A")
        item_name = item.get("item_name", "N/A")
        percentage = item.get("percentage", "N/A")
        status = str(item.get("status", "N/A")).lower()
        host_status = str(item.get("host_status", "N/A")).lower()

        score_display = "N/A" if status == "no_data" else f"{percentage}%"
        status_tr = item_status_tr_map.get(status, status.upper())
        host_status_tr = host_status_tr_map.get(host_status, host_status.upper())

        meta = _host_metadata_columns(item)
        writer.writerow(
            [
                row_idx,
                host_name,
                *meta,
                item_name,
                score_display,
                status_tr,
                host_status_tr,
                timestamp,
            ]
        )
        row_idx += 1

    hosts_without_items = analysis_results.get("hosts_without_connection_items", [])
    for host in hosts_without_items:
        host_name = host.get("host_name") or host.get("hostname", "N/A")
        meta = _host_metadata_columns(host)
        writer.writerow(
            [
                row_idx,
                host_name,
                *meta,
                "—",
                "N/A",
                "BAĞLANTI İTEMİ YOK",
                "BİLİNMİYOR",
                timestamp,
            ]
        )
        row_idx += 1

    csv_bytes = csv_buffer.getvalue().encode("utf-8-sig")
    attachment = MIMEApplication(csv_bytes, _subtype="csv")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename="zabbix_connectivity_raporu.csv",
    )
    total_rows = row_idx - 1
    print(f"INFO: CSV attachment created with {total_rows} records")
    return attachment


def build_message(
    subject: str,
    from_addr: str,
    to_addrs: list[str],
    text_content: str,
    html_content: str,
    analysis_results: dict,
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

    csv_attachment = build_csv_attachment(analysis_results)
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
        description="Send Zabbix connectivity monitoring report email with CSV attachment."
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

        analysis_results = load_json_file(Path(args.results_file))
        html_content = load_text_file(Path(args.html_file))
        text_content = load_text_file(Path(args.text_file))

        msg = build_message(
            subject=args.subject,
            from_addr=args.from_addr,
            to_addrs=to_addrs,
            text_content=text_content,
            html_content=html_content,
            analysis_results=analysis_results,
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
