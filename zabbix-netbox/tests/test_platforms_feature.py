import pytest
from pathlib import Path

import yaml


def test_role_defaults_sync_flags():
    repo_root = Path(__file__).resolve().parent.parent
    defaults_path = repo_root / "playbooks" / "roles" / "netbox_zabbix_sync" / "defaults" / "main.yml"
    data = yaml.safe_load(defaults_path.read_text(encoding="utf-8"))
    assert data.get("sync_devices") is True
    assert data.get("sync_platforms") is False


def get_izlenmeli_status(platform):
    """Keep in sync with fetch_all_platforms.yml embedded script."""
    custom_fields = platform.get("custom_fields") or {}
    val = custom_fields.get("izlenmeli")
    if val is None:
        return "null"
    if val is False:
        return "hayir"
    text = str(val).strip().lower()
    if text == "false":
        return "hayir"
    if text in ["evet", "true", "yes", "1"]:
        return "evet"
    if text in ["hayir", "hayır", "no", "0"]:
        return "hayir"
    return "null"


def select_platforms_for_mode(all_platforms, izlenmeli_mode="monitor"):
    """Mirror fetch_all_platforms.yml loop (before location_filter)."""
    out = []
    for platform in all_platforms:
        if izlenmeli_mode == "monitor" and get_izlenmeli_status(platform) == "hayir":
            continue
        out.append(platform)
    return out


def build_mock_platform(
    platform_id=1,
    name="Test Platform",
    manufacturer_name="Nutanix",
    site="DC11-CLS",
    dc="DC11",
    ip="10.0.0.1",
    zabbix=True,
    izlenmeli=None,
):
    return {
        "id": platform_id,
        "name": name,
        "manufacturer": {"name": manufacturer_name},
        "custom_fields": {
            "Site": site,
            "DC": dc,
            "ip_addresses": ip,
            "Zabbix": zabbix,
            "izlenmeli": izlenmeli,
            "Port": "9440",
            "URL": "https://example.local",
        },
        "created": "2025-01-01T00:00:00+03:00",
        "last_updated": "2025-01-02T00:00:00+03:00",
    }


def extract_site_valid(site: str) -> bool:
    import re

    if not site:
        return False
    return re.search(r"(DC|AZ|ICT|UZ)[0-9]+", site, re.IGNORECASE) is not None


def normalize_dc_limit_bucket(site_code: str) -> str:
    """Mirror process_platform.yml: first (DC|AZ|ICT|UZ)[0-9]+ match, uppercased; else full string."""
    import re

    if site_code is None:
        return ""
    s = str(site_code).strip()
    if not s:
        return ""
    m = re.search(r"(DC|AZ|ICT|UZ)[0-9]+", s, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    return s


def test_normalize_dc_limit_bucket():
    assert normalize_dc_limit_bucket("DC13-G12") == "DC13"
    assert normalize_dc_limit_bucket("dc13-FC1-CLS") == "DC13"
    assert normalize_dc_limit_bucket("AZ11-CLS") == "AZ11"
    assert normalize_dc_limit_bucket("ICT21-HALL") == "ICT21"
    assert normalize_dc_limit_bucket("UZ11") == "UZ11"
    assert normalize_dc_limit_bucket("") == ""


def test_limit_per_dc_simulation_uses_normalized_bucket():
    """Same logical DC with different Site suffixes shares one counter (matches Ansible)."""
    platforms = [
        build_mock_platform(platform_id=1, site="DC13-G12"),
        build_mock_platform(platform_id=2, site="DC13-G13"),
        build_mock_platform(platform_id=3, site="DC14"),
    ]
    limit = 1
    usage = {}
    allowed_ids = []
    device_type = "Nutanix"
    for p in platforms:
        cf = p.get("custom_fields") or {}
        site = cf.get("Site") or cf.get("DC") or ""
        bucket = normalize_dc_limit_bucket(site)
        by_type = usage.setdefault(device_type, {})
        cur = by_type.get(bucket, 0)
        if limit > 0 and cur >= limit:
            continue
        by_type[bucket] = cur + 1
        allowed_ids.append(p["id"])
    assert allowed_ids == [1, 3]


def test_limit_per_dc_zero_allows_all_in_same_bucket():
    platforms = [
        build_mock_platform(platform_id=1, site="DC13-G12"),
        build_mock_platform(platform_id=2, site="DC13-G13"),
    ]
    limit = 0
    usage = {}
    allowed_ids = []
    device_type = "Nutanix"
    for p in platforms:
        cf = p.get("custom_fields") or {}
        site = cf.get("Site") or cf.get("DC") or ""
        bucket = normalize_dc_limit_bucket(site)
        by_type = usage.setdefault(device_type, {})
        cur = by_type.get(bucket, 0)
        if limit > 0 and cur >= limit:
            continue
        by_type[bucket] = cur + 1
        allowed_ids.append(p["id"])
    assert allowed_ids == [1, 2]


def extract_dc_limit(platforms, limit, dc_key="DC"):
    from collections import defaultdict

    if limit <= 0:
        return platforms

    by_dc = defaultdict(list)
    for p in platforms:
        custom_fields = p.get("custom_fields") or {}
        dc = custom_fields.get(dc_key) or ""
        by_dc[dc].append(p)

    limited = []
    for dc, items in by_dc.items():
        for p in items[:limit]:
            limited.append(p)
    return limited


def test_site_pattern_validation():
    assert extract_site_valid("DC11-CLS")
    assert extract_site_valid("AZ01-XYZ")
    assert extract_site_valid("ICT10-HALL1")
    assert extract_site_valid("uz5-room1")
    assert not extract_site_valid("ISTANBUL")
    assert not extract_site_valid("HALL-1")
    assert not extract_site_valid("")


def test_dc_limit_per_dc():
    platforms = [
        build_mock_platform(platform_id=1, dc="DC11"),
        build_mock_platform(platform_id=2, dc="DC11"),
        build_mock_platform(platform_id=3, dc="DC11"),
        build_mock_platform(platform_id=4, dc="DC12"),
        build_mock_platform(platform_id=5, dc="DC12"),
    ]

    limited = extract_dc_limit(platforms, limit=2)
    ids = sorted(p["id"] for p in limited)
    # Expect first 2 from each DC11 and DC12
    assert ids == [1, 2, 4, 5]


def test_izlenmeli_filtering_logic():
    assert get_izlenmeli_status(build_mock_platform(izlenmeli=None)) == "null"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="evet")) == "evet"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="Evet")) == "evet"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="hayir")) == "hayir"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="hayır")) == "hayir"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="no")) == "hayir"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli=False)) == "hayir"
    assert get_izlenmeli_status(build_mock_platform(izlenmeli="false")) == "hayir"


def test_monitor_list_includes_platform_when_zabbix_cf_false_if_izlenmeli_ok():
    p = build_mock_platform(platform_id=99, zabbix=False, izlenmeli=None)
    selected = select_platforms_for_mode([p], "monitor")
    assert len(selected) == 1 and selected[0]["id"] == 99


def test_monitor_list_excludes_only_hayir_not_zabbix():
    ok = build_mock_platform(platform_id=1, zabbix=False, izlenmeli=None)
    skip = build_mock_platform(platform_id=2, zabbix=True, izlenmeli="hayir")
    selected = select_platforms_for_mode([ok, skip], "monitor")
    assert [p["id"] for p in selected] == [1]


def test_skip_mode_does_not_drop_hayir_rows():
    """Skip API returns only Hayır; loop must not filter them out."""
    p = build_mock_platform(platform_id=1, zabbix=False, izlenmeli="hayir")
    selected = select_platforms_for_mode([p], "skip")
    assert len(selected) == 1


def filter_platforms_by_site_substring(platforms, location_filter: str):
    """Mirror fetch_all_platforms.yml post-fetch location_filter on custom_fields['Site']."""
    needle = location_filter.strip().lower()
    if not needle:
        return list(platforms)

    def matches(p):
        custom_fields = p.get("custom_fields") or {}
        site_val = custom_fields.get("Site")
        site_str = "" if site_val is None else str(site_val).strip().lower()
        return needle in site_str

    return [p for p in platforms if matches(p)]


def test_platform_location_filter_site_substring():
    dc13_g12 = build_mock_platform(platform_id=1, site="DC13-G12", dc="Equinix IL2")
    az11 = build_mock_platform(platform_id=2, site="AZ11-CLS", dc="Azin Telecom")
    dc14 = build_mock_platform(platform_id=3, site="DC14", dc="ANKARA KKB")
    platforms = [dc13_g12, az11, dc14]

    assert filter_platforms_by_site_substring(platforms, "") == platforms
    assert [p["id"] for p in filter_platforms_by_site_substring(platforms, "DC13")] == [1]
    assert [p["id"] for p in filter_platforms_by_site_substring(platforms, "dc13")] == [1]
    assert [p["id"] for p in filter_platforms_by_site_substring(platforms, "AZ11")] == [2]


def test_platform_mapping_yaml_has_mappings_key():
    repo_root = Path(__file__).resolve().parent.parent
    path = repo_root / "mappings" / "netbox_platform_mapping.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "mappings" in data
    assert isinstance(data["mappings"], list)
    manufacturers = {m["manufacturer"] for m in data["mappings"] if isinstance(m, dict)}
    assert "Nutanix" in manufacturers
    assert "VMware" in manufacturers

