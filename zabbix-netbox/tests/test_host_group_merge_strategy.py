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


def test_platform_merge_drops_wrong_manual_groups():
    """PLATFORM sync: preserve_manual=False — only managed set, no Veeam leftovers."""
    existing = ["Nutanix", "Nutanix Cluster", "Virtual Infrastructure"]
    required = ["Virtual Infrastructure", "Acropolis"]
    merged, needs_update = merge_host_groups(
        existing, required, preserve_manual=False
    )
    assert merged == ["Virtual Infrastructure", "Acropolis"]
    assert "Nutanix" not in merged
    assert "Nutanix Cluster" not in merged
    assert needs_update is True


def test_platform_merge_no_change_when_correct():
    existing = ["Virtual Infrastructure", "VMware"]
    required = ["Virtual Infrastructure", "VMware"]
    merged, needs_update = merge_host_groups(
        existing, required, preserve_manual=False
    )
    assert merged == ["Virtual Infrastructure", "VMware"]
    assert needs_update is False


def test_required_includes_template_groups_not_subtracted():
    """Managed set is full required list (template host_groups stay in required)."""
    existing = ["Backup & Replication", "Veeam"]
    required = ["Virtual Infrastructure", "VMware"]
    merged, needs_update = merge_host_groups(
        existing, required, preserve_manual=False
    )
    assert merged == ["Virtual Infrastructure", "VMware"]
    assert "Veeam" not in merged
    assert needs_update is True


def test_device_merge_still_preserves_manual():
    existing = ["HOST", "Legacy_Custom"]
    required = ["HOST", "SWITCH"]
    merged, needs_update = merge_host_groups(existing, required, preserve_manual=True)
    assert "Legacy_Custom" in merged
    assert merged == ["HOST", "SWITCH", "Legacy_Custom"]
