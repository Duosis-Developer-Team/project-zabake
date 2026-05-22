#!/usr/bin/env python3
"""
Normalize NetBox API device dicts to datalake-flat field names used by process_device.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

_INVALID_HOSTNAME_CHARS = re.compile(r"[\t\r\n]+")
_MULTI_WHITESPACE = re.compile(r"\s{2,}")


def sanitize_hostname(name: str) -> str:
    """Normalize hostnames for Zabbix API (tab/CR/LF and repeated spaces)."""
    if not name:
        return name
    cleaned = _INVALID_HOSTNAME_CHARS.sub(" ", str(name))
    cleaned = _MULTI_WHITESPACE.sub(" ", cleaned).strip()
    return cleaned


def _nested_name(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("name") or "").strip()
    return ""


def device_role_name(device: Dict[str, Any]) -> str:
    flat = device.get("device_role_name")
    if flat:
        return str(flat).strip()
    return _nested_name(device.get("role") or device.get("device_role"))


def manufacturer_name(device: Dict[str, Any]) -> str:
    flat = device.get("manufacturer_name")
    if flat:
        return str(flat).strip()
    device_type = device.get("device_type") or {}
    if isinstance(device_type, dict):
        return _nested_name(device_type.get("manufacturer"))
    return ""


def device_model(device: Dict[str, Any]) -> str:
    flat = device.get("device_model")
    if flat:
        return str(flat).strip()
    device_type = device.get("device_type") or {}
    if isinstance(device_type, dict):
        return str(device_type.get("model") or "").strip()
    return ""


def extract_primary_ip_address(device: Dict[str, Any]) -> str:
    flat = device.get("primary_ip_address")
    if flat:
        text = str(flat).strip()
        if text:
            return text.split("/")[0] if "/" in text else text

    for key in ("primary_ip4", "primary_ip6"):
        pip = device.get(key)
        if isinstance(pip, dict):
            addr = pip.get("address") or pip.get("display") or ""
            if addr:
                text = str(addr).strip()
                return text.split("/")[0] if "/" in text else text
        elif isinstance(pip, str) and pip.strip():
            text = pip.strip()
            return text.split("/")[0] if "/" in text else text
    return ""


def build_location_root_map(locations: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Build a map from location id to root (top-level) location name.

    Standalone copy aligned with scripts/netbox_location_hierarchy.py.
    """
    parent_of: Dict[int, Optional[int]] = {}
    name_of: Dict[int, str] = {}

    for loc in locations:
        lid = loc.get("id")
        if lid is None:
            continue
        name_of[lid] = str(loc.get("name") or "").strip()
        parent = loc.get("parent")
        if isinstance(parent, dict):
            parent_of[lid] = parent.get("id")
        elif isinstance(parent, int):
            parent_of[lid] = parent
        else:
            parent_of[lid] = None

    root_cache: Dict[int, str] = {}

    def get_root(lid: int, visited: Optional[Set[int]] = None) -> str:
        if lid in root_cache:
            return root_cache[lid]
        if visited is None:
            visited = set()
        if lid in visited:
            return name_of.get(lid, "")
        visited.add(lid)
        pid = parent_of.get(lid)
        if pid is None or pid not in parent_of:
            root_cache[lid] = name_of.get(lid, "")
        else:
            root_cache[lid] = get_root(pid, visited)
        return root_cache[lid]

    return {lid: get_root(lid) for lid in name_of}


def get_location_name_flat(device: Dict[str, Any], location_filter: str = "") -> str:
    """DC_ID-style label: root_location_name -> location_parent_name -> location_name -> site_name."""
    for key in (
        "root_location_name",
        "location_parent_name",
        "location_name",
        "site_name",
    ):
        value = device.get(key)
        if value:
            return str(value).strip()

    location_obj = device.get("location")
    if isinstance(location_obj, dict):
        parent = location_obj.get("parent")
        if isinstance(parent, dict) and parent.get("name"):
            parent_name = str(parent.get("name")).strip()
            loc_name = _nested_name(location_obj)
            if location_filter:
                return location_filter.strip()
            return parent_name or loc_name

        loc_name = _nested_name(location_obj)
        if loc_name:
            if location_filter:
                return location_filter.strip()
            return loc_name

    site_name = _nested_name(device.get("site"))
    if site_name:
        return site_name

    if location_filter:
        return location_filter.strip()
    return ""


def normalize_device_record(
    device: Dict[str, Any],
    location_filter: str = "",
    location_root_map: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """Return shallow copy with flat fields for datalake-compatible processing."""
    record = dict(device)
    if record.get("name"):
        record["name"] = sanitize_hostname(str(record["name"]))
    loc_filter = (location_filter or "").strip()
    root_map = location_root_map or {}

    record["device_role_name"] = device_role_name(device)
    record["manufacturer_name"] = manufacturer_name(device)
    record["device_model"] = device_model(device)
    record["primary_ip_address"] = extract_primary_ip_address(device)

    location_obj = device.get("location")
    if isinstance(location_obj, dict):
        record["location_name"] = _nested_name(location_obj) or record.get("location_name") or ""
        parent = location_obj.get("parent")
        if isinstance(parent, dict):
            record["location_parent_name"] = _nested_name(parent) or record.get(
                "location_parent_name"
            ) or ""
        desc = location_obj.get("description")
        if desc:
            record["location_description"] = str(desc).strip()
    elif not record.get("location_name"):
        record["location_name"] = ""

    site_obj = device.get("site")
    if isinstance(site_obj, dict):
        record["site_name"] = _nested_name(site_obj) or record.get("site_name") or ""

    tenant_obj = device.get("tenant")
    if isinstance(tenant_obj, dict):
        record["tenant_name"] = _nested_name(tenant_obj) or record.get("tenant_name") or ""

    rack_obj = device.get("rack")
    if isinstance(rack_obj, dict):
        record["rack_name"] = _nested_name(rack_obj) or record.get("rack_name") or ""

    record["location_name"] = record.get("location_name") or ""
    record["location_parent_name"] = record.get("location_parent_name") or ""

    if loc_filter:
        record["root_location_name"] = loc_filter
    else:
        resolved_root = ""
        location_obj_for_root = device.get("location")
        if isinstance(location_obj_for_root, dict) and root_map:
            loc_id = location_obj_for_root.get("id")
            if loc_id is not None and loc_id in root_map:
                resolved_root = root_map[loc_id]
        elif isinstance(location_obj_for_root, int) and root_map:
            if location_obj_for_root in root_map:
                resolved_root = root_map[location_obj_for_root]
        if resolved_root:
            record["root_location_name"] = resolved_root
        elif not record.get("root_location_name"):
            record["root_location_name"] = (
                record.get("location_parent_name")
                or record.get("location_name")
                or record.get("site_name")
                or ""
            )

    cf = record.get("custom_fields")
    if cf is None:
        record["custom_fields"] = {}
    elif not isinstance(cf, dict):
        record["custom_fields"] = {}

    if not record.get("sahiplik"):
        sahiplik = (record.get("custom_fields") or {}).get("Sahiplik")
        if sahiplik is not None:
            record["sahiplik"] = sahiplik

    return record
