"""Unit tests for HMDL host group merge helpers."""

import sys
from pathlib import Path

ROLE_LIB = Path(__file__).resolve().parents[1] / "playbooks" / "roles" / "netbox_zabbix_sync" / "library"
sys.path.insert(0, str(ROLE_LIB))

from zabbix_merge_helpers import merge_host_groups  # noqa: E402


def test_merge_host_groups_preserves_manual():
    existing = ["HOST", "DC11", "Manual_Group"]
    required = ["HOST", "DC11", "SWITCH"]
    merged, needs_update = merge_host_groups(existing, required)
    assert "Manual_Group" in merged
    assert "SWITCH" in merged
    assert needs_update is True


def test_merge_host_groups_no_change():
    existing = ["HOST", "Manual_Group"]
    required = ["HOST"]
    merged, needs_update = merge_host_groups(existing, required)
    assert merged == ["HOST", "Manual_Group"]
    assert needs_update is False
