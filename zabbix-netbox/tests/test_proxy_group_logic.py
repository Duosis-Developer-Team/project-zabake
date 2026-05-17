"""Unit tests for proxy group update policy."""

import sys
from pathlib import Path

ROLE_LIB = Path(__file__).resolve().parents[1] / "playbooks" / "roles" / "netbox_zabbix_sync" / "library"
sys.path.insert(0, str(ROLE_LIB))

from zabbix_merge_helpers import resolve_proxy_group_update  # noqa: E402


def test_location_change_forces_update():
    result = resolve_proxy_group_update(
        current_location="DC12",
        last_hmdl_location="DC11",
        expected_proxy_group_id="5",
        zabbix_proxy_group_id="3",
        last_hmdl_proxy_group_id="3",
    )
    assert result["proxy_location_change"] is True
    assert result["apply_update"] is True
    assert result["proxy_manual_change_detected"] is False


def test_manual_proxy_change_preserved():
    result = resolve_proxy_group_update(
        current_location="DC11",
        last_hmdl_location="DC11",
        expected_proxy_group_id="5",
        zabbix_proxy_group_id="9",
        last_hmdl_proxy_group_id="5",
    )
    assert result["proxy_manual_change_detected"] is True
    assert result["apply_update"] is False
    assert "manually" in result["reason"]


def test_sync_catch_up_when_last_log_did_not_match_expected():
    """Automation logged old proxy; recalc expects new — should update Zabbix."""
    result = resolve_proxy_group_update(
        current_location="DC11",
        last_hmdl_location="DC11",
        expected_proxy_group_id="5",
        zabbix_proxy_group_id="3",
        last_hmdl_proxy_group_id="3",
    )
    assert result["apply_update"] is True
    assert result["proxy_manual_change_detected"] is False
