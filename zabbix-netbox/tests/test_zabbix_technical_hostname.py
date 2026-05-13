"""Unit tests for Zabbix technical hostname transliteration (filter plugin core)."""

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


def test_turkish_letters_transliterate():
    mod = _load_module()
    fn = mod.zabbix_technical_hostname
    assert fn("İstanbul-Şişli-01") == "Istanbul-Sisli-01"
    assert fn("Ağ_Rafı") == "Ag_Rafi"
    assert fn("Örnek_Ünite") == "Ornek_Unite"
    assert fn("Çanakkale_Göç") == "Canakkale_Goc"


def test_ascii_passthrough():
    mod = _load_module()
    fn = mod.zabbix_technical_hostname
    assert fn("dc11-switch-01") == "dc11-switch-01"
    assert fn("HOST.01") == "HOST.01"


def test_max_length_truncation():
    mod = _load_module()
    fn = mod.zabbix_technical_hostname
    long_name = "a" * 200
    out = fn(long_name)
    assert len(out) == 128


def test_empty_input_uses_fallback_id():
    mod = _load_module()
    fn = mod.zabbix_technical_hostname
    assert fn("", "42") == "host-42"
    assert fn("   ", "P_7") == "P_7"


def test_only_special_chars_uses_fallback():
    mod = _load_module()
    fn = mod.zabbix_technical_hostname
    assert fn("@@@###", "99") == "host-99"


def test_filter_module_registers():
    mod = _load_module()
    fm = mod.FilterModule()
    assert "zabbix_technical_hostname" in fm.filters()
    assert "zabbix_platform_technical_hostname" in fm.filters()


def test_platform_technical_hostname_appends_id_suffix():
    mod = _load_module()
    fn = mod.zabbix_platform_technical_hostname
    out = fn("My-Cluster-Name", "117")
    assert out.endswith("_P_117")
    assert len(out) <= 128


def test_platform_technical_hostname_unique_for_same_name_different_id():
    mod = _load_module()
    fn = mod.zabbix_platform_technical_hostname
    a = fn("Same-Name", "1")
    b = fn("Same-Name", "2")
    assert a != b
    assert a.endswith("_P_1")
    assert b.endswith("_P_2")


def test_platform_technical_hostname_idempotent_when_suffix_present():
    mod = _load_module()
    fn = mod.zabbix_platform_technical_hostname
    base = fn("Short", "99")
    assert base.endswith("_P_99")
    assert fn(base, "99") == base
