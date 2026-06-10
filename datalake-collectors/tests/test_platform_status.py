"""Unit tests for platform status classification and fetch."""

import sys
from pathlib import Path

ROLE_UTILS = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/module_utils"
)
ROLE_FILES = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/files"
)
sys.path.insert(0, str(ROLE_UTILS))
sys.path.insert(0, str(ROLE_FILES))

from collector_core import (  # noqa: E402
    append_platform_status_to_reason,
    build_ip_platform_status_map,
    classify_platform_status,
    is_platform_not_monitored,
    match_customer_environment,
    match_platform_mapping,
    reconcile_section_ips,
)
from fetch_netbox_inventory import dedupe_by_id  # noqa: E402


def test_is_platform_not_monitored():
    assert is_platform_not_monitored({"izlenmeli": "Hayır"}) is True
    assert is_platform_not_monitored({"izlenmeli": "Evet"}) is False
    assert is_platform_not_monitored({}) is False
    assert is_platform_not_monitored({"monitor_edilmeli_mi": "false"}) is True


def test_match_customer_environment_moneygram():
    platform = {
        "name": "Moneygram-VMware-DC13",
        "manufacturer": {"name": "VMware"},
        "custom_fields": {"Site": "DC13-G12"},
    }
    rows = [
        {
            "manufacturer": "VMware",
            "name_contains": "moneygram",
            "site_contains": "moneygram",
            "match_logic": "or",
            "customer_environment": True,
            "priority": 1,
        }
    ]
    assert match_customer_environment(platform, rows) is True


def test_classify_platform_status_combined():
    platform = {
        "name": "Moneygram-VMware",
        "manufacturer": {"name": "VMware"},
        "custom_fields": {"izlenmeli": "Hayır", "Site": "DC13"},
    }
    rows = [
        {
            "manufacturer": "VMware",
            "name_contains": "moneygram",
            "customer_environment": True,
            "priority": 1,
        }
    ]
    status, note = classify_platform_status(platform, rows)
    assert status == "not_monitored; customer_environment"
    assert note == status


def test_classify_platform_status_monitored_default():
    platform = {
        "name": "Equinix-Nutanix",
        "manufacturer": {"name": "Nutanix"},
        "custom_fields": {"izlenmeli": "Evet", "Site": "DC13"},
    }
    status, _ = classify_platform_status(platform, [])
    assert status == "monitored"


def test_match_platform_mapping_match_logic_or():
    mappings = [
        {
            "manufacturer": "VMware",
            "collector_type": "VmWare",
            "name_contains": "moneygram",
            "site_contains": "moneygram",
            "match_logic": "or",
            "priority": 1,
        },
        {"manufacturer": "VMware", "collector_type": "VmWare", "priority": 999},
    ]
    row = match_platform_mapping("VMware", "prod-cluster", "moneygram-dc13", mappings)
    assert row["priority"] == 1


def test_reconcile_section_appends_platform_status_reason():
    current = {"VMwareIP": "10.0.0.1", "VMwarePort": "443"}
    _, diffs = reconcile_section_ips(
        current,
        ["10.0.0.1", "10.0.0.2"],
        "VMwareIP",
        "comma_string",
        ip_status_map={"10.0.0.2": "not_monitored"},
    )
    added = [d for d in diffs if d["action"] == "added"][0]
    preserved = [d for d in diffs if d["action"] == "preserved"][0]
    assert "[platform_status: not_monitored]" in added["reason"]
    assert preserved["reason"] == "unchanged"


def test_build_ip_platform_status_map_merges():
    targets = [
        {"ip": "10.0.0.1", "platform_status": "not_monitored"},
        {"ip": "10.0.0.1", "platform_status": "customer_environment"},
    ]
    assert build_ip_platform_status_map(targets)["10.0.0.1"] == "not_monitored; customer_environment"


def test_append_platform_status_to_reason_skips_monitored():
    assert append_platform_status_to_reason("unchanged", "10.0.0.1", {"10.0.0.1": "monitored"}) == "unchanged"


def test_dedupe_by_id():
    items = [{"id": 1, "name": "a"}, {"id": 1, "name": "b"}, {"id": 2, "name": "c"}]
    out = dedupe_by_id(items)
    assert len(out) == 2
    assert out[0]["name"] == "a"
