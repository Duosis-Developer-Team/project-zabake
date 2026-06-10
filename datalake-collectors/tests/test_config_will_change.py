"""Tests for config_will_change.py."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/files/config_will_change.py"
)


def run_compare(current: dict, reconciled: dict) -> bool:
    tmp = Path(__file__).parent / "_tmp_config_compare"
    tmp.mkdir(exist_ok=True)
    cur = tmp / "current.json"
    rec = tmp / "reconciled.json"
    cur.write_text(json.dumps(current), encoding="utf-8")
    rec.write_text(json.dumps(reconciled), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--current", str(cur), "--reconciled", str(rec)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["changed"]


def test_unchanged_when_identical():
    cfg = {"Nutanix": {"PRISM_IP": "10.0.0.1"}}
    assert run_compare(cfg, dict(cfg)) is False


def test_changed_when_ip_added():
    current = {"Nutanix": {"PRISM_IP": "10.0.0.1"}}
    reconciled = {"Nutanix": {"PRISM_IP": "10.0.0.1,10.0.0.2"}}
    assert run_compare(current, reconciled) is True


def test_unchanged_when_key_order_differs():
    current = {"B": 1, "A": {"z": 1, "y": 2}}
    reconciled = {"A": {"y": 2, "z": 1}, "B": 1}
    assert run_compare(current, reconciled) is False
