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
    assert "interfaces" not in enriched["update_payload"]
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


SNMPV3_TEMPLATE_TYPE_MAP = {
    **TEMPLATE_TYPE_MAP,
    "snmpv3": {
        "interface": {
            "type": 2,
            "port": 161,
            "useip": 1,
            "dns": "",
            "details": {
                "version": 3,
                "bulk": 1,
                "securityname": "zabbix",
                "securitylevel": 2,
            },
        }
    },
}

LENOVO_IPMI_CTX = {
    **BASE_CTX,
    "templates_map": {
        "Lenovo IPMI": [
            {
                "name": "BLT - Lenovo ICT XCC Monitoring",
                "type": "snmpv3",
                "host_groups": ["Physical Hosts"],
            }
        ]
    },
    "template_type_map": SNMPV3_TEMPLATE_TYPE_MAP,
    "template_id_cache": {"BLT - Lenovo ICT XCC Monitoring": "10002"},
    "group_id_cache": {
        **BASE_CTX["group_id_cache"],
        "Physical Hosts": "20003",
        "Lenovo IPMI": "20004",
    },
}


def test_resolve_template_types_from_type_string_field():
    builder = ZabbixPayloadBuilder(LENOVO_IPMI_CTX)
    names, types, _rows = builder.resolve_template_names_and_types("Lenovo IPMI")
    assert names == ["BLT - Lenovo ICT XCC Monitoring"]
    assert types == ["snmpv3"]
    assert builder.resolve_interface_type(types) == "snmpv3"


def test_lenovo_ipmi_create_payload_uses_snmpv3_interface():
    builder = ZabbixPayloadBuilder(LENOVO_IPMI_CTX)
    plan = {
        "action": "create",
        "device_id": "123",
        "zbx_record": {
            "DEVICE_TYPE": "Lenovo IPMI",
            "DEVICE_ROLE": "BMC",
            "HOST_IP": "10.34.2.61",
            "HOSTNAME": "10.34.2.61",
            "HOST_VISIBLE_NAME": "10.34.2.61 - BMC",
            "HOST_STATUS": 0,
            "DC_ID": "DC14",
            "HOST_GROUPS": "Physical Hosts,Lenovo IPMI",
            "MACROS": json.dumps({"Loki_ID": "123"}),
            "REPORT_LOCATION": "DC13",
            "REPORT_SITE": "DC13",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {},
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["action"] == "create"
    iface = enriched["create_payload"]["interfaces"][0]
    assert iface["details"]["version"] == 3
    assert "community" not in iface["details"]


def test_snmp_v3_downgrade_is_blocked_on_interface_update():
    builder = ZabbixPayloadBuilder(LENOVO_IPMI_CTX)
    existing_host = {
        "interfaces": [
            {
                "interfaceid": "70001",
                "type": "2",
                "ip": "10.34.2.61",
                "port": "161",
                "details": {"version": 3, "securityname": "zabbix"},
            }
        ]
    }
    iface_update, locked = builder.build_interface_update(
        {"HOST_IP": "10.34.2.61"},
        None,
        existing_host,
        interface_type_changed=False,
    )
    assert iface_update == []
    assert locked is False


def test_ip_change_only_sends_ip_in_interface_update():
    builder = ZabbixPayloadBuilder(BASE_CTX)
    existing_host = {
        "interfaces": [
            {
                "interfaceid": "70001",
                "type": "2",
                "ip": "10.0.0.1",
                "port": "161",
                "details": {"version": 2, "community": "custom_community"},
            }
        ]
    }
    iface_update, locked = builder.build_interface_update(
        {"HOST_IP": "10.0.0.99"},
        builder.resolve_interface_spec("snmpv2"),
        existing_host,
        interface_type_changed=False,
    )
    assert locked is False
    assert iface_update == [{"interfaceid": "70001", "ip": "10.0.0.99"}]
    assert "details" not in iface_update[0]
    assert "port" not in iface_update[0]
    assert "dns" not in iface_update[0]


def test_no_ip_change_omits_interfaces_from_payload():
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
                {
                    "interfaceid": "60001",
                    "type": "2",
                    "ip": "10.0.0.1",
                    "port": "161",
                    "details": {"version": 2, "community": "custom_community"},
                }
            ],
            "groups": [{"name": "Network"}, {"name": "Generic SNMP"}],
            "tags": [{"tag": "Location", "value": "DC14"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["needs_update"] is True
    assert "interfaces" not in enriched["update_payload"]


def test_interface_override_applied_on_create():
    ctx = {
        **BASE_CTX,
        "templates_map": {
            "H3C IPMI": [
                {
                    "name": "BLT - SNMP Template",
                    "type": "snmpv2",
                    "interface_override": {
                        "details": {"community": "H3C_custom_community"},
                        "port": 16100,
                    },
                    "host_groups": ["Network"],
                }
            ]
        },
    }
    builder = ZabbixPayloadBuilder(ctx)
    plan = {
        "action": "create",
        "device_id": "200",
        "zbx_record": {
            "DEVICE_TYPE": "H3C IPMI",
            "DEVICE_ROLE": "BMC",
            "HOST_IP": "10.0.0.50",
            "HOSTNAME": "h3c-bmc-01",
            "HOST_VISIBLE_NAME": "h3c-bmc-01",
            "HOST_STATUS": 0,
            "DC_ID": "DC14",
            "HOST_GROUPS": "Network,H3C IPMI",
            "MACROS": json.dumps({"Loki_ID": "200"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {},
    }
    enriched = builder.enrich_plan(plan)
    iface = enriched["create_payload"]["interfaces"][0]
    assert iface["port"] == "16100"
    assert iface["details"]["community"] == "H3C_custom_community"
    assert iface["details"]["version"] == 2


def test_interface_override_partial_merge():
    ctx = {
        **LENOVO_IPMI_CTX,
        "templates_map": {
            "Lenovo IPMI": [
                {
                    "name": "BLT - Lenovo ICT XCC Monitoring",
                    "type": "snmpv3",
                    "interface_override": {
                        "details": {"securityname": "lenovo_zabbix"},
                    },
                    "host_groups": ["Physical Hosts"],
                }
            ]
        },
    }
    builder = ZabbixPayloadBuilder(ctx)
    _, types, rows = builder.resolve_template_names_and_types("Lenovo IPMI")
    spec = builder.resolve_interface_spec_with_override(types[0], rows)
    assert spec["details"]["securityname"] == "lenovo_zabbix"
    assert spec["details"]["securitylevel"] == 2
    assert spec["details"]["version"] == 3


def test_interface_override_not_applied_on_update():
    ctx = {
        **LENOVO_IPMI_CTX,
        "templates_map": {
            "Lenovo IPMI": [
                {
                    "name": "BLT - Lenovo ICT XCC Monitoring",
                    "type": "snmpv3",
                    "interface_override": {
                        "details": {"securityname": "lenovo_zabbix"},
                    },
                    "host_groups": ["Physical Hosts"],
                }
            ]
        },
    }
    builder = ZabbixPayloadBuilder(ctx)
    plan = {
        "action": "update",
        "device_id": "123",
        "zbx_record": {
            "DEVICE_TYPE": "Lenovo IPMI",
            "DEVICE_ROLE": "BMC",
            "HOST_IP": "10.34.2.99",
            "HOSTNAME": "10.34.2.99",
            "HOST_VISIBLE_NAME": "10.34.2.99 - BMC",
            "DC_ID": "DC14",
            "HOST_GROUPS": "Physical Hosts,Lenovo IPMI",
            "MACROS": json.dumps({"Loki_ID": "123", "Location": "DC14"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {
            "hostid": "50002",
            "host": "10.34.2.99",
            "monitored_by": "2",
            "proxy_groupid": "45",
            "interfaces": [
                {
                    "interfaceid": "60002",
                    "type": "2",
                    "ip": "10.34.2.61",
                    "port": "161",
                    "details": {"version": 3, "securityname": "custom", "securitylevel": 2},
                }
            ],
            "groups": [{"name": "Physical Hosts"}, {"name": "Lenovo IPMI"}],
            "tags": [{"tag": "Loki_ID", "value": "123"}, {"tag": "Location", "value": "DC14"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["needs_update"] is True
    ifaces = enriched["update_payload"].get("interfaces") or []
    assert ifaces == [{"interfaceid": "60002", "ip": "10.34.2.99"}]


def test_update_reasons_populated_on_tag_change():
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
    assert "tags:" in "; ".join(enriched["update_reasons"])
    assert enriched["current_device_result"]["reason"]
    assert "Location" in enriched["current_device_result"]["reason"] or "tags" in enriched["update_reasons"][0]


def test_lenovo_ipmi_update_does_not_downgrade_snmp_when_tags_change():
    """Simulates Phase A plan: tag delta must not rewrite SNMPv3 interface to v2."""
    builder = ZabbixPayloadBuilder(LENOVO_IPMI_CTX)
    plan = {
        "action": "update",
        "device_id": "123",
        "zbx_record": {
            "DEVICE_TYPE": "Lenovo IPMI",
            "DEVICE_ROLE": "BMC",
            "HOST_IP": "10.34.2.61",
            "HOSTNAME": "10.34.2.61",
            "HOST_VISIBLE_NAME": "10.34.2.61 - BMC",
            "DC_ID": "DC14",
            "HOST_GROUPS": "Physical Hosts,Lenovo IPMI",
            "MACROS": json.dumps({"Loki_ID": "123", "Location": "DC14-Rack1"}),
            "REPORT_LOCATION": "DC14",
            "REPORT_SITE": "DC14",
            "REPORT_TENANT": "",
            "REPORT_OWNERSHIP": "",
        },
        "zbx_existing_host": {
            "hostid": "50002",
            "host": "10.34.2.61",
            "monitored_by": "2",
            "proxy_groupid": "45",
            "interfaces": [
                {
                    "interfaceid": "60002",
                    "type": "2",
                    "ip": "10.34.2.61",
                    "port": "161",
                    "details": {"version": 3, "securityname": "zabbix", "securitylevel": 2},
                }
            ],
            "groups": [{"name": "Physical Hosts"}, {"name": "Lenovo IPMI"}],
            "tags": [{"tag": "Loki_ID", "value": "123"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["needs_update"] is True
    payload = enriched["update_payload"]
    assert "interfaces" not in payload
    assert "tags:" in "; ".join(enriched["update_reasons"])


def test_update_reasons_empty_when_no_delta():
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
                {"interfaceid": "60001", "type": "2", "ip": "10.0.0.1", "port": "161"}
            ],
            "groups": [{"name": "Network"}, {"name": "Generic SNMP"}],
            "tags": [{"tag": "Location", "value": "DC14"}],
        },
    }
    enriched = builder.enrich_plan(plan)
    assert enriched["needs_update"] is False
    assert enriched["update_reasons"] == []
