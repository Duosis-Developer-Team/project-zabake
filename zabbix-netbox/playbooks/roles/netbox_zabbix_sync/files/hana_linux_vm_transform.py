#!/usr/bin/env python3
"""Transform discovery_netbox_virtualization_vm rows into device-shaped sync records."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def extract_dc_code(cluster_name: str | None) -> str:
    if not cluster_name:
        return ""
    match = re.match(r"^(DC\d+)", str(cluster_name).strip(), re.IGNORECASE)
    return match.group(1).upper() if match else ""


def is_hana_linux_vm(row: dict[str, Any]) -> bool:
    name = str(row.get("name") or "")
    cluster = str(row.get("cluster_name") or "")
    guest_os = str(row.get("custom_fields_guest_os") or "")
    endpoint = str(row.get("custom_fields_endpoint") or "").strip()
    status = str(row.get("status_value") or "").lower()

    if status in ("poweredoff", "offline", "decommissioning", "failed"):
        return False
    if "IBM" not in cluster.upper():
        return False
    if "LINUX" not in guest_os.upper():
        return False
    if "hana" not in name.lower():
        return False
    return bool(endpoint)


def vm_row_to_device(row: dict[str, Any]) -> dict[str, Any]:
    cluster_name = row.get("cluster_name") or ""
    dc_code = extract_dc_code(cluster_name)
    vm_id = row.get("id")
    tenant = row.get("custom_fields_musteri") or row.get("tenant") or ""

    return {
        "id": f"vm-{vm_id}",
        "name": row.get("name") or "",
        "device_model": "Hana Linux",
        "manufacturer_name": "IBM",
        "device_role_name": "HANA VM",
        "primary_ip_address": str(row.get("custom_fields_endpoint") or "").strip(),
        "site_id": row.get("site_id"),
        "site_name": row.get("site_name") or dc_code,
        "location_id": None,
        "location_name": cluster_name,
        "location_description": row.get("cluster_description") or "",
        "location_parent_id": None,
        "location_parent_name": row.get("device_name") or "",
        "root_location_name": dc_code,
        "root_location_description": dc_code,
        "tenant_id": None,
        "tenant_name": tenant,
        "platform_id": None,
        "platform_name": None,
        "platform_parent_name": None,
        "platform_manufacturer_name": None,
        "platform_cf_dc": dc_code,
        "platform_cf_site": row.get("site_name") or "",
        "platform_cf_ip_addresses": row.get("custom_fields_endpoint") or "",
        "platform_cf_port": None,
        "platform_cf_url": None,
        "cluster_name": cluster_name,
        "custom_fields": {
            "guest_os": row.get("custom_fields_guest_os"),
            "endpoint": row.get("custom_fields_endpoint"),
            "vm_name": row.get("custom_fields_vm_name") or row.get("name"),
            "source": "discovery_netbox_virtualization_vm",
        },
        "sahiplik": None,
        "kurulum_tarihi": None,
        "izlenmeli": None,
        "zabbix_monitoring": None,
        "datalake_monitoring": None,
        "tags1_name": row.get("tags1_name"),
        "tags2_name": row.get("tags2_name"),
        "tags3_name": row.get("tags3_name"),
        "tags4_name": row.get("tags4_name"),
        "tags5_name": row.get("tags5_name"),
        "created": row.get("created"),
        "last_updated": row.get("last_updated"),
        "rack_name": None,
    }


def transform_hana_linux_vms(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for row in rows:
        if not is_hana_linux_vm(row):
            continue
        device = vm_row_to_device(row)
        name_key = str(device.get("name") or "").lower()
        if not name_key or name_key in seen_names:
            continue
        seen_names.add(name_key)
        devices.append(device)
    return devices


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: hana_linux_vm_transform.py <vm_rows.json>", file=sys.stderr)
        return 1
    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        rows = []
    devices = transform_hana_linux_vms(rows)
    print(json.dumps({"devices": devices, "count": len(devices)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
