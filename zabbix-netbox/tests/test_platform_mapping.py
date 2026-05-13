#!/usr/bin/env python3
"""
Unit tests for platform manufacturer mapping (name/site conditions, priority).
Logic mirrors process_platform.yml — keep in sync when changing matching rules.
"""

import re
import unittest


def find_platform_mapping(
    platform_name: str,
    platform_site_code: str,
    manufacturer_name: str,
    platform_mapping: dict,
):
    """
    Return the first matching mapping dict for a platform, or None.
    Same rules as Ansible task "Find mapping for platform manufacturer".
    """
    mappings = platform_mapping.get("mappings", [])
    escaped = re.escape(manufacturer_name or "")
    pat = re.compile(rf"^{escaped}$", re.IGNORECASE)

    def manufacturer_matches(m: dict) -> bool:
        mfg = m.get("manufacturer")
        if mfg is None:
            return False
        return pat.match(str(mfg).strip()) is not None

    candidates = [m for m in mappings if manufacturer_matches(m)]
    candidates.sort(key=lambda x: int(x.get("priority", 999)))

    name_l = (platform_name or "").lower()
    site_l = (platform_site_code or "").lower()

    for m in candidates:
        nc = str(m.get("name_contains") or "").lower()
        sc = str(m.get("site_contains") or "").lower()
        name_match = (nc == "") or (nc in name_l)
        site_match = (sc == "") or (sc in site_l)
        logic = str(m.get("match_logic") or "and").lower()
        if logic == "or":
            passes = name_match or site_match
        else:
            passes = name_match and site_match
        if passes:
            return m
    return None


def extract_dc_code_for_proxy(site_or_location: str) -> str:
    """
    First (DC|AZ|ICT|UZ)[0-9]+ match, uppercased — aligned with zabbix_host_operations.yml.
    """
    if not site_or_location:
        return ""
    m = re.search(r"(DC|AZ|ICT|UZ)[0-9]+", site_or_location, re.IGNORECASE)
    return m.group(0).upper() if m else ""


def load_sample_platform_mapping() -> dict:
    """Minimal mapping fixture mirroring netbox_platform_mapping.yml VMware rows."""
    return {
        "mappings": [
            {
                "manufacturer": "VMware",
                "device_type": "VMware Moneygram",
                "name_contains": "moneygram",
                "site_contains": "moneygram",
                "match_logic": "or",
                "priority": 1,
                "limit_per_dc": 0,
            },
            {
                "manufacturer": "VMware",
                "device_type": "VMware",
                "priority": 999,
                "limit_per_dc": 0,
            },
        ]
    }


class TestPlatformMoneygramMapping(unittest.TestCase):
    def setUp(self):
        self.mapping = load_sample_platform_mapping()

    def test_moneygram_by_name_only(self):
        m = find_platform_mapping(
            "MoneyGramDr-CLS",
            "SomeOtherSite-DC99",
            "Vmware",
            self.mapping,
        )
        self.assertIsNotNone(m)
        self.assertEqual(m["device_type"], "VMware Moneygram")

    def test_moneygram_by_site_only(self):
        m = find_platform_mapping(
            "GenericVcenter",
            "Moneygramdr-DC16",
            "VMware",
            self.mapping,
        )
        self.assertIsNotNone(m)
        self.assertEqual(m["device_type"], "VMware Moneygram")

    def test_generic_vmware_when_no_moneygram(self):
        m = find_platform_mapping(
            "GenericPlatform",
            "DC13",
            "VMware",
            self.mapping,
        )
        self.assertIsNotNone(m)
        self.assertEqual(m["device_type"], "VMware")

    def test_priority_sort_not_yaml_file_order(self):
        """Lower priority number is evaluated first even if generic row appears first in the list."""
        generic_first = {
            "mappings": [
                {
                    "manufacturer": "VMware",
                    "device_type": "VMware",
                    "priority": 999,
                    "limit_per_dc": 0,
                },
                {
                    "manufacturer": "VMware",
                    "device_type": "VMware Moneygram",
                    "name_contains": "moneygram",
                    "site_contains": "moneygram",
                    "match_logic": "or",
                    "priority": 1,
                    "limit_per_dc": 0,
                },
            ]
        }
        m = find_platform_mapping("MoneyGram-X", "nosite", "VMware", generic_first)
        self.assertEqual(m["device_type"], "VMware Moneygram")


class TestDcCodeExtraction(unittest.TestCase):
    """Prod vs DR proxy keys use DC13 / DC16 from Site or location string."""

    def test_dc16_from_moneygram_site(self):
        self.assertEqual(extract_dc_code_for_proxy("Moneygramdr-DC16"), "DC16")

    def test_dc13(self):
        self.assertEqual(extract_dc_code_for_proxy("Moneygram-DC13-CLS"), "DC13")


if __name__ == "__main__":
    unittest.main()
