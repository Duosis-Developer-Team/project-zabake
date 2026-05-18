#!/usr/bin/env python3
"""Unit tests for Zabbix host resolution chain (Loki_ID -> hostname -> visible name)."""

import unittest


def resolve_existing_host(
    *,
    loki_id,
    zabbix_hostname_final,
    by_loki_id,
    by_hostname,
    by_visible_name,
):
    resolved = {}
    lid = str(loki_id or "").strip()
    if lid and by_loki_id:
        candidate = by_loki_id.get(lid, {})
        if candidate.get("hostid"):
            return candidate

    hostname = str(zabbix_hostname_final or "").strip()
    if hostname and by_hostname:
        candidate = by_hostname.get(hostname, {})
        if candidate.get("hostid"):
            return candidate

    if hostname and by_visible_name:
        candidate = by_visible_name.get(hostname, {})
        if candidate.get("hostid"):
            return candidate

    return resolved


class TestZabbixHostResolution(unittest.TestCase):
    def test_loki_id_match(self):
        host = {"hostid": "14001", "host": "c1h1ict11 - BMC", "name": "c1h1ict11 - BMC"}
        result = resolve_existing_host(
            loki_id="12365",
            zabbix_hostname_final="c1h1ict11 - BMC",
            by_loki_id={"12365": host},
            by_hostname={},
            by_visible_name={},
        )
        self.assertEqual(result["hostid"], "14001")

    def test_visible_name_fallback_when_no_loki_tag(self):
        host = {"hostid": "14001", "host": "c1h1ict11 - BMC", "name": "c1h1ict11 - BMC"}
        result = resolve_existing_host(
            loki_id="12365",
            zabbix_hostname_final="c1h1ict11 - BMC",
            by_loki_id={},
            by_hostname={"c1h1ict11 - BMC": host},
            by_visible_name={"c1h1ict11 - BMC": host},
        )
        self.assertEqual(result["hostid"], "14001")

    def test_no_match_returns_empty(self):
        result = resolve_existing_host(
            loki_id="12365",
            zabbix_hostname_final="c1h1ict11 - BMC",
            by_loki_id={},
            by_hostname={},
            by_visible_name={},
        )
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
