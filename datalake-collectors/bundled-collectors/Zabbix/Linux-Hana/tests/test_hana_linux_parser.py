"""Unit tests for Hana Linux Zabbix item parser."""

from __future__ import annotations

import unittest

from lib.hana_linux_parser import parse_hana_linux_items
from lib.template_filter import filter_linux_agent_hosts, host_has_linux_agent_template


class TestTemplateFilter(unittest.TestCase):
    def test_matches_linux_agent_template_variant(self):
        host = {
            "parentTemplates": [{"name": "BLT - Linux by Zabbix Agent Active"}],
        }
        self.assertTrue(host_has_linux_agent_template(host))

    def test_rejects_non_linux_template(self):
        host = {"parentTemplates": [{"name": "BLT - Template Module ICMP Ping"}]}
        self.assertFalse(host_has_linux_agent_template(host))

    def test_filter_linux_agent_hosts(self):
        hosts = [
            {"hostid": "1", "parentTemplates": [{"name": "Linux by Zabbix Agent"}]},
            {"hostid": "2", "parentTemplates": [{"name": "ICMP Ping"}]},
        ]
        filtered = filter_linux_agent_hosts(hosts)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["hostid"], "1")


class TestHanaLinuxParser(unittest.TestCase):
    def _host(self) -> dict:
        return {
            "hostid": "101",
            "name": "zbx-host-101",
            "host": "zbx-host-101",
            "parentTemplates": [{"name": "BLT - Linux by Zabbix Agent"}],
        }

    def test_parses_agent_hostname_and_partition_name(self):
        items = [
            {"name": "Host name of Zabbix agent running", "lastvalue": "hana01.example", "units": ""},
            {"name": "IBM Partition Name", "lastvalue": "BOYNER_SAP01", "units": ""},
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["agent_hostname"], "hana01.example")
        self.assertEqual(record["host"], "hana01.example")
        self.assertEqual(record["ibm_partition_name"], "BOYNER_SAP01")
        self.assertEqual(record["data_type"], "zabbix_hana_linux_host")

    def test_parses_memory_and_root_disk_metrics(self):
        items = [
            {"name": "Host name of Zabbix agent running", "lastvalue": "hana01", "units": ""},
            {"name": "IBM Partition Name", "lastvalue": "LPAR01", "units": ""},
            {"name": "Total memory", "lastvalue": "17179869184", "units": "B"},
            {"name": "Available memory", "lastvalue": "8589934592", "units": "B"},
            {"name": "FS [/]: Space: Total", "lastvalue": "107374182400", "units": "B"},
            {"name": "FS [/]: Space: Used", "lastvalue": "53687091200", "units": "B"},
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["memory_total_bytes"], 17179869184)
        self.assertEqual(record["memory_used_bytes"], 8589934592)
        self.assertEqual(record["memory_utilization_pct"], 50.0)
        self.assertEqual(record["disk_total_bytes"], 107374182400)
        self.assertEqual(record["disk_used_bytes"], 53687091200)
        self.assertEqual(record["disk_utilization_pct"], 50.0)

    def test_parses_modern_fs_item_names(self):
        items = [
            {"name": "FS [/]: Total space", "key_": "vfs.fs.dependent.size[/,total]", "lastvalue": "1000", "units": "B"},
            {"name": "FS [/]: Used space", "key_": "vfs.fs.dependent.size[/,used]", "lastvalue": "400", "units": "B"},
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["disk_total_bytes"], 1000)
        self.assertEqual(record["disk_used_bytes"], 400)
        self.assertEqual(record["disk_utilization_pct"], 40.0)

    def test_parses_legacy_disk_space_on_root_items(self):
        items = [
            {"name": "Total disk space on /", "key_": "vfs.fs.size[/,total]", "lastvalue": "2000", "units": "B"},
            {"name": "Used disk space on /", "key_": "vfs.fs.size[/,used]", "lastvalue": "500", "units": "B"},
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["disk_total_bytes"], 2000)
        self.assertEqual(record["disk_used_bytes"], 500)

    def test_parses_disk_metrics_from_item_key_only(self):
        items = [
            {
                "name": "Root filesystem total",
                "key_": "vfs.fs.size[/,total]",
                "lastvalue": "8589934592",
                "units": "B",
            },
            {
                "name": "Root filesystem used percent",
                "key_": "vfs.fs.size[/,pused]",
                "lastvalue": "61.2",
                "units": "%",
            },
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["disk_total_bytes"], 8589934592)
        self.assertEqual(record["disk_utilization_pct"], 61.2)
        self.assertEqual(record["disk_used_bytes"], int(8589934592 * 61.2 / 100.0))

    def test_uses_memory_utilization_directly(self):
        items = [
            {"name": "Memory utilization", "lastvalue": "73.5", "units": "%"},
            {"name": "Total memory", "lastvalue": "1000", "units": "B"},
        ]
        record = parse_hana_linux_items(self._host(), items, 1_700_000_000_000)
        self.assertEqual(record["memory_utilization_pct"], 73.5)
        self.assertEqual(record["memory_used_bytes"], 735)


if __name__ == "__main__":
    unittest.main()
