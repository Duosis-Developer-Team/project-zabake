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
