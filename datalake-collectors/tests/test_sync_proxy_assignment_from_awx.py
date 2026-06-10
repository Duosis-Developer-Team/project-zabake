"""Unit tests for AWX proxy assignment sync helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "sync_proxy_assignment_from_awx.py"
)
spec = importlib.util.spec_from_file_location("sync_proxy_assignment_from_awx", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_build_proxy_assignment_dual_nifi():
    assignment = module.build_proxy_assignment(
        {"NiFi_DC16": ["10.60.16.250", "10.60.16.251"]},
        {"NiFi_DC16": "DC16"},
    )
    assert assignment["DC16"]["proxies"][0]["id"] == "DC16-NIFI1"
    assert assignment["DC16"]["proxies"][1]["proxy_nifi_host"] == "10.60.16.251"


def test_compare_assignments_detects_added_proxy():
    current = {
        "DC16": {
            "dc_code": "DC16",
            "proxies": [
                {"id": "DC16-NIFI1", "proxy_nifi_host": "10.60.16.250"},
                {"id": "DC16-NIFI2", "proxy_nifi_host": "10.60.16.251"},
            ],
        }
    }
    updated = {
        "DC16": {
            "dc_code": "DC16",
            "proxies": [
                {"id": "DC16-NIFI1", "proxy_nifi_host": "10.60.16.250"},
                {"id": "DC16-NIFI2", "proxy_nifi_host": "10.60.16.251"},
                {"id": "DC16-NIFI3", "proxy_nifi_host": "10.60.16.252"},
            ],
        }
    }
    diff = module.compare_assignments(current, updated)
    assert diff["added"] == [{"proxy_id": "DC16-NIFI3", "host": "10.60.16.252"}]
    assert diff["removed"] == []


def test_unmapped_awx_group_raises():
    try:
        module.build_proxy_assignment({"NiFi_NEW_SITE": ["10.0.0.1"]}, {})
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "NiFi_NEW_SITE" in str(exc)
