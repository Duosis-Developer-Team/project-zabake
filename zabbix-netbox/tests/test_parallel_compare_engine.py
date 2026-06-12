"""
Unit tests for parallel_compare_engine.py

Covers:
- compare_one_device: determinism, skip cases, plan format
- compare_one_platform: mapping, skip cases, plan format
- compare_one_vfw: mapping, skip cases, plan format
- Parallel error isolation (one failure does not abort others)
- Plan format Phase B compatibility
"""
import json
import os
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

# Add files directory to path so the engine can be imported directly
_FILES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "playbooks", "roles", "netbox_zabbix_sync", "files"
)
sys.path.insert(0, os.path.abspath(_FILES_DIR))

from parallel_compare_engine import (
    compare_one_device,
    compare_one_platform,
    compare_one_vfw,
    process_device_info,
    run_parallel_compare,
    _find_matching_mapping_safe,
    _resolve_vfw_existing_host,
    zabbix_platform_technical_hostname,
    zabbix_vfw_technical_hostname,
    zabbix_vfw_display_name,
    vfw_hostname_prefix_hostgroup,
    parse_virtual_fw_ip_port,
    virtual_fw_mapping_match,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

DEVICE_TYPE_MAPPING = {
    "mappings": [
        {
            "priority": 1,
            "device_type": "HPE iLO BMC",
            "conditions": {"manufacturer": "HPE", "device_role": "Server"},
            "hostname_suffix": " - BMC",
        },
        {
            "priority": 2,
            "device_type": "Generic SNMP",
            "conditions": {"device_role": "Switch"},
        },
    ]
}

TEMPLATES_MAP = {
    "HPE iLO BMC": [{"name": "BLT - HPE iLO", "snmpv2": True, "host_groups": ["Physical Hosts"]}],
    "Generic SNMP": [{"name": "BLT - SNMP Switch", "snmpv2": True, "host_groups": ["Network"]}],
    "Juniper Platform": [{"name": "BLT - Juniper Platform", "snmpv2": True, "host_groups": ["Platforms"]}],
    "Fortinet VFW": [{"name": "BLT - Fortinet FW", "snmpv2": True, "host_groups": ["Virtual Firewalls"]}],
}

PLATFORM_MAPPING = {
    "mappings": [
        {
            "priority": 1,
            "manufacturer": "Juniper",
            "device_type": "Juniper Platform",
        }
    ]
}

VFW_MAPPING = {
    "mappings": [
        {
            "vendor": "Fortinet",
            "device_type": "Fortinet VFW",
        }
    ]
}


def _make_ctx(**overrides):
    ctx = {
        "device_type_mapping": DEVICE_TYPE_MAPPING,
        "host_groups_config": None,
        "tags_config": None,
        "templates_map": TEMPLATES_MAP,
        "platform_mapping": PLATFORM_MAPPING,
        "vfw_mapping": VFW_MAPPING,
        "by_loki": {},
        "by_hostname": {},
        "by_visible": {},
        "by_ip": {},
        "create_devices_disabled": False,
        "create_platforms_disabled": False,
        "create_virtual_fws_disabled": False,
    }
    ctx.update(overrides)
    return ctx


def _make_device(name="srv01dc14.blt.vc", device_id=1001, role="Server", manufacturer="HPE", ip="10.0.0.1"):
    return {
        "id": device_id,
        "name": name,
        "device_role_name": role,
        "manufacturer_name": manufacturer,
        "device_model": "ProLiant DL380 Gen10",
        "primary_ip_address": ip,
        "root_location_name": "DC14",
        "site_name": "DC14",
        "tenant_name": "Bulutistan",
    }


def _make_platform(name="TestPlatform", platform_id=2001, manufacturer="Juniper", ip="192.168.1.1", site="DC14"):
    return {
        "id": platform_id,
        "name": name,
        "manufacturer": {"name": manufacturer},
        "custom_fields": {
            "ip_addresses": ip,
            "Site": site,
            "DC": site,
        },
    }


def _make_vfw(hostname="ACME-FW1", vfw_id=3001, vendor="Fortinet", model="FortiGate 100F", location="DC14", ip_port="10.1.0.1:443"):
    return {
        "id": vfw_id,
        "hostname": hostname,
        "ip_port": ip_port,
        "vendor": {"name": vendor},
        "manufacturer_model": {"model": model, "manufacturer": {"name": vendor}},
        "lokasyon": {"name": location},
        "proje": "",
        "fw_status": "active",
    }


# ---------------------------------------------------------------------------
# Device tests
# ---------------------------------------------------------------------------

HPE_MONEYGRAM_MAPPING = {
    "mappings": [
        {
            "device_type": "HPE IPMI Moneygram",
            "tenant": "Moneygram",
            "conditions": {"device_role": "HOST", "manufacturer": ["HPE", "HP"]},
            "hostname_suffix": " - BMC",
            "priority": 1,
        },
        {
            "device_type": "HPE IPMI",
            "conditions": {"device_role": "HOST", "manufacturer": ["HPE", "HP"]},
            "hostname_suffix": " - BMC",
            "priority": 1,
        },
    ]
}


class TestHpeMoneygramTenantGate:
    def test_hpe_host_without_moneygram_tenant_gets_generic_ipmi(self):
        device = {
            "id": 9001,
            "name": "srv01",
            "device_role_name": "HOST",
            "manufacturer_name": "HPE",
            "device_model": "DL380",
            "primary_ip_address": "10.0.0.1",
            "tenant": {},
            "tenant_name": "CPE-Tenant",
        }
        info = process_device_info(device, HPE_MONEYGRAM_MAPPING, None, None, TEMPLATES_MAP)
        assert info["device_type"] == "HPE IPMI"

    def test_find_matching_mapping_safe_skips_moneygram_without_tenant(self):
        device = {
            "id": 9002,
            "name": "srv02",
            "device_role_name": "HOST",
            "manufacturer_name": "HPE",
            "tenant": {},
            "tenant_name": "",
        }
        mapping = _find_matching_mapping_safe(device, HPE_MONEYGRAM_MAPPING)
        assert mapping is not None
        assert mapping.get("device_type") == "HPE IPMI"


class TestCompareOneDevice:
    def test_create_scenario_when_not_in_zabbix(self):
        device = _make_device()
        plan = compare_one_device(device, _make_ctx())
        assert plan["action"] == "create"
        assert plan["zbx_scenario"] == "create"
        assert plan["zbx_record"]["HOSTNAME"] == "srv01dc14.blt.vc - BMC"
        assert plan["zbx_record"]["HOST_IP"] == "10.0.0.1"
        assert plan["device_id"] == 1001

    def test_update_scenario_when_exists_by_hostname(self):
        ctx = _make_ctx(by_hostname={"srv01dc14.blt.vc - BMC": {"hostid": "999", "host": "srv01dc14.blt.vc - BMC"}})
        plan = compare_one_device(_make_device(), ctx)
        assert plan["action"] == "update"
        assert plan["zbx_existing_host"]["hostid"] == "999"

    def test_update_scenario_when_exists_by_loki_id(self):
        ctx = _make_ctx(by_loki={"1001": {"hostid": "888", "host": "old_hostname"}})
        device = _make_device()
        device["id"] = 1001
        plan = compare_one_device(device, ctx)
        assert plan["action"] == "update"
        assert plan["zbx_existing_host"]["hostid"] == "888"

    def test_skip_when_matched_zabbix_host_is_network_discovered(self):
        hostname = "srv01dc14.blt.vc - BMC"
        ctx = _make_ctx(
            by_loki={
                "1001": {
                    "hostid": "777",
                    "host": hostname,
                    "flags": 4,
                }
            }
        )
        device = _make_device(name="srv01dc14.blt.vc", device_id=1001)
        plan = compare_one_device(device, ctx)
        assert plan["action"] == "skip"
        assert plan["zbx_scenario"] == "skip"
        assert plan["current_device_result"]["status"] == "atlandı"
        assert plan["current_device_result"]["reason"] == "Network Discovery, no action taken"

    def test_skip_when_no_matching_device_type(self):
        device = _make_device(role="Unknown Role", manufacturer="UnknownMfr")
        plan = compare_one_device(device, _make_ctx())
        assert plan["action"] == "skip"
        assert plan["current_device_result"]["status"] == "eklenemedi"
        assert "device type" in plan["current_device_result"]["reason"].lower()

    def test_skip_when_no_ip(self):
        device = _make_device(ip="")
        plan = compare_one_device(device, _make_ctx())
        assert plan["action"] == "skip"
        assert "IP" in plan["current_device_result"]["reason"]

    def test_determinism_same_result_on_repeated_calls(self):
        device = _make_device()
        ctx = _make_ctx()
        plan1 = compare_one_device(device, ctx)
        plan2 = compare_one_device(device, ctx)
        assert plan1["zbx_record"] == plan2["zbx_record"]
        assert plan1["action"] == plan2["action"]

    def test_plan_has_all_required_phase_b_keys(self):
        plan = compare_one_device(_make_device(), _make_ctx())
        for key in ("action", "device_id", "zbx_record", "zbx_existing_host", "zbx_scenario", "device_info", "netbox_device_name"):
            assert key in plan, f"Missing key: {key}"

    def test_zbx_record_has_all_required_fields(self):
        plan = compare_one_device(_make_device(), _make_ctx())
        zbx = plan["zbx_record"]
        for field in ("DEVICE_TYPE", "HOST_IP", "HOSTNAME", "HOST_VISIBLE_NAME", "DC_ID", "HOST_GROUPS", "MACROS"):
            assert field in zbx, f"Missing zbx_record field: {field}"

    def test_hostname_sanitize_tab_characters(self):
        device = _make_device(name="srv01\tdc14.blt.vc")
        plan = compare_one_device(device, _make_ctx())
        assert "\t" not in plan["zbx_record"]["HOSTNAME"]

    def test_hostname_suffix_applied(self):
        device = _make_device()
        plan = compare_one_device(device, _make_ctx())
        assert plan["zbx_record"]["HOSTNAME"].endswith(" - BMC")

    def test_create_devices_disabled_sets_host_status_1(self):
        ctx = _make_ctx(create_devices_disabled=True)
        plan = compare_one_device(_make_device(), ctx)
        assert plan["zbx_record"]["HOST_STATUS"] == 1

    def test_loki_id_in_tags(self):
        device = _make_device(device_id=9999)
        plan = compare_one_device(device, _make_ctx())
        tags = json.loads(plan["zbx_record"]["MACROS"])
        assert tags.get("Loki_ID") == "9999"


# ---------------------------------------------------------------------------
# Platform tests
# ---------------------------------------------------------------------------

class TestCompareOnePlatform:
    def test_create_scenario(self):
        plan = compare_one_platform(_make_platform(), _make_ctx())
        assert plan["action"] == "create"
        assert plan["zbx_record"]["DEVICE_TYPE"] == "Juniper Platform"

    def test_update_scenario_by_loki_id(self):
        pid = "2001"
        ctx = _make_ctx(by_loki={f"P_{pid}": {"hostid": "777", "host": "anything"}})
        plan = compare_one_platform(_make_platform(platform_id=int(pid)), ctx)
        assert plan["action"] == "update"
        assert plan["zbx_existing_host"]["hostid"] == "777"

    def test_skip_when_no_mapping(self):
        platform = _make_platform(manufacturer="UnknownVendor")
        plan = compare_one_platform(platform, _make_ctx())
        assert plan["action"] == "skip"

    def test_skip_when_no_ip(self):
        platform = _make_platform(ip="")
        plan = compare_one_platform(platform, _make_ctx())
        assert plan["action"] == "skip"

    def test_skip_invalid_site_code(self):
        platform = _make_platform(site="INVALID_SITE")
        plan = compare_one_platform(platform, _make_ctx())
        assert plan["action"] == "skip"
        assert "site" in plan["current_platform_result"]["reason"].lower()

    def test_technical_hostname_has_platform_id_suffix(self):
        plan = compare_one_platform(_make_platform(platform_id=2001), _make_ctx())
        assert "_P_2001" in plan["zbx_record"]["HOSTNAME"]

    def test_plan_has_all_required_keys(self):
        plan = compare_one_platform(_make_platform(), _make_ctx())
        for key in ("action", "platform_id", "zbx_record", "zbx_existing_host", "zbx_scenario"):
            assert key in plan, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Virtual firewall tests
# ---------------------------------------------------------------------------

class TestCompareOneVfw:
    def test_create_scenario(self):
        plan = compare_one_vfw(_make_vfw(), _make_ctx())
        assert plan["action"] == "create"
        assert plan["zbx_record"]["DEVICE_TYPE"] == "Fortinet VFW"

    def test_update_scenario_by_loki_id(self):
        vfw_id = "3001"
        ctx = _make_ctx(by_loki={f"VFW_{vfw_id}": {"hostid": "555", "host": "anything"}})
        plan = compare_one_vfw(_make_vfw(vfw_id=int(vfw_id)), ctx)
        assert plan["action"] == "update"

    def test_skip_when_no_ip(self):
        vfw = _make_vfw(ip_port="")
        plan = compare_one_vfw(vfw, _make_ctx())
        assert plan["action"] == "skip"

    def test_skip_when_no_vendor(self):
        vfw = _make_vfw()
        vfw["vendor"] = {}
        plan = compare_one_vfw(vfw, _make_ctx())
        assert plan["action"] == "skip"

    def test_skip_when_no_location(self):
        vfw = _make_vfw()
        vfw["lokasyon"] = {}
        plan = compare_one_vfw(vfw, _make_ctx())
        assert plan["action"] == "skip"

    def test_skip_when_no_mapping(self):
        vfw = _make_vfw(vendor="PaloAlto")
        plan = compare_one_vfw(vfw, _make_ctx())
        assert plan["action"] == "skip"

    def test_technical_hostname_has_vfw_suffix(self):
        plan = compare_one_vfw(_make_vfw(vfw_id=3001), _make_ctx())
        assert "_VFW_3001" in plan["zbx_record"]["HOSTNAME"]

    def test_visible_name_has_firewall_suffix(self):
        plan = compare_one_vfw(_make_vfw(hostname="ACME-FW1"), _make_ctx())
        assert plan["zbx_record"]["HOST_VISIBLE_NAME"] == "ACME-FW1 - Firewall"

    def test_loki_id_tag_is_vfw_prefixed(self):
        plan = compare_one_vfw(_make_vfw(vfw_id=3001), _make_ctx())
        tags = json.loads(plan["zbx_record"]["MACROS"])
        assert tags.get("Loki_ID") == "VFW_3001"

    def test_plan_has_all_required_keys(self):
        plan = compare_one_vfw(_make_vfw(), _make_ctx())
        for key in ("action", "vfw_id", "zbx_record", "zbx_existing_host", "zbx_scenario"):
            assert key in plan, f"Missing key: {key}"

    def test_update_scenario_by_ip_and_visible_name(self):
        hostname = "ADILE SULTAN_EV_YEMEKLERI"
        visible = f"{hostname} - Firewall"
        ip = "91.108.216.173"
        ctx = _make_ctx(
            by_ip={
                ip: {
                    "hostid": "88001",
                    "host": "ADILE_SULTAN_EV_YEMEKLERI_VFW_1884",
                    "name": visible,
                }
            }
        )
        plan = compare_one_vfw(
            _make_vfw(hostname=hostname, vfw_id=727, ip_port=f"{ip}:443"),
            ctx,
        )
        assert plan["action"] == "update"
        assert plan["zbx_existing_host"]["hostid"] == "88001"

    def test_canonical_override_when_loki_points_to_stale_host(self):
        target = zabbix_vfw_technical_hostname("DIJITAL_KURYE_DC14", "804")
        stale = {"hostid": "34103", "host": "DIJITAL_KURYE - Firewall", "name": "DIJITAL_KURYE - Firewall"}
        canonical = {"hostid": "35001", "host": target, "name": "DIJITAL_KURYE - Firewall"}
        ctx = _make_ctx(
            by_loki={"VFW_804": stale},
            by_hostname={target: canonical},
        )
        resolved = _resolve_vfw_existing_host(
            "804",
            target,
            "DIJITAL_KURYE - Firewall",
            "DIJITAL_KURYE_DC14",
            "10.0.0.1",
            ctx,
        )
        assert resolved["hostid"] == "35001"
        assert resolved["host"] == target


# ---------------------------------------------------------------------------
# Parallel error isolation
# ---------------------------------------------------------------------------

class TestParallelErrorIsolation:
    def test_single_error_does_not_abort_others(self, tmp_path):
        """One device that raises an exception should not block the rest."""
        good_device = _make_device(name="good_device", device_id=1)
        # Malformed device with no id and None name that will trigger processing
        bad_device = {"id": None, "name": None, "device_role_name": "Server", "manufacturer_name": "HPE"}

        ctx = _make_ctx()
        summary = run_parallel_compare(
            devices=[good_device, bad_device],
            platforms=[],
            vfws=[],
            ctx=ctx,
            output_dir=str(tmp_path),
            workers=2,
        )
        # Good device plan must exist
        good_plan_path = tmp_path / "device_plan_1.json"
        assert good_plan_path.exists(), "Good device plan file should be written even when another device fails"

    def test_all_results_in_summary(self, tmp_path):
        devices = [_make_device(device_id=i, name=f"srv{i}") for i in range(5)]
        summary = run_parallel_compare(
            devices=devices,
            platforms=[],
            vfws=[],
            ctx=_make_ctx(),
            output_dir=str(tmp_path),
            workers=5,
        )
        total = summary["devices"]["create"] + summary["devices"]["update"] + summary["devices"]["skip"] + summary["devices"]["error"]
        assert total == 5

    def test_plan_files_written_for_all_items(self, tmp_path):
        devices = [_make_device(device_id=i, name=f"srv{i}") for i in range(3)]
        run_parallel_compare(
            devices=devices,
            platforms=[],
            vfws=[],
            ctx=_make_ctx(),
            output_dir=str(tmp_path),
            workers=3,
        )
        for i in range(3):
            assert (tmp_path / f"device_plan_{i}.json").exists()

    def test_compare_summary_json_written(self, tmp_path):
        run_parallel_compare(
            devices=[_make_device()],
            platforms=[],
            vfws=[],
            ctx=_make_ctx(),
            output_dir=str(tmp_path),
            workers=1,
        )
        summary_path = tmp_path / "compare_summary.json"
        assert summary_path.exists()
        with open(summary_path) as f:
            data = json.load(f)
        assert "devices" in data
        assert "platforms" in data
        assert "vfws" in data

    def test_parallel_determinism(self, tmp_path):
        """Running 20 times on same input must yield identical plans."""
        device = _make_device(device_id=42)
        ctx = _make_ctx()
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(compare_one_device, device, ctx) for _ in range(20)]
            for f in futures:
                results.append(f.result()["zbx_record"]["HOSTNAME"])
        assert len(set(results)) == 1, "All parallel results must be identical"


# ---------------------------------------------------------------------------
# Filter / hostname helper tests
# ---------------------------------------------------------------------------

class TestHostnameHelpers:
    def test_platform_hostname_includes_suffix(self):
        result = zabbix_platform_technical_hostname("My Platform", "123")
        assert "_P_123" in result

    def test_vfw_hostname_includes_suffix(self):
        result = zabbix_vfw_technical_hostname("ACME-FW1", "456")
        assert "_VFW_456" in result

    def test_vfw_display_name_appends_firewall(self):
        assert zabbix_vfw_display_name("ACME-FW1") == "ACME-FW1 - Firewall"

    def test_vfw_display_name_idempotent(self):
        name = "ACME-FW1 - Firewall"
        assert zabbix_vfw_display_name(name) == name

    def test_vfw_display_empty(self):
        assert zabbix_vfw_display_name("") == ""

    def test_prefix_hostgroup(self):
        assert vfw_hostname_prefix_hostgroup("ACME-FW1") == "Acme"

    def test_prefix_hostgroup_no_hyphen(self):
        assert vfw_hostname_prefix_hostgroup("NOHYPHEN") == ""

    def test_parse_ip_port_basic(self):
        result = parse_virtual_fw_ip_port("10.0.0.1:443")
        assert result["ip"] == "10.0.0.1"
        assert result["port"] == "443"

    def test_parse_ip_port_no_port(self):
        result = parse_virtual_fw_ip_port("10.0.0.1")
        assert result["ip"] == "10.0.0.1"
        assert result["port"] == ""

    def test_parse_ip_port_empty(self):
        result = parse_virtual_fw_ip_port("")
        assert result["ip"] == ""
        assert result["port"] == ""

    def test_vfw_mapping_match_found(self):
        entries = [{"vendor": "Fortinet", "device_type": "FG-100F"}]
        result = virtual_fw_mapping_match(entries, "Fortinet", "FG-100F")
        assert result["device_type"] == "FG-100F"

    def test_vfw_mapping_match_not_found(self):
        entries = [{"vendor": "Fortinet", "device_type": "FG-100F"}]
        result = virtual_fw_mapping_match(entries, "PaloAlto", "PA-220")
        assert result == {}
