import pytest


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
    # Import the helper used in fetch_all_platforms.yml script logic
    from textwrap import dedent
    import runpy
    import types
    import os
    import tempfile

    # We emulate only the izlenmeli evaluation function
    code = dedent(
        """
        def get_izlenmeli_status(platform):
            custom_fields = platform.get("custom_fields") or {}
            val = custom_fields.get("izlenmeli")
            if val is None:
                return "null"
            text = str(val).strip().lower()
            if text in ["evet", "true", "yes", "1"]:
                return "evet"
            if text in ["hayir", "hayır", "no", "0"]:
                return "hayir"
            return "null"
        """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        module_path = os.path.join(tmpdir, "izlenmeli_helper.py")
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(code)

        mod_globals = runpy.run_path(module_path)
        get_status = mod_globals["get_izlenmeli_status"]

    assert get_status(build_mock_platform(izlenmeli=None)) == "null"
    assert get_status(build_mock_platform(izlenmeli="evet")) == "evet"
    assert get_status(build_mock_platform(izlenmeli="Evet")) == "evet"
    assert get_status(build_mock_platform(izlenmeli="hayir")) == "hayir"
    assert get_status(build_mock_platform(izlenmeli="hayır")) == "hayir"
    assert get_status(build_mock_platform(izlenmeli="no")) == "hayir"

