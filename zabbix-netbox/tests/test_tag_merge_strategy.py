"""Unit tests for HMDL tag merge helpers."""

import sys
from pathlib import Path

import pytest

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
