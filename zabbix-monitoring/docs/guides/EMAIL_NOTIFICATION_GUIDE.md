# Email Notification Guide

## Overview

The `zabbix_tag_based_monitoring.yaml` playbook sends an email notification after the connectivity analysis completes. The email includes an HTML report, a plain-text fallback, and a **CSV attachment** (`zabbix_connectivity_raporu.csv`) with the full per-item breakdown.

Email sending is handled by a dedicated Python script (`roles/zabbix_monitoring/files/send_notification_email_smtp.py`) that receives file paths as arguments — not inline content. This prevents `ARG_MAX` and special-character issues that occur when large HTML bodies are interpolated into shell scripts.

## SMTP Configuration

Default SMTP settings (configured in `defaults/main.yml`):

| Variable | Default | Description |
|---|---|---|
| `mail_smtp_host` | `10.34.8.191` | SMTP server address |
| `mail_smtp_port` | `587` | SMTP port |
| `mail_from` | `infrareport@alert.bulutistan.com` | Sender address |
| `mail_smtp_username` | `""` | SMTP username (empty = no auth) |
| `mail_smtp_password` | `""` | SMTP password (use AWX Credentials) |
| `mail_recipients` | `[]` | Recipient list — must be provided as input |

## Usage

### Basic Usage (with email notification)

```bash
ansible-playbook playbooks/zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e '{"mail_recipients": ["user1@example.com", "user2@example.com"]}'
```

### Single recipient

```bash
ansible-playbook playbooks/zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e '{"mail_recipients": ["admin@bulutistan.com"]}'
```

### Run without email

Omit `mail_recipients` or pass an empty list:

```bash
ansible-playbook playbooks/zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Override SMTP settings

```bash
ansible-playbook playbooks/zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e '{"mail_recipients": ["user@example.com"]}' \
  -e "mail_smtp_host=10.34.8.191" \
  -e "mail_smtp_port=587" \
  -e "mail_from=infrareport@alert.bulutistan.com"
```

## Email Content

The notification includes:

### Summary section
- Total hosts analyzed
- Hosts with issues / without issues
- Hosts without connection items
- Total items analyzed / items below threshold
- Threshold percentage
- Analysis timestamp

### Problematic connection items (if any)
HTML table with columns: Host Name, Item Name, Connectivity Score (%), Item Status, Host Status.

### Hosts without connection items (if any)
Hosts that have no items tagged with `connection status`.

### CSV attachment — `zabbix_connectivity_raporu.csv`
Full per-item breakdown sorted by severity:

| Column | Description |
|---|---|
| Sıra No | Row number |
| Host Adı | Zabbix hostname |
| İtem Adı | Item name |
| Bağlantı Skoru (%) | Connectivity percentage (N/A for no-data items) |
| İtem Durumu | KRİTİK / UYARI / VERİ YOK / BAĞLANTI İTEMİ YOK |
| Host Durumu | TAMAMEN KRİTİK / KISMİ SORUN / TAMAM |
| Zaman Damgası | Report generation time |

## Email sending conditions

Email is sent when **all** of the following are true:
1. `mail_recipients` is defined and non-empty (list)
2. `connectivity_analysis` data was successfully produced by the check

## AWX Usage

In AWX Job Template extra variables:

```yaml
mail_recipients:
  - "admin@example.com"
  - "team@example.com"
```

SMTP settings use `defaults/main.yml` values unless overridden in extra vars.

## Architecture

```
set_fact (HTML, text, subject)
         │
         ▼
/tmp/zabbix_monitoring/
   ├── analysis_results.json
   ├── email_body.html
   └── email_body.txt
         │
         ▼
python3 files/send_notification_email_smtp.py
   --html-file ... --text-file ... --results-file ...
         │
         ▼
SMTP → HTML + plain text + zabbix_connectivity_raporu.csv
```

The temporary directory path is configurable via `zabbix_monitoring_tmp_dir` (default: `/tmp/zabbix_monitoring`).

## Related Documents

- [Usage Guide](USAGE.md)
- [AWX Testing Guide](AWX_TESTING.md)
- [Architecture](../design/ARCHITECTURE.md)
