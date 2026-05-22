# Email Notification Guide

Uses the same SMTP variables as zabbix-netbox (ADR-0003):

- `mail_smtp_host`, `mail_smtp_port`, `mail_smtp_username`, `mail_smtp_password`
- `mail_from`, `mail_recipients`

Script: `roles/datalake_collector_sync/files/send_notification_email_smtp.py`

Report includes added/removed IPs and connectivity failures. Set `mail_recipients: []` to disable.
