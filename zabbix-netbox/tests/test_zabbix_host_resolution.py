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


def resolve_vfw_existing_host(
    *,
    vfw_loki_id,
    target_hostname,
    host_visible_name,
    legacy_hostname_raw,
    by_loki_id,
    by_hostname,
    by_visible_name,
):
    """
    Mirror virtual firewall host resolution in process_virtual_fw.yml:
    Loki_ID -> override when stale Loki host vs canonical hostname -> hostname -> visible fallbacks.
    """
    resolved = {}
    lid = f"VFW_{str(vfw_loki_id or '').strip()}"
    if lid and lid != "VFW_" and by_loki_id:
        candidate = by_loki_id.get(lid, {})
        if candidate.get("hostid"):
            resolved = candidate

    hostname = str(target_hostname or "").strip()
    if (
        resolved.get("hostid")
        and hostname
        and by_hostname
        and resolved.get("host", "") != hostname
    ):
        canonical = by_hostname.get(hostname, {})
        if canonical.get("hostid"):
            resolved = canonical

    if not resolved.get("hostid") and hostname and by_hostname:
        candidate = by_hostname.get(hostname, {})
        if candidate.get("hostid"):
            resolved = candidate

    visible = str(host_visible_name or "").strip()
    if not resolved.get("hostid") and visible and by_visible_name:
        candidate = by_visible_name.get(visible, {})
        if candidate.get("hostid"):
            resolved = candidate

    legacy = str(legacy_hostname_raw or "").strip()
    if not resolved.get("hostid") and legacy and by_visible_name:
        candidate = by_visible_name.get(legacy, {})
        if candidate.get("hostid"):
            resolved = candidate

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


class TestVfwHostResolution(unittest.TestCase):
    def test_loki_id_override_when_canonical_hostname_exists_elsewhere(self):
        """Stale host holds Loki_ID; canonical technical hostname is on another host."""
        stale_host = {
            "hostid": "34103",
            "host": "DIJITAL_KURYE - Firewall",
            "name": "DIJITAL_KURYE - Firewall",
        }
        canonical_host = {
            "hostid": "35001",
            "host": "DIJITAL_KURYE_DC14_VFW_804",
            "name": "DIJITAL_KURYE - Firewall",
        }
        target = "DIJITAL_KURYE_DC14_VFW_804"
        result = resolve_vfw_existing_host(
            vfw_loki_id="804",
            target_hostname=target,
            host_visible_name="DIJITAL_KURYE - Firewall",
            legacy_hostname_raw="DIJITAL_KURYE_DC14",
            by_loki_id={"VFW_804": stale_host},
            by_hostname={target: canonical_host},
            by_visible_name={"DIJITAL_KURYE - Firewall": stale_host},
        )
        self.assertEqual(result["hostid"], "35001")
        self.assertEqual(result["host"], target)

    def test_loki_id_match_used_when_hostname_already_correct(self):
        host = {
            "hostid": "15342",
            "host": "SERIM_BILGISAYAR_DC14_VFW_570",
            "name": "SERIM_BILGISAYAR - Firewall",
        }
        target = "SERIM_BILGISAYAR_DC14_VFW_570"
        result = resolve_vfw_existing_host(
            vfw_loki_id="570",
            target_hostname=target,
            host_visible_name="SERIM_BILGISAYAR - Firewall",
            legacy_hostname_raw="SERIM_BILGISAYAR_DC14",
            by_loki_id={"VFW_570": host},
            by_hostname={target: host},
            by_visible_name={},
        )
        self.assertEqual(result["hostid"], "15342")

    def test_hostname_fallback_when_no_loki_tag(self):
        host = {
            "hostid": "36000",
            "host": "IXPANSE_TEKNOLOJI_VFW_889",
            "name": "IXPANSE_TEKNOLOJI - Firewall",
        }
        target = "IXPANSE_TEKNOLOJI_VFW_889"
        result = resolve_vfw_existing_host(
            vfw_loki_id="889",
            target_hostname=target,
            host_visible_name="IXPANSE_TEKNOLOJI - Firewall",
            legacy_hostname_raw="IXPANSE_TEKNOLOJI",
            by_loki_id={},
            by_hostname={target: host},
            by_visible_name={},
        )
        self.assertEqual(result["hostid"], "36000")


if __name__ == "__main__":
    unittest.main()
