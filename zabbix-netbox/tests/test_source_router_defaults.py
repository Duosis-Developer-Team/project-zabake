"""Validate inventory source defaults and allowed values."""

import re
from pathlib import Path


DEFAULTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "playbooks"
    / "roles"
    / "netbox_zabbix_sync"
    / "defaults"
    / "main.yml"
)


def test_per_host_type_source_defaults_exist():
    content = DEFAULTS_PATH.read_text(encoding="utf-8")
    assert re.search(r"^device_source:\s*datalake\s*$", content, re.M)
    assert re.search(r"^platform_source:\s*loki\s*$", content, re.M)
    assert re.search(r"^virtual_fw_source:\s*loki\s*$", content, re.M)
    assert "sync_virtual_fws:" in content
    assert "virtual_fw_mapping_path:" in content
