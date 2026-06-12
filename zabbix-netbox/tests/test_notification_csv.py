"""CSV attachment columns for integration report email."""
import csv
import importlib.util
import io
from pathlib import Path

_ROLE_FILES = Path(__file__).resolve().parent.parent / (
    "playbooks/roles/netbox_zabbix_sync/files/send_notification_email_smtp.py"
)


def _load_smtp_module():
    spec = importlib.util.spec_from_file_location("send_notification_email_smtp", _ROLE_FILES)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_build_csv_attachment_includes_location_tenant_ownership_columns():
    mod = _load_smtp_module()
    rows = [
        {
            "hostname": "host1",
            "device_role": "Switch",
            "location": "DC1-A",
            "site": "SiteX",
            "tenant": "T1",
            "ownership": "TeamA",
            "ip": "10.0.0.1",
            "status": "eklendi",
            "reason": "",
        }
    ]
    attachment = mod.build_csv_attachment(rows)
    assert attachment.get_content_subtype() == "csv"
    raw = attachment.get_payload(decode=True)
    assert raw is not None
    text = raw.decode("utf-8-sig")
    first_line = text.splitlines()[0]
    assert "Lokasyon" in first_line
    assert "Site" in first_line
    assert "Tenant" in first_line
    assert "Sahiplik" in first_line
    assert "Device Role" in first_line


def test_build_csv_attachment_defaults_missing_report_fields_to_na():
    mod = _load_smtp_module()
    rows = [{"hostname": "h", "device_role": "R", "ip": "1.1.1.1", "status": "güncel", "reason": "-"}]
    attachment = mod.build_csv_attachment(rows)
    raw = attachment.get_payload(decode=True)
    assert raw is not None
    lines = raw.decode("utf-8-sig").splitlines()
    reader = csv.reader(io.StringIO(lines[1]))
    data_cols = next(reader)
    # Columns: idx, hostname, role, location, site, tenant, ownership, ip, ...
    assert data_cols[3] == "N/A"
    assert data_cols[4] == "N/A"
    assert data_cols[5] == "N/A"
    assert data_cols[6] == "N/A"


def test_build_csv_attachment_network_discovery_skip_shows_atlandi():
    mod = _load_smtp_module()
    rows = [
        {
            "hostname": "G2HV28DC13",
            "device_role": "HOST",
            "location": "DC13",
            "site": "ISTANBUL",
            "tenant": "N/A",
            "ownership": "N/A",
            "ip": "10.132.1.120",
            "status": "atlandı",
            "reason": "Network Discovery, no action taken",
        }
    ]
    attachment = mod.build_csv_attachment(rows)
    raw = attachment.get_payload(decode=True)
    assert raw is not None
    text = raw.decode("utf-8-sig")
    assert "ATLANDI" in text
    assert "Network Discovery, no action taken" in text


def test_build_csv_attachment_includes_update_reasons_and_error_detail_columns():
    mod = _load_smtp_module()
    rows = [
        {
            "hostname": "G2HV28DC13",
            "device_role": "HOST",
            "location": "DC13",
            "site": "ISTANBUL",
            "tenant": "N/A",
            "ownership": "N/A",
            "ip": "10.132.1.120",
            "status": "eklenemedi",
            "reason": 'Cannot update "host" for a discovered host "G2HV28DC13".',
            "update_reasons": ["ip_changed:10.134.16.13->10.132.1.120", "interface_changed"],
            "error_data": 'Cannot update "host" for a discovered host "G2HV28DC13".',
        }
    ]
    attachment = mod.build_csv_attachment(rows)
    raw = attachment.get_payload(decode=True)
    assert raw is not None
    text = raw.decode("utf-8-sig")
    first_line = text.splitlines()[0]
    assert "Update Reasons" in first_line
    assert "Error Detail" in first_line
    assert "discovered host" in text
    assert "ip_changed" in text


def test_build_csv_attachment_dry_run_create_and_update_labels():
    mod = _load_smtp_module()
    rows = [
        {
            "hostname": "new-host",
            "device_role": "HOST",
            "location": "DC14",
            "site": "DC14",
            "tenant": "CPE-Tenant",
            "ownership": "Team",
            "ip": "10.0.0.2",
            "status": "dry_run",
            "planned_operation": "create",
            "reason": "Dry-run: host.create çağrısı yapılmadı — eklenecekti",
        },
        {
            "hostname": "upd-host",
            "device_role": "HOST",
            "location": "DC14",
            "site": "DC14",
            "tenant": "CPE-Tenant",
            "ownership": "Team",
            "ip": "10.0.0.3",
            "status": "dry_run",
            "planned_operation": "update",
            "reason": "Dry-run: host.update çağrısı yapılmadı — güncellenecekti",
        },
    ]
    attachment = mod.build_csv_attachment(rows)
    raw = attachment.get_payload(decode=True)
    assert raw is not None
    text = raw.decode("utf-8-sig")
    assert "DRY-RUN — CREATE (host.create)" in text
    assert "DRY-RUN — UPDATE (host.update)" in text
    assert "eklenecekti" in text
    assert "güncellenecekti" in text
