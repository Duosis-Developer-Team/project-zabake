"""Tests for hostname sanitization in netbox_device_normalize."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "playbooks" / "roles" / "netbox_zabbix_sync" / "files"))

from netbox_device_normalize import sanitize_hostname


def test_sanitize_hostname_replaces_tab_with_space():
    assert sanitize_hostname("Kale Kilit \tFortiGate 100F Master") == "Kale Kilit FortiGate 100F Master"


def test_sanitize_hostname_collapses_multiple_spaces():
    assert sanitize_hostname("host  with   spaces") == "host with spaces"


def test_sanitize_hostname_strips_edges():
    assert sanitize_hostname("  trimmed  ") == "trimmed"


def test_sanitize_hostname_empty():
    assert sanitize_hostname("") == ""
