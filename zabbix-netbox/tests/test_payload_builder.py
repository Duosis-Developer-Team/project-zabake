"""Unit tests for zabbix_payload_builder.py (Phase A payload build)."""
import json
import os
import sys

import pytest

_FILES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "playbooks",
    "roles",
    "netbox_zabbix_sync",
    "files",
)
_MODULE_UTILS = os.path.join(
    os.path.dirname(__file__),
    "..",
    "playbooks",
    "roles",
    "netbox_zabbix_sync",
    "module_utils",
)
sys.path.insert(0, os.path.abspath(_FILES_DIR))
sys.path.insert(0, os.path.abspath(_MODULE_UTILS))

from zabbix_payload_builder import (  # noqa: E402
    ZabbixPayloadBuilder,
    build_proxy_group_config,
    _extract_dc_code,
)

TEMPLATE_TYPE_MAP = {
    "snmpv2": {
        "interface": {
            "type": 2,
            "port": 161,
            "useip": 1,
            "dns": "",
            "details": {"version": 2, "bulk": 1, "community": "public"},
        }
    },
    "agent": {
        "interface": {"type": 1, "port": 10050, "useip": 1, "dns": ""},
    },
}

TEMPLATES_MAP = {
    "Generic SNMP": [
        {
            "name": "BLT - SNMP Template",
            "snmpv2": True,
            "host_groups": ["Network"],
            "macros": {"{$SNMP_COMMUNITY}": "{HOST.IP}"},
        }
    ],
}

BASE_CTX = {
    "templates_map": TEMPLATES_MAP,
    "template_type_map": TEMPLATE_TYPE_MAP,
    "template_id_cache": {"BLT - SNMP Template": "10001"},
    "group_id_cache": {"Network": "20001", "Generic SNMP": "20002"},
    "proxy_group_config": [
        {"name": "Dc14-proxy Group", "proxy_groupid": "45", "dc_pattern": "DC14"},
    ],
    "tags_config": {"tags": {"definitions": [{"tag_name": "Location", "enabled": True}]}},
    "platform_managed_tag_keys": [],
    "vfw_managed_tag_keys": [],
    "hmdl_baseline_map": {},
}


def test_extract_dc_code():
    assert _extract_dc_code("DC14-Rack1") == "DC14"
    assert _extract_dc_code("") == ""


def test_build_proxy_group_config():
    cfg = build_proxy_group_config({"Dc14-proxy Group": "45"})
    assert len(cfg) == 1
    assert cfg[0]["dc_pattern"] == "DC14"
    assert cfg[0]["proxy_groupid"] == "45"


def test_detect_missing_groups():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    missing = builder.detect_missing_groups(["Network", "Brand New Group"])
    assert "Brand New Group" in missing
    assert "Network" not in missing


def test_resolve_proxy_group_id():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    monitored_by, pg_id, _ = builder.resolve_proxy(
        {"DC_ID": "DC14"},
        TEMPLATES_MAP["Generic SNMP"],
    )
    assert monitored_by == "2"
    assert pg_id == "45"


def test_build_create_payload_basic():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    plan = {
        "action": "create",
        "zbx_record": {
            "DEVICE_TYPE": "Generic SNMP",
            "DEVICE_ROLE": "Switch",
            "HOST_IP": "10.0.0.1",
            "HOSTNAME": "switch-01",
            "HOST_VISIBLE_NAME": "switch-01",
            "HOST_STATUS": 0,
            "DC_ID": "DC14",
            "HOST_GROUPS": "Network",
            "MACROS": json.dumps({"Location": "DC14"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {},
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["action"] == "create"
    assert enriched["create_payload"] is not None
    assert enriched["create_payload"]["host"] == "switch-01"
    assert enriched["create_payload"]["interfaces"][0]["ip"] == "10.0.0.1"
    assert enriched["create_payload"]["templates"][0]["templateid"] == "10001"
    assert enriched["create_payload"]["proxy_groupid"] == 45
    assert enriched["needs_update"] is False


def test_compute_update_delta_no_change_returns_none_payload():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    plan = {
        "action": "update",
        "device_id": "1",
        "zbx_record": {
            "DEVICE_TYPE": "Generic SNMP",
            "DEVICE_ROLE": "Switch",
            "HOST_IP": "10.0.0.1",
            "HOSTNAME": "switch-01",
            "HOST_VISIBLE_NAME": "switch-01",
            "DC_ID": "DC14",
            "HOST_GROUPS": "Network,Generic SNMP",
            "MACROS": json.dumps({"Location": "DC14"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {
            "hostid": "50001",
            "host": "switch-01",
            "monitored_by": "2",
            "proxy_groupid": "45",
            "interfaces": [
                {
                    "interfaceid": "60001",
                    "type": "2",
                    "ip": "10.0.0.1",
                    "port": "161",
                }
            ],
            "groups": [{"name": "Network"}, {"name": "Generic SNMP"}],
            "tags": [{"tag": "Location", "value": "DC14"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["action"] == "update"
    assert enriched["needs_update"] is False
    assert enriched["update_payload"] is None
    assert enriched["current_device_result"]["status"] == "güncel"


def test_compute_update_delta_tag_change():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    plan = {
        "action": "update",
        "device_id": "1",
        "zbx_record": {
            "DEVICE_TYPE": "Generic SNMP",
            "DEVICE_ROLE": "Switch",
            "HOST_IP": "10.0.0.1",
            "HOSTNAME": "switch-01",
            "HOST_VISIBLE_NAME": "switch-01",
            "DC_ID": "DC14",
            "HOST_GROUPS": "Network,Generic SNMP",
            "MACROS": json.dumps({"Location": "DC15"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {
            "hostid": "50001",
            "host": "switch-01",
            "monitored_by": "2",
            "proxy_groupid": "45",
            "interfaces": [
                {"interfaceid": "60001", "type": "2", "ip": "10.0.0.1", "port": "161"}
            ],
            "groups": [{"name": "Network"}, {"name": "Generic SNMP"}],
            "tags": [{"tag": "Location", "value": "DC14"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["needs_update"] is True
    assert enriched["update_payload"] is not None
    tags = {t["tag"]: t["value"] for t in enriched["update_payload"]["tags"]}
    assert tags["Location"] == "DC15"


def test_validation_failure_skips_plan():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    plan = {
        "action": "create",
        "device_id": "99",
        "zbx_record": {
            "DEVICE_TYPE": "Unknown Type",
            "DEVICE_ROLE": "Switch",
            "HOST_IP": "10.0.0.1",
            "HOSTNAME": "switch-01",
            "DC_ID": "DC14",
            "HOST_GROUPS": "",
            "MACROS": "{}",
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {},
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["action"] == "skip"
    assert enriched["create_payload"] is None
