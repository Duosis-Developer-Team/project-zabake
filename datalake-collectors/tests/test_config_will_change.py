"""Tests for config_will_change.py."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/files/config_will_change.py"
)


def run_compare(current: dict, reconciled: dict, tmp_path: Path) -> bool:
    cur = tmp_path / "current.json"
    rec = tmp_path / "reconciled.json"
    cur.write_text(json.dumps(current), encoding="utf-8")
    rec.write_text(json.dumps(reconciled), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--current", str(cur), "--reconciled", str(rec)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)["changed"]


def test_unchanged_when_identical(tmp_path):
    cfg = {"Nutanix": {"PRISM_IP": "10.0.0.1"}}
    assert run_compare(cfg, dict(cfg), tmp_path) is False


def test_changed_when_ip_added(tmp_path):
    current = {"Nutanix": {"PRISM_IP": "10.0.0.1"}}
    reconciled = {"Nutanix": {"PRISM_IP": "10.0.0.1,10.0.0.2"}}
    assert run_compare(current, reconciled, tmp_path) is True


def test_unchanged_when_key_order_differs(tmp_path):
    current = {"B": 1, "A": {"z": 1, "y": 2}}
    reconciled = {"A": {"y": 2, "z": 1}, "B": 1}
    assert run_compare(current, reconciled, tmp_path) is False
