"""Unit tests for collector_core reconcile logic."""

import json
import sys
from pathlib import Path

import pytest

ROLE_UTILS = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/module_utils"
)
sys.path.insert(0, str(ROLE_UTILS))

from collector_core import (  # noqa: E402
    format_ip_list,
    match_platform_mapping,
    normalize_proxy_assignment,
    parse_ip_list,
    reconcile_proxy_config,
    reconcile_section_ips,
    resolve_proxy_ids,
)


def test_parse_ip_list_comma_string():
    assert parse_ip_list("10.1.1.1, 10.1.1.2") == ["10.1.1.1", "10.1.1.2"]


def test_format_ip_list_comma():
    assert format_ip_list(["10.1.1.1", "10.1.1.2"], "comma_string") == "10.1.1.1,10.1.1.2"


def test_format_ip_list_single():
    assert format_ip_list(["10.1.1.1", "10.1.1.2"], "single_string") == "10.1.1.1"


def test_match_platform_mapping_priority():
    mappings = [
        {"manufacturer": "VMware", "collector_type": "VmWare", "priority": 999},
        {"manufacturer": "Nutanix", "collector_type": "Nutanix", "priority": 1},
    ]
    row = match_platform_mapping("Nutanix", "cluster-1", "DC13", mappings)
    assert row["collector_type"] == "Nutanix"


def test_reconcile_section_add_remove():
    current = {"VMwareIP": "10.0.0.1,10.0.0.2", "VMwarePort": "443"}
    updated, diffs = reconcile_section_ips(
        current,
        ["10.0.0.2", "10.0.0.3"],
        "VMwareIP",
        "comma_string",
    )
    assert "10.0.0.3" in updated["VMwareIP"]
    assert "10.0.0.1" not in updated["VMwareIP"]
    assert updated["VMwarePort"] == "443"
    actions = {d["action"] for d in diffs}
    assert "added" in actions
    assert "removed" in actions


def test_reconcile_hmc_multi_host_comma_string():
    collector_types = {
        "IBM-HMC": {
            "conf_key": "IBM-HMC",
            "ip_field": "hmc_hostname",
            "ip_format": "comma_string",
            "source_type": "platform",
        },
    }
    current = {"IBM-HMC": {"hmc_hostname": "10.34.2.110", "hmc_user": "zabbix"}}
    desired = {
        "IBM-HMC": {
            "hmc_hostname": "10.34.2.110,10.34.10.110",
            "hmc_user": "zabbix",
        },
    }
    reconciled, diffs = reconcile_proxy_config(current, desired, collector_types)
    assert "10.34.2.110" in reconciled["IBM-HMC"]["hmc_hostname"]
    assert "10.34.10.110" in reconciled["IBM-HMC"]["hmc_hostname"]
    actions = {d["action"] for d in diffs}
    assert "added" in actions


def test_reconcile_proxy_preserves_manual_only():
    collector_types = {
        "VmWare": {
            "conf_key": "VmWare",
            "ip_field": "VMwareIP",
            "ip_format": "comma_string",
            "source_type": "platform",
        },
        "Zabbix": {
            "conf_key": "Zabbix",
            "source_type": "manual_only",
        },
    }
    current = {
        "VmWare": {"VMwareIP": "10.0.0.1", "VMwarePort": "443"},
        "Zabbix": {"zabUrl": "https://zabbix.example.com/api_jsonrpc.php"},
        "Loki": {"address": "https://loki.example.com"},
    }
    desired = {
        "VmWare": {"VMwareIP": "10.0.0.1,10.0.0.2", "VMwarePort": "443"},
    }
    result, diffs = reconcile_proxy_config(current, desired, collector_types)
    assert result["Zabbix"]["zabUrl"] == current["Zabbix"]["zabUrl"]
    assert result["Loki"] == current["Loki"]
    assert "10.0.0.2" in result["VmWare"]["VMwareIP"]


def test_reconcile_section_removal_blocked_when_reachable():
    current = {"VMwareIP": "10.0.0.1,10.0.0.2", "VMwarePort": "443"}
    updated, diffs = reconcile_section_ips(
        current,
        ["10.0.0.2"],
        "VMwareIP",
        "comma_string",
        connectivity_map={"10.0.0.1": "ok"},
    )
    assert "10.0.0.1" in updated["VMwareIP"]
    assert "10.0.0.2" in updated["VMwareIP"]
    actions = {d["action"] for d in diffs}
    assert "removal_blocked" in actions
    assert "removed" not in actions


def test_reconcile_section_removes_when_unreachable():
    current = {"VMwareIP": "10.0.0.1,10.0.0.2", "VMwarePort": "443"}
    updated, diffs = reconcile_section_ips(
        current,
        ["10.0.0.2"],
        "VMwareIP",
        "comma_string",
        connectivity_map={"10.0.0.1": "icmp_fail"},
    )
    assert "10.0.0.1" not in updated["VMwareIP"]
    actions = {d["action"] for d in diffs}
    assert "removed" in actions


def test_normalize_proxy_assignment_multi_nifi():
    assignment = {
        "DC16": {
            "dc_code": "DC16",
            "proxies": [
                {"id": "DC16-NIFI1", "proxy_nifi_host": "dc16-nifi-1"},
                {"id": "DC16-NIFI2", "proxy_nifi_host": "dc16-nifi-2"},
            ],
        }
    }
    dc_map, lookup = normalize_proxy_assignment(assignment)
    assert dc_map["DC16"] == ["DC16-NIFI1", "DC16-NIFI2"]
    assert lookup["DC16-NIFI2"]["proxy_nifi_host"] == "dc16-nifi-2"


def test_resolve_proxy_ids_fan_out():
    assignment = {
        "DC16": {
            "dc_code": "DC16",
            "proxies": [
                {"id": "DC16-NIFI1", "proxy_nifi_host": "a"},
                {"id": "DC16-NIFI2", "proxy_nifi_host": "b"},
            ],
        }
    }
    assert resolve_proxy_ids("DC16", assignment) == ["DC16-NIFI1", "DC16-NIFI2"]


def test_legacy_proxy_assignment_still_works():
    assignment = {
        "DC13": {
            "proxy_nifi_host": "dc13-nifi-1",
            "ssh_user": "root",
        }
    }
    dc_map, lookup = normalize_proxy_assignment(assignment)
    assert "DC13" in dc_map
    assert lookup["DC13"]["proxy_nifi_host"] == "dc13-nifi-1"
