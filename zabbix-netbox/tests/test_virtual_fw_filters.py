"""Unit tests for virtual firewall helpers (filter plugin core)."""

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parent.parent
    path = root / "playbooks" / "roles" / "netbox_zabbix_sync" / "filter_plugins" / "zabbix_hostname.py"
    spec = importlib.util.spec_from_file_location("zabbix_hostname_filter", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_parse_virtual_fw_ip_port_ipv4_with_port():
    mod = _load_module()
    assert mod.parse_virtual_fw_ip_port("194.56.187.241:4444") == {
        "ip": "194.56.187.241",
        "port": "4444",
    }


def test_parse_virtual_fw_ip_port_ip_only():
    mod = _load_module()
    assert mod.parse_virtual_fw_ip_port("10.0.0.1") == {"ip": "10.0.0.1", "port": ""}


def test_parse_virtual_fw_ip_port_empty():
    mod = _load_module()
    assert mod.parse_virtual_fw_ip_port("") == {"ip": "", "port": ""}
    assert mod.parse_virtual_fw_ip_port(None) == {"ip": "", "port": ""}


def test_parse_virtual_fw_ip_port_non_numeric_last_segment():
    mod = _load_module()
    out = mod.parse_virtual_fw_ip_port("2001:db8::1")
    assert out["port"] == ""
    assert out["ip"] == "2001:db8::1"


def test_virtual_fw_mapping_match_vendor_only():
    mod = _load_module()
    entries = [
        {"vendor": "SOPHOS", "device_type": "Sophos Firewall"},
        {"vendor": "FORTINET", "device_type": "Fortinet Firewall"},
    ]
    assert mod.virtual_fw_mapping_match(entries, "sophos", "XG135") == entries[0]


def test_virtual_fw_mapping_match_prefix():
    mod = _load_module()
    entries = [
        {"vendor": "SOPHOS", "model_prefix": "XG", "device_type": "Sophos Firewall"},
        {"vendor": "SOPHOS", "device_type": "Sophos Other"},
    ]
    assert mod.virtual_fw_mapping_match(entries, "SOPHOS", "XG135") == entries[0]
    assert mod.virtual_fw_mapping_match(entries, "SOPHOS", "SG125") == entries[1]


def test_virtual_fw_mapping_match_suffix():
    mod = _load_module()
    entries = [{"vendor": "X", "model_suffix": "135", "device_type": "T"}]
    assert mod.virtual_fw_mapping_match(entries, "X", "XG135") == entries[0]
    assert mod.virtual_fw_mapping_match(entries, "X", "XG136") == {}


def test_zabbix_vfw_technical_hostname_suffix():
    mod = _load_module()
    out = mod.zabbix_vfw_technical_hostname("SERIM_HOST_DC14", "570")
    assert out.endswith("_VFW_570")
    assert len(out) <= 128


def test_zabbix_vfw_display_name_appends_suffix():
    mod = _load_module()
    assert mod.zabbix_vfw_display_name("UNIVERA-FINROTA") == "UNIVERA-FINROTA - Firewall"


def test_zabbix_vfw_display_name_idempotent():
    mod = _load_module()
    s = "UNIVERA-FINROTA - Firewall"
    assert mod.zabbix_vfw_display_name(s) == s


def test_zabbix_vfw_display_name_empty():
    mod = _load_module()
    assert mod.zabbix_vfw_display_name("") == ""
    assert mod.zabbix_vfw_display_name(None) == ""


def test_vfw_hostname_prefix_hostgroup():
    mod = _load_module()
    assert mod.vfw_hostname_prefix_hostgroup("UNIVERA-FINROTA") == "Univera"


def test_vfw_hostname_prefix_hostgroup_no_hyphen():
    mod = _load_module()
    assert mod.vfw_hostname_prefix_hostgroup("SINGLE") == ""


def test_vfw_hostname_prefix_hostgroup_empty_prefix():
    mod = _load_module()
    assert mod.vfw_hostname_prefix_hostgroup("-foo") == ""


def test_filter_module_registers_virtual_fw_filters():
    mod = _load_module()
    fm = mod.FilterModule()
    names = fm.filters()
    assert "zabbix_vfw_technical_hostname" in names
    assert "zabbix_vfw_display_name" in names
    assert "vfw_hostname_prefix_hostgroup" in names
    assert "parse_virtual_fw_ip_port" in names
    assert "virtual_fw_mapping_match" in names
