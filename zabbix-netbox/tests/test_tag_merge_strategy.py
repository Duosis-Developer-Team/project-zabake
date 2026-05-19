"""Unit tests for HMDL tag merge helpers."""

import sys
from pathlib import Path

import pytest
import yaml

ROLE_LIB = Path(__file__).resolve().parents[1] / "playbooks" / "roles" / "netbox_zabbix_sync" / "library"
sys.path.insert(0, str(ROLE_LIB))

from zabbix_merge_helpers import (  # noqa: E402
    is_managed_tag,
    load_managed_tag_keys,
    merge_tags,
)


@pytest.fixture
def sample_tags_config():
    return {
        "tags": {
            "definitions": [
                {"tag_name": "Manufacturer", "enabled": True},
                {"tag_name": "Loki_ID", "enabled": True},
                {"tag_name": "Disabled_Tag", "enabled": False},
            ]
        }
    }


def test_load_managed_tag_keys(sample_tags_config):
    keys = load_managed_tag_keys(sample_tags_config)
    assert "Manufacturer" in keys
    assert "Loki_ID" in keys
    assert "Disabled_Tag" not in keys


def test_is_managed_tag_loki_prefix():
    assert is_managed_tag("Loki_Tag_foo", [])
    assert not is_managed_tag("Custom_Manual", ["Manufacturer"])


def test_merge_tags_preserves_manual():
    existing = [
        {"tag": "Manufacturer", "value": "OLD"},
        {"tag": "Manual_Tag", "value": "keep-me"},
    ]
    new_managed = [
        {"tag": "Manufacturer", "value": "CISCO"},
        {"tag": "Loki_ID", "value": "123"},
    ]
    merged, log = merge_tags(existing, new_managed, ["Manufacturer", "Loki_ID"])
    tags = {t["tag"]: t["value"] for t in merged}
    assert tags["Manufacturer"] == "CISCO"
    assert tags["Loki_ID"] == "123"
    assert tags["Manual_Tag"] == "keep-me"
    assert any(e["action"] == "updated" for e in log if e["key_name"] == "Manufacturer")


PLATFORM_MANAGED_KEYS = [
    "IP",
    "Port",
    "URL",
    "Site",
    "DC",
    "Manufacturer",
    "Created",
    "Last_Updated",
    "Loki_Platform_ID",
    "Loki_ID",
]


def test_platform_managed_keys_include_ip():
    config_path = Path(__file__).resolve().parents[1] / "mappings" / "platform_tags_config.yml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    keys = data["platform_tags"]["managed_keys"]
    assert "IP" in keys
    assert keys == PLATFORM_MANAGED_KEYS


def test_merge_tags_platform_ip_no_duplicate():
    """Regression: host.update must not send duplicate (IP, value) pairs (Zabbix -32602)."""
    existing = [
        {"tag": "IP", "value": "10.0.0.1"},
        {"tag": "Site", "value": "DC14-G1"},
        {"tag": "Custom", "value": "manual"},
    ]
    new_managed = [
        {"tag": "IP", "value": "10.0.0.1"},
        {"tag": "Site", "value": "DC14-G1"},
        {"tag": "Port", "value": "9440"},
        {"tag": "Loki_ID", "value": "P_103"},
    ]
    merged, log = merge_tags(existing, new_managed, PLATFORM_MANAGED_KEYS)
    ip_entries = [t for t in merged if t["tag"] == "IP"]
    assert len(ip_entries) == 1
    assert ip_entries[0]["value"] == "10.0.0.1"
    assert {t["tag"] for t in merged} == {"IP", "Site", "Port", "Loki_ID", "Custom"}
    assert not any(e["action"] in ("added", "updated") for e in log if e["key_name"] == "IP")


def test_merge_tags_platform_ip_value_change():
    existing = [{"tag": "IP", "value": "10.0.0.1"}]
    new_managed = [{"tag": "IP", "value": "10.0.0.2"}]
    merged, log = merge_tags(existing, new_managed, PLATFORM_MANAGED_KEYS)
    assert len([t for t in merged if t["tag"] == "IP"]) == 1
    assert merged[0]["value"] == "10.0.0.2"
    assert any(
        e["key_name"] == "IP" and e["action"] == "updated" for e in log
    )


def test_merge_tags_tags_needs_update_false_when_unchanged():
    existing = [
        {"tag": "IP", "value": "10.50.2.45"},
        {"tag": "Loki_ID", "value": "P_103"},
    ]
    new_managed = [
        {"tag": "IP", "value": "10.50.2.45"},
        {"tag": "Loki_ID", "value": "P_103"},
    ]
    _, log = merge_tags(existing, new_managed, PLATFORM_MANAGED_KEYS)
    needs_update = any(e.get("action") in ("added", "updated") for e in log)
    assert needs_update is False
