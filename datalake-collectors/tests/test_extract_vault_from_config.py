"""Unit tests for extract_vault_from_config.py."""

import json
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_vault_from_config import extract_vault_section, excluded_fields  # noqa: E402


def test_excluded_fields_includes_ip_and_secondary():
    meta = {
        "ip_field": "VMwareIP",
        "secondary_fields": {"link": "https://{ip}:7443"},
    }
    assert excluded_fields(meta) == {"VMwareIP", "link"}


def test_extract_vault_section_manual_only_keeps_all():
    section = {"zabUrl": "https://zabbix.example.com", "zabPassword": "secret"}
    meta = {"source_type": "manual_only"}
    assert extract_vault_section(section, meta) == section


def test_extract_vault_section_strips_ip_field():
    section = {"VMwareIP": "10.0.0.1", "VMware_password": "secret", "VMwarePort": "443"}
    meta = {"source_type": "platform", "ip_field": "VMwareIP"}
    out = extract_vault_section(section, meta)
    assert "VMwareIP" not in out
    assert out["VMware_password"] == "secret"
