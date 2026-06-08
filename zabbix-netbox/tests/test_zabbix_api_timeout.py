"""Regression: Zabbix API uri calls use configurable 5-minute default timeout."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS_PATH = (
    REPO_ROOT
    / "playbooks"
    / "roles"
    / "netbox_zabbix_sync"
    / "defaults"
    / "main.yml"
)
PLAYBOOK_PATH = REPO_ROOT / "playbooks" / "netbox_zabbix_sync.yaml"


def test_zabbix_api_timeout_default_in_role_defaults():
    content = DEFAULTS_PATH.read_text(encoding="utf-8")
    assert re.search(r"^zabbix_api_timeout:\s*300\s", content, re.M), (
        "defaults/main.yml must define zabbix_api_timeout: 300"
    )


def test_playbook_applies_uri_module_defaults_for_zabbix_timeout():
    content = PLAYBOOK_PATH.read_text(encoding="utf-8")
    assert "module_defaults:" in content
    assert "ansible.builtin.uri:" in content
    assert "zabbix_api_timeout" in content
    assert "default(300)" in content
