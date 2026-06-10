#!/usr/bin/env python3
"""Apply NetBox inventory + YAML mappings -> collector targets JSON."""

import argparse
import json
import sys
from pathlib import Path

_ROLE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROLE_DIR / "module_utils"))

import yaml  # noqa: E402

from collector_core import (  # noqa: E402
    classify_platform_status,
    extract_dc_code,
    extract_device_ip,
    extract_platform_ip,
    is_valid_ip_or_host,
    is_valid_platform_site,
    match_device_mapping,
    match_platform_mapping,
    platform_manufacturer_name,
    platform_site_code,
    resolve_proxy_ids,
)


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity", choices=["platforms", "devices"], required=True)
    parser.add_argument("--inventory-file", required=True)
    parser.add_argument("--collector-types", required=True)
    parser.add_argument("--mapping-file", required=True)
    parser.add_argument("--proxy-assignment", required=True)
    parser.add_argument("--collector-filter", default="")
    parser.add_argument(
        "--platform-status-mapping",
        default="",
        help="Path to zabbix-netbox netbox_platform_mapping.yml for status classification",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--skipped-output",
        default="",
        help="Optional JSON file for unmapped/invalid platforms",
    )
    args = parser.parse_args()

    inventory = json.loads(Path(args.inventory_file).read_text(encoding="utf-8"))
    collector_types = load_yaml(args.collector_types)
    mapping_data = load_yaml(args.mapping_file)
    proxy_assignment = load_yaml(args.proxy_assignment)
    mappings = mapping_data.get("mappings", [])

    zabbix_rows: list[dict] = []
    if args.platform_status_mapping:
        status_path = Path(args.platform_status_mapping)
        if status_path.exists():
            zabbix_rows = load_yaml(str(status_path)).get("mappings", []) or []

    filt = {x.strip() for x in args.collector_filter.split(",") if x.strip()}

    targets = []
    skipped: list[dict] = []
    for item in inventory:
        if args.entity == "platforms":
            mfr = platform_manufacturer_name(item)
            site = platform_site_code(item)
            platform_status, platform_status_note = classify_platform_status(
                item, zabbix_rows
            )
            row = match_platform_mapping(mfr, item.get("name", ""), site, mappings)
            if not row:
                skipped.append(
                    {
                        "netbox_entity_id": item.get("id"),
                        "entity_name": item.get("name"),
                        "manufacturer": mfr,
                        "site": site,
                        "skip_reason": "unmapped",
                        "platform_status": platform_status,
                        "platform_status_note": platform_status_note,
                    }
                )
                continue
            if not is_valid_platform_site(site):
                skipped.append(
                    {
                        "netbox_entity_id": item.get("id"),
                        "entity_name": item.get("name"),
                        "manufacturer": mfr,
                        "site": site,
                        "skip_reason": "invalid",
                        "platform_status": platform_status,
                        "platform_status_note": platform_status_note,
                    }
                )
                continue
            ctype = row["collector_type"]
            if filt and ctype not in filt:
                continue
            meta = collector_types.get(ctype, {})
            if meta.get("source_type") != "platform":
                continue
            ip = extract_platform_ip(item)
            if not ip or not is_valid_ip_or_host(ip):
                skipped.append(
                    {
                        "netbox_entity_id": item.get("id"),
                        "entity_name": item.get("name"),
                        "manufacturer": mfr,
                        "site": site,
                        "skip_reason": "invalid",
                        "platform_status": platform_status,
                        "platform_status_note": platform_status_note,
                    }
                )
                continue
            dc = extract_dc_code(site)
            proxy_ids = resolve_proxy_ids(dc, proxy_assignment)
            for proxy_id in proxy_ids:
                targets.append(
                    {
                        "collector_type": ctype,
                        "conf_key": meta.get("conf_key", ctype),
                        "ip": ip.split("/")[0],
                        "proxy_id": proxy_id,
                        "host_entity_type": "platform",
                        "netbox_entity_id": item.get("id"),
                        "entity_name": item.get("name"),
                        "manufacturer": mfr,
                        "dc_code": dc,
                        "check_ports": meta.get("check_ports", []),
                        "platform_status": platform_status,
                        "platform_status_note": platform_status_note,
                    }
                )
        else:
            row = match_device_mapping(item, mappings)
            if not row:
                continue
            ctype = row["collector_type"]
            if filt and ctype not in filt:
                continue
            meta = collector_types.get(ctype, {})
            if meta.get("source_type") != "device":
                continue
            ip_src = row.get("ip_field_source", "primary_ip")
            ip = extract_device_ip(item, ip_src)
            if not ip or not is_valid_ip_or_host(ip):
                continue
            cf = item.get("custom_fields") or {}
            site = cf.get("Site") or cf.get("DC") or ""
            dc = extract_dc_code(site)
            proxy_ids = resolve_proxy_ids(dc, proxy_assignment)
            mfr = ""
            if item.get("device_type") and item["device_type"].get("manufacturer"):
                mfr = item["device_type"]["manufacturer"].get("name", "")
            for proxy_id in proxy_ids:
                targets.append(
                    {
                        "collector_type": ctype,
                        "conf_key": meta.get("conf_key", ctype),
                        "ip": ip.split("/")[0],
                        "proxy_id": proxy_id,
                        "host_entity_type": "device",
                        "netbox_entity_id": item.get("id"),
                        "entity_name": item.get("name"),
                        "manufacturer": mfr,
                        "dc_code": dc,
                        "check_ports": meta.get("check_ports", []),
                    }
                )

    Path(args.output).write_text(json.dumps(targets, indent=2), encoding="utf-8")
    if args.skipped_output and args.entity == "platforms":
        Path(args.skipped_output).write_text(
            json.dumps(skipped, indent=2), encoding="utf-8"
        )
    print(json.dumps({"count": len(targets), "skipped": len(skipped)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
