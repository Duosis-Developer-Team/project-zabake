#!/usr/bin/env python3
"""
Unit tests: Loki (NetBox API) device JSON → flat fields → device_type mapping.
"""

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playbooks/roles/netbox_zabbix_sync/files"))

from netbox_device_normalize import (  # noqa: E402
    device_role_name,
    extract_primary_ip_address,
    manufacturer_name,
    normalize_device_record,
)

from test_device_type_mapping import (  # noqa: E402
    check_condition,
    determine_device_type,
    find_matching_mapping,
)

MAPPING_PATH = ROOT / "mappings" / "netbox_device_type_mapping.yml"

LOKI_HOST_RAW = {
    "id": 12345,
    "name": "c1h1ict11",
    "status": {"value": "active", "label": "Active"},
    "role": {"id": 1, "name": "HOST", "slug": "host"},
    "device_type": {
        "id": 99,
        "model": "ThinkAgile HX7531",
        "manufacturer": {"id": 10, "name": "LENOVO", "slug": "lenovo"},
    },
    "primary_ip4": {"id": 501, "address": "10.11.12.13/24", "display": "10.11.12.13/24"},
    "location": {"id": 200, "name": "Rack-A1", "parent": {"id": 100, "name": "ICT11"}},
    "site": {"id": 50, "name": "DC-Example"},
    "tenant": {"id": 5, "name": "TEAM VIRTUALIZATION"},
    "custom_fields": {"Sahiplik": "TEAM VIRTUALIZATION", "izlenmeli": "Evet"},
}


class TestLokiDeviceNormalize(unittest.TestCase):
  """Normalize NetBox API payloads to datalake-compatible flat fields."""

  @classmethod
  def setUpClass(cls):
    with open(MAPPING_PATH, encoding="utf-8") as handle:
      cls.device_type_mapping = yaml.safe_load(handle)

  def test_raw_nested_fields_empty_before_normalize(self):
    self.assertEqual(LOKI_HOST_RAW.get("device_role_name"), None)
    self.assertEqual(LOKI_HOST_RAW.get("manufacturer_name"), None)

  def test_normalize_populates_flat_fields(self):
    record = normalize_device_record(LOKI_HOST_RAW, location_filter="ICT11")
    self.assertEqual(record["device_role_name"], "HOST")
    self.assertEqual(record["manufacturer_name"], "LENOVO")
    self.assertEqual(record["device_model"], "ThinkAgile HX7531")
    self.assertEqual(record["primary_ip_address"], "10.11.12.13")
    self.assertEqual(record["location_name"], "Rack-A1")
    self.assertEqual(record["root_location_name"], "ICT11")
    self.assertEqual(record["tenant_name"], "TEAM VIRTUALIZATION")

  def test_helpers_read_nested_without_flat_columns(self):
    self.assertEqual(device_role_name(LOKI_HOST_RAW), "HOST")
    self.assertEqual(manufacturer_name(LOKI_HOST_RAW), "LENOVO")
    self.assertEqual(extract_primary_ip_address(LOKI_HOST_RAW), "10.11.12.13")

  def test_normalized_device_matches_lenovo_ipmi(self):
    record = normalize_device_record(LOKI_HOST_RAW, location_filter="ICT11")
    device_type = determine_device_type(record, self.device_type_mapping)
    self.assertEqual(device_type, "Lenovo IPMI")

  def test_normalized_passes_mapping_conditions(self):
    record = normalize_device_record(LOKI_HOST_RAW, location_filter="ICT11")
    mapping = find_matching_mapping(record, self.device_type_mapping)
    self.assertIsNotNone(mapping)
    self.assertEqual(mapping.get("device_type"), "Lenovo IPMI")
    conditions = mapping.get("conditions", {})
    for key, value in conditions.items():
      self.assertTrue(
        check_condition(record, key, value),
        msg=f"condition {key}={value} failed on normalized record",
      )

  def test_flat_only_record_still_works(self):
    flat = {
      "name": "db-host-01",
      "device_role_name": "HOST",
      "manufacturer_name": "LENOVO",
      "device_model": "SR650",
    }
    self.assertEqual(determine_device_type(flat, self.device_type_mapping), "Lenovo IPMI")


if __name__ == "__main__":
  unittest.main()
