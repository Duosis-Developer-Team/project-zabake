#!/usr/bin/env python3
"""
Normalize NetBox API device dicts to datalake-flat field names used by process_device.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


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
    device: Dict[str, Any], location_filter: str = ""
) -> Dict[str, Any]:
    """Return shallow copy with flat fields for datalake-compatible processing."""
    record = dict(device)
    loc_filter = (location_filter or "").strip()

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
