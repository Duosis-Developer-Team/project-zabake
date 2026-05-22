#!/usr/bin/env python3
"""
Parallel Compare Engine for Zabbix-NetBox sync.

Performs Phase A (compare, no Zabbix writes) in parallel for devices,
platforms, and virtual firewalls using ThreadPoolExecutor.

Outputs one JSON-line per item to stdout (AWX-visible stream) and writes
plan files to --output-dir:
  device_plan_<id>.json       — consumed by process_device_apply.yml
  platform_plan_<id>.json     — consumed by process_platform_apply.yml
  vfw_plan_<id>.json          — consumed by process_virtual_fw_apply.yml

A final aggregate compare_summary.json is written on completion.

Exit codes:
  0 — all items compared successfully (some may have action=skip)
  1 — one or more items raised an unhandled exception during compare
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Hostname / filter helpers (from filter_plugins/zabbix_hostname.py)
# ---------------------------------------------------------------------------

_MAX_HOST_LEN = 128
_TR_MAP = str.maketrans(
    {
        "ı": "i", "İ": "I", "ş": "s", "Ş": "S",
        "ğ": "g", "Ğ": "G", "ü": "u", "Ü": "U",
        "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
    }
)


def _truncate_and_sanitize(s: str) -> str:
    if not s:
        return ""
    s = s[:_MAX_HOST_LEN]
    s = re.sub(r"_+", "_", s).strip("._-")
    return s


def zabbix_technical_hostname(text: Any, fallback_id: str = "") -> str:
    raw = str(text or "").strip()
    if not raw:
        fb = str(fallback_id).strip() if fallback_id else ""
        if fb:
            low = fb.lower()
            if low.startswith("host-") or low.startswith("p"):
                return _truncate_and_sanitize(fb)
            return _truncate_and_sanitize(f"host-{fb}")
        return "host"
    step1 = raw.translate(_TR_MAP)
    nfkd = unicodedata.normalize("NFKD", step1)
    ascii_buf = [ch for ch in nfkd if unicodedata.category(ch) != "Mn"]
    merged = "".join(ascii_buf)
    safe = []
    for ch in merged:
        if ch.isalnum() or ch in "._-":
            safe.append(ch)
        else:
            safe.append("_")
    slug = re.sub(r"_+", "_", "".join(safe)).strip("._-")
    slug = _truncate_and_sanitize(slug)
    if not slug:
        fb = str(fallback_id).strip() if fallback_id else ""
        slug = _truncate_and_sanitize(f"host-{fb}") if fb else "host"
    return slug


def zabbix_platform_technical_hostname(text: Any, platform_id: str = "") -> str:
    sid = str(platform_id).strip() if platform_id else ""
    suffix = f"_P_{sid}" if sid else ""
    base = zabbix_technical_hostname(text, "")
    if not suffix:
        return base or "host"
    if not base:
        return zabbix_technical_hostname("", f"P_{sid}")
    if base.lower().endswith(suffix.lower()):
        return _truncate_and_sanitize(base)[:_MAX_HOST_LEN]
    max_base = _MAX_HOST_LEN - len(suffix)
    truncated = base[:max(max_base, 1)].rstrip("._-")
    if not truncated:
        return zabbix_technical_hostname("", f"P_{sid}")
    return _truncate_and_sanitize(truncated + suffix)[:_MAX_HOST_LEN]


def zabbix_vfw_technical_hostname(text: Any, vfw_id: str = "") -> str:
    sid = str(vfw_id).strip() if vfw_id else ""
    suffix = f"_VFW_{sid}" if sid else ""
    base = zabbix_technical_hostname(text, "")
    if not suffix:
        return base or "host"
    if not base:
        return zabbix_technical_hostname("", f"VFW_{sid}")
    if base.lower().endswith(suffix.lower()):
        return _truncate_and_sanitize(base)[:_MAX_HOST_LEN]
    max_base = _MAX_HOST_LEN - len(suffix)
    truncated = base[:max(max_base, 1)].rstrip("._-")
    if not truncated:
        return zabbix_technical_hostname("", f"VFW_{sid}")
    return _truncate_and_sanitize(truncated + suffix)[:_MAX_HOST_LEN]


def zabbix_vfw_display_name(hostname_raw: Any) -> str:
    raw = str(hostname_raw or "").strip()
    if not raw:
        return ""
    suffix = " - Firewall"
    return raw if raw.endswith(suffix) else raw + suffix


def vfw_hostname_prefix_hostgroup(hostname_raw: Any) -> str:
    s = str(hostname_raw or "").strip()
    if "-" not in s:
        return ""
    first = s.split("-", 1)[0].strip()
    return first.title() if first else ""


def parse_virtual_fw_ip_port(value: Any) -> Dict[str, str]:
    s = str(value or "").strip()
    if not s:
        return {"ip": "", "port": ""}
    if ":" not in s:
        return {"ip": s, "port": ""}
    host_part, rest = s.split(":", 1)
    rest = rest.strip()
    if rest.isdigit() and host_part.strip():
        return {"ip": host_part.strip(), "port": rest}
    return {"ip": s, "port": ""}


def virtual_fw_mapping_match(entries: List[Dict], vendor_name: str = "", model_name: str = "") -> Dict:
    vn = (vendor_name or "").strip().lower()
    ml = (model_name or "").strip().lower()
    for e in (entries or []):
        if not isinstance(e, dict):
            continue
        if str(e.get("vendor", "")).strip().lower() != vn:
            continue
        prefix = e.get("model_prefix")
        suffix = e.get("model_suffix")
        ok = True
        if prefix and str(prefix).strip() and not ml.startswith(str(prefix).strip().lower()):
            ok = False
        if ok and suffix and str(suffix).strip() and not ml.endswith(str(suffix).strip().lower()):
            ok = False
        if ok:
            return e
    return {}


# ---------------------------------------------------------------------------
# Device processing helpers (extracted from process_device.yml inline script)
# ---------------------------------------------------------------------------

def _nested_name(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("name") or "").strip()
    return ""


def _device_role_name(device: Dict) -> str:
    flat = device.get("device_role_name")
    if flat:
        return str(flat).strip()
    return _nested_name(device.get("role") or device.get("device_role"))


def _manufacturer_name(device: Dict) -> str:
    flat = device.get("manufacturer_name")
    if flat:
        return str(flat).strip()
    dt = device.get("device_type") or {}
    if isinstance(dt, dict):
        return _nested_name(dt.get("manufacturer"))
    return ""


def _device_model(device: Dict) -> str:
    flat = device.get("device_model")
    if flat:
        return str(flat).strip()
    dt = device.get("device_type") or {}
    return str(dt.get("model") or "").strip() if isinstance(dt, dict) else ""


def _extract_primary_ip(device: Dict) -> str:
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


def _get_location_name(device: Dict) -> str:
    flat = (
        device.get("root_location_name") or
        device.get("location_parent_name") or
        device.get("location_name") or
        device.get("site_name") or ""
    )
    if flat:
        return str(flat).strip()
    location_obj = device.get("location")
    if isinstance(location_obj, dict):
        parent = location_obj.get("parent")
        if isinstance(parent, dict) and parent.get("name"):
            return str(parent["name"]).strip()
        name = location_obj.get("name")
        if name:
            return str(name).strip()
    site_obj = device.get("site")
    if isinstance(site_obj, dict) and site_obj.get("name"):
        return str(site_obj["name"]).strip()
    return ""


def _extract_by_path(obj: Any, path: str) -> Any:
    if not obj or not path:
        return None
    current = obj
    for key in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def _extract_by_path_with_fallback(obj: Any, path: str, fallback: Any = None) -> Any:
    value = _extract_by_path(obj, path)
    if value is not None and value != "":
        return value
    if fallback:
        fallback_paths = [fallback] if isinstance(fallback, str) else fallback
        for fp in fallback_paths:
            value = _extract_by_path(obj, fp)
            if value is not None and value != "":
                return value
    return None


def _check_condition(device: Dict, key: str, value: Any) -> bool:
    if key == "device_role":
        role = _device_role_name(device).upper()
        if isinstance(value, list):
            return role in [v.upper() for v in value]
        return role == str(value).upper()
    elif key == "manufacturer":
        mfr = _manufacturer_name(device).upper()
        if isinstance(value, list):
            return mfr in [v.upper() for v in value]
        return mfr == str(value).upper()
    elif key == "model_contains":
        model = _device_model(device).upper()
        if isinstance(value, list):
            return any(str(v).upper() in model for v in value)
        return str(value).upper() in model
    elif key == "model_suffix":
        model = _device_model(device).upper()
        if isinstance(value, list):
            return any(model.endswith(str(v).upper()) for v in value)
        return model.endswith(str(value).upper())
    elif key == "name_contains":
        name = (device.get("name") or "").upper()
        if isinstance(value, list):
            return any(str(v).upper() in name for v in value)
        return str(value).upper() in name
    return False


def _resolve_device_tenant_name(device: Dict) -> str:
    """
    Resolve NetBox tenant label from nested tenant object or flat tenant_name (datalake/Loki).
    Empty tenant dict must not hide a valid flat tenant_name field.
    """
    tenant_obj = device.get("tenant")
    if isinstance(tenant_obj, dict):
        name = (tenant_obj.get("name") or "").strip()
        if name:
            return name
    return (device.get("tenant_name") or "").strip()


def _mapping_tenant_allowlist(mapping: Dict) -> Optional[List[str]]:
    if "tenants" in mapping and mapping.get("tenants") is not None:
        raw = mapping["tenants"]
        if isinstance(raw, list):
            names = [str(x).strip() for x in raw if x is not None and str(x).strip()]
        else:
            names = [str(raw).strip()] if str(raw).strip() else []
        return names if names else None
    t1 = mapping.get("tenant")
    if t1 is not None and str(t1).strip():
        return [str(t1).strip()]
    return None


def _mapping_applies_for_tenant(device: Dict, mapping: Dict) -> bool:
    allow = _mapping_tenant_allowlist(mapping)
    if not allow:
        return True
    dev_name = _resolve_device_tenant_name(device)
    if not dev_name:
        return False
    dev_u = dev_name.upper()
    return any(n.strip().upper() == dev_u for n in allow)


def _mapping_is_tenant_scoped(mapping: Dict) -> bool:
    return _mapping_tenant_allowlist(mapping) is not None


def _device_type_mapping_without_tenant_scope(
    device_type_mapping: Dict, excluded_tenant_labels: List[str]
) -> Dict:
    excluded = {str(t).strip().upper() for t in excluded_tenant_labels if str(t).strip()}
    filtered = []
    for mapping in device_type_mapping.get("mappings", []):
        allow = _mapping_tenant_allowlist(mapping)
        if allow and any(label in excluded for label in (a.upper() for a in allow)):
            continue
        filtered.append(mapping)
    return {"mappings": filtered}


def _find_matching_mapping(device: Dict, device_type_mapping: Dict) -> Optional[Dict]:
    mappings = device_type_mapping.get("mappings", [])
    for mapping in sorted(mappings, key=lambda x: x.get("priority", 999)):
        if not _mapping_applies_for_tenant(device, mapping):
            continue
        conditions = mapping.get("conditions", {})
        if all(_check_condition(device, k, v) for k, v in conditions.items()):
            return mapping
    return None


def _find_matching_mapping_safe(device: Dict, device_type_mapping: Dict) -> Optional[Dict]:
    """
    Pick device_type mapping; if a tenant-scoped row matched without tenant proof, retry without it.
    Prevents HPE HOST -> HPE IPMI Moneygram when tenant_name is missing/wrong on empty tenant dict.
    """
    matching = _find_matching_mapping(device, device_type_mapping)
    if not matching or not _mapping_is_tenant_scoped(matching):
        return matching
    allow = _mapping_tenant_allowlist(matching) or []
    dev_tenant = _resolve_device_tenant_name(device).upper()
    if dev_tenant and any(a.strip().upper() == dev_tenant for a in allow):
        return matching
    stripped = _device_type_mapping_without_tenant_scope(device_type_mapping, allow)
    return _find_matching_mapping(device, stripped)


def _extract_host_groups_from_config(
    device: Dict, config: Optional[Dict], device_type: Optional[str], templates: List[Dict]
) -> str:
    groups: List[str] = []
    if config is None:
        if device_type:
            groups.append(device_type)
        loc = _get_location_name(device)
        if loc:
            groups.append(loc)
        sahiplik = device.get("sahiplik") or (device.get("custom_fields") or {}).get("Sahiplik", "")
        if sahiplik:
            groups.append(str(sahiplik).strip())
        return ",".join(g for g in groups if g)

    sources = config.get("host_groups", {}).get("sources", [])
    settings = config.get("host_groups", {}).get("settings", {})
    for source in sorted(sources, key=lambda x: x.get("priority", 999)):
        if not source.get("enabled", True):
            continue
        stype = source.get("type")
        value = None
        if stype == "mapping_result":
            value = device_type
        elif stype == "netbox_attribute":
            value = _extract_by_path_with_fallback(device, source.get("path", ""), source.get("fallback"))
        elif stype == "custom_field":
            value = (device.get("custom_fields") or {}).get(source.get("field_name"))
        elif stype == "computed" and source.get("compute_function") == "get_location_name":
            value = _get_location_name(device)
        elif stype == "template_mapping":
            attr = source.get("attribute", "host_groups")
            tg = []
            for t in templates:
                if attr in t:
                    tg.extend(t.get(attr, []))
            if tg:
                groups.extend(tg)
                continue
        if value and str(value) != "":
            if settings.get("trim", True) and isinstance(value, str):
                value = value.strip()
            groups.append(str(value))

    if settings.get("unique", True):
        seen: set = set()
        unique_groups: List[str] = []
        for g in groups:
            if g not in seen:
                seen.add(g)
                unique_groups.append(g)
        groups = unique_groups
    if settings.get("skip_empty", True):
        groups = [g for g in groups if g]
    return settings.get("separator", ",").join(groups)


def _extract_tags_original(device: Dict) -> Tuple[Dict, List]:
    tags: Dict = {}
    loki_tags: List = []
    if device.get("manufacturer_name"):
        tags["Manufacturer"] = device["manufacturer_name"]
    if device.get("device_model"):
        tags["Device_Type"] = device["device_model"]
    loc = device.get("location_name") or ""
    site = device.get("site_name") or ""
    if loc:
        tags["Location_Detail"] = loc
    elif site:
        tags["Location_Detail"] = site
    if site:
        tags["City"] = site
    if device.get("tenant_name"):
        tags["Tenant"] = device["tenant_name"]
    sahiplik = device.get("sahiplik") or (device.get("custom_fields") or {}).get("Sahiplik", "") or ""
    if sahiplik:
        tags["Contact"] = str(sahiplik).strip()
    cf = device.get("custom_fields") or {}
    if cf.get("Sorumlu_Ekip"):
        tags["Sorumlu_Ekip"] = cf["Sorumlu_Ekip"]
    if device.get("id"):
        tags["Loki_ID"] = str(device["id"])
    if device.get("cluster_name"):
        tags["Cluster"] = device["cluster_name"]
    if device.get("rack_name"):
        tags["Rack_Name"] = device["rack_name"]
    loc_desc = device.get("location_description") or ""
    if loc_desc:
        tags["Hall"] = loc_desc
    elif loc:
        tags["Hall"] = loc
    kurulum = device.get("kurulum_tarihi") or cf.get("Kurulum_Tarihi") or ""
    if kurulum:
        tags["Kurulum_Tarihi"] = str(kurulum)
    for tf in ["tags1_name", "tags2_name", "tags3_name", "tags4_name", "tags5_name"]:
        tv = device.get(tf)
        if tv:
            loki_tags.append(str(tv))
    return {k: v for k, v in tags.items() if v is not None and v != ""}, loki_tags


def _extract_tags_from_config(
    device: Dict, config: Optional[Dict], device_type: Optional[str] = None, templates: Optional[List] = None
) -> Tuple[Dict, List]:
    if config is None:
        return _extract_tags_original(device)
    tags: Dict = {}
    loki_tags: List = []
    definitions = config.get("tags", {}).get("definitions", [])
    settings = config.get("tags", {}).get("settings", {})
    for tag_def in definitions:
        if not tag_def.get("enabled", True):
            continue
        tag_name = tag_def.get("tag_name")
        stype = tag_def.get("source_type")
        value = None
        if stype == "netbox_attribute":
            value = _extract_by_path_with_fallback(device, tag_def.get("path", ""), tag_def.get("fallback"))
            if tag_def.get("transform") == "to_string" and value is not None:
                value = str(value)
        elif stype == "custom_field":
            value = (device.get("custom_fields") or {}).get(tag_def.get("field_name"))
        elif stype == "computed":
            compute_func = tag_def.get("compute_function")
            if compute_func == "extract_hall":
                value = device.get("location_description") or device.get("location_name") or None
            elif compute_func == "get_location_name":
                value = _get_location_name(device)
        elif stype == "mapping_result":
            value = device_type
        elif stype == "template_mapping" and templates:
            attr = tag_def.get("attribute", "host_groups")
            tg = []
            for t in templates:
                if attr in t:
                    tg.extend(t.get(attr, []))
            if tg:
                sep = tag_def.get("separator", ",")
                value = sep.join(str(x) for x in tg)
        elif stype == "array_expansion":
            path = tag_def.get("path")
            prefix = tag_def.get("prefix", "")
            if path == "tags":
                tag_values = [device.get(f"tags{i}_name") for i in range(1, 6) if device.get(f"tags{i}_name")]
            else:
                raw = _extract_by_path(device, path or "")
                tag_values = []
                if raw and isinstance(raw, list):
                    for item in raw:
                        n = item.get("name") if isinstance(item, dict) else (item if isinstance(item, str) else None)
                        if n:
                            tag_values.append(n)
            for item_name in tag_values:
                item_name = str(item_name)
                loki_tags.append(item_name)
                tags[f"{prefix}{item_name}"] = item_name
            continue
        if value is not None and value != "":
            if settings.get("trim", True) and isinstance(value, str):
                value = value.strip()
            if settings.get("treat_empty_as_none", True) and value == "":
                continue
            tags[tag_name] = value
    if settings.get("skip_none", True):
        tags = {k: v for k, v in tags.items() if v is not None}
    if settings.get("skip_empty", True):
        tags = {k: v for k, v in tags.items() if v != ""}
    return tags, loki_tags


def _sanitize_hostname(name: str) -> str:
    if not name:
        return name
    cleaned = re.sub(r"[\t\r\n]+", " ", str(name))
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def _normalize_netbox_choice(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list) and len(value) > 0:
        return str(value[0]).strip()
    return str(value).strip()


def process_device_info(
    device: Dict,
    device_type_mapping: Dict,
    host_groups_config: Optional[Dict],
    tags_config: Optional[Dict],
    templates_map: Optional[Dict],
) -> Dict:
    """Run the device processing logic (equivalent to netbox_device_processor.py)."""
    matching_mapping = _find_matching_mapping_safe(device, device_type_mapping)
    device_type = matching_mapping.get("device_type") if matching_mapping else None
    hostname_prefix = (matching_mapping.get("hostname_prefix") or "") if matching_mapping else ""
    hostname_suffix = (matching_mapping.get("hostname_suffix") or "") if matching_mapping else ""

    templates: List[Dict] = []
    if templates_map and device_type and device_type in templates_map:
        templates = templates_map[device_type]

    location_name = _get_location_name(device)
    site_name = (device.get("site_name") or "").strip()

    host_groups_str = _extract_host_groups_from_config(device, host_groups_config, device_type, templates)
    tags_dict, loki_tags_list = _extract_tags_from_config(device, tags_config, device_type, templates)

    if tags_config is None:
        for loki_tag in loki_tags_list:
            if loki_tag:
                tags_dict[f"Loki_Tag_{loki_tag}"] = loki_tag

    device_role = device.get("device_role_name") or _device_role_name(device) or ""
    tenant_name = (device.get("tenant_name") or "").strip()
    sahiplik = device.get("sahiplik") or ""
    if not sahiplik:
        sahiplik = _normalize_netbox_choice((device.get("custom_fields") or {}).get("Sahiplik"))

    return {
        "device_type": device_type,
        "device_role": device_role,
        "primary_ip": _extract_primary_ip(device),
        "host_groups": host_groups_str,
        "tags": tags_dict,
        "loki_tags": loki_tags_list,
        "location": location_name,
        "dc_id": location_name if location_name else site_name,
        "tenant": tenant_name,
        "site": site_name,
        "ownership": sahiplik,
        "hostname_prefix": hostname_prefix,
        "hostname_suffix": hostname_suffix,
        "rack_name": device.get("rack_name") or "",
    }


# ---------------------------------------------------------------------------
# Zabbix host resolution helpers
# ---------------------------------------------------------------------------

def _resolve_existing_host(
    loki_key: str,
    technical_hostname: str,
    visible_name: Optional[str],
    by_loki: Dict,
    by_hostname: Dict,
    by_visible: Dict,
) -> Dict:
    """Resolve existing Zabbix host via Loki_ID → hostname → visible name."""
    if loki_key and loki_key in by_loki:
        h = by_loki[loki_key]
        if isinstance(h, dict) and h.get("hostid"):
            return h
    if technical_hostname and technical_hostname in by_hostname:
        h = by_hostname[technical_hostname]
        if isinstance(h, dict) and h.get("hostid"):
            return h
    if visible_name and visible_name in by_visible:
        h = by_visible[visible_name]
        if isinstance(h, dict) and h.get("hostid"):
            return h
    return {}


# ---------------------------------------------------------------------------
# Per-item compare functions
# ---------------------------------------------------------------------------

def compare_one_device(
    device: Dict,
    ctx: Dict,
) -> Dict:
    """
    Compare a single NetBox device against Zabbix. Returns a plan dict
    compatible with process_device_apply.yml.
    """
    device_id = device.get("id", "unknown")
    device_name = _sanitize_hostname(str(device.get("name") or ""))

    # Device info (mapping + tags + host groups)
    device_info = process_device_info(
        device,
        ctx["device_type_mapping"],
        ctx.get("host_groups_config"),
        ctx.get("tags_config"),
        ctx.get("templates_map"),
    )

    # Skip checks
    if not device_info.get("device_type"):
        result = {
            "hostname": device_name or "N/A",
            "device_role": device_info.get("device_role", "N/A"),
            "status": "eklenemedi",
            "reason": "Device type bulunamadı",
            "ip": device_info.get("primary_ip") or "N/A",
            "location": device_info.get("location") or "N/A",
            "site": device_info.get("site") or "N/A",
            "tenant": device_info.get("tenant") or "N/A",
            "ownership": device_info.get("ownership") or "N/A",
        }
        return {
            "action": "skip",
            "device_id": device_id,
            "zbx_record": {},
            "zbx_existing_host": {},
            "zbx_scenario": "skip",
            "device_info": device_info,
            "current_device_result": result,
            "netbox_device_name": device_name,
        }

    if not device_info.get("primary_ip"):
        result = {
            "hostname": device_name or "N/A",
            "device_role": device_info.get("device_role", "N/A"),
            "status": "eklenemedi",
            "reason": "IP adresi bulunamadı",
            "ip": "N/A",
            "location": device_info.get("location") or "N/A",
            "site": device_info.get("site") or "N/A",
            "tenant": device_info.get("tenant") or "N/A",
            "ownership": device_info.get("ownership") or "N/A",
        }
        return {
            "action": "skip",
            "device_id": device_id,
            "zbx_record": {},
            "zbx_existing_host": {},
            "zbx_scenario": "skip",
            "device_info": device_info,
            "current_device_result": result,
            "netbox_device_name": device_name,
        }

    # Build Zabbix hostname
    prefix = str(device_info.get("hostname_prefix") or "")
    suffix = str(device_info.get("hostname_suffix") or "")
    zabbix_hostname = (prefix + device_name + suffix).strip()

    # Build zbx_record
    zbx_record = {
        "DEVICE_TYPE": device_info["device_type"],
        "DEVICE_ROLE": device_info.get("device_role", "N/A"),
        "HOST_IP": device_info["primary_ip"],
        "HOSTNAME": zabbix_hostname,
        "HOST_VISIBLE_NAME": zabbix_hostname,
        "HOST_STATUS": 0 if not ctx.get("create_devices_disabled", False) else 1,
        "LOKI_DEVICE_ID": str(device_id),
        "DC_ID": device_info.get("location", ""),
        "HOST_GROUPS": device_info.get("host_groups", ""),
        "TEMPLATE_TYPE": "",
        "MACROS": json.dumps(device_info.get("tags", {})),
        "REPORT_LOCATION": device_info.get("location", ""),
        "REPORT_SITE": device_info.get("site", ""),
        "REPORT_TENANT": device_info.get("tenant", ""),
        "REPORT_OWNERSHIP": device_info.get("ownership", ""),
    }

    # Resolve existing host
    loki_key = str(device_info.get("tags", {}).get("Loki_ID", ""))
    zbx_existing = _resolve_existing_host(
        loki_key,
        zabbix_hostname,
        zabbix_hostname,
        ctx.get("by_loki", {}),
        ctx.get("by_hostname", {}),
        ctx.get("by_visible", {}),
    )

    zbx_scenario = "update" if zbx_existing.get("hostid") else "create"
    action = zbx_scenario  # create or update

    current_result: Dict = {}

    return {
        "action": action,
        "device_id": device_id,
        "zbx_record": zbx_record,
        "zbx_existing_host": zbx_existing,
        "zbx_scenario": zbx_scenario,
        "device_info": device_info,
        "current_device_result": current_result,
        "netbox_device_name": device_name,
    }


def compare_one_platform(
    platform: Dict,
    ctx: Dict,
) -> Dict:
    """
    Compare a single NetBox platform against Zabbix. Returns a plan dict
    compatible with process_platform_apply.yml.
    """
    platform_id = str(platform.get("id", "unknown"))
    platform_name = str(platform.get("name") or platform.get("display") or "Unknown Platform")
    custom_fields = platform.get("custom_fields") or {}
    manufacturer_name = ""
    mfr = platform.get("manufacturer")
    if isinstance(mfr, dict):
        manufacturer_name = (mfr.get("name") or "").strip()

    platform_ip = str(custom_fields.get("ip_addresses") or "").strip()
    platform_port = str(custom_fields.get("Port") or "").strip()
    platform_url = str(custom_fields.get("URL") or "").strip()
    platform_site = str(custom_fields.get("Site") or "").strip()
    platform_dc = str(custom_fields.get("DC") or "").strip()
    platform_site_code = platform_site or platform_dc

    def _skip_result(reason: str) -> Dict:
        return {
            "action": "skip",
            "platform_id": platform_id,
            "zbx_record": {},
            "zbx_existing_host": {},
            "zbx_scenario": "skip",
            "current_platform_result": {
                "hostname": platform_name,
                "device_role": "PLATFORM",
                "status": "eklenemedi",
                "reason": reason,
                "ip": platform_ip or "N/A",
                "location": platform_dc or platform_site_code or "N/A",
                "site": platform_site_code or "N/A",
                "tenant": "N/A",
                "ownership": "N/A",
            },
        }

    # Check izlenmeli
    izlenmeli_raw = custom_fields.get("izlenmeli") or custom_fields.get("monitor_edilmeli_mi")
    if izlenmeli_raw is not None:
        val = izlenmeli_raw
        if isinstance(val, list) and val:
            val = val[0]
        txt = str(val).lower()
        if txt in ("hayir", "hayır", "no", "0", "false"):
            return {
                "action": "skip",
                "platform_id": platform_id,
                "zbx_record": {},
                "zbx_existing_host": {},
                "zbx_scenario": "skip",
                "current_platform_result": {
                    "hostname": platform_name,
                    "device_role": "PLATFORM",
                    "status": "atlandı",
                    "reason": "İzlenmeyecek olarak işaretli",
                    "ip": platform_ip or "N/A",
                    "location": platform_dc or platform_site_code or "N/A",
                    "site": platform_site_code or "N/A",
                    "tenant": "N/A",
                    "ownership": "N/A",
                },
            }

    # Validate site pattern
    dc_pattern = re.search(r"(DC|AZ|ICT|UZ)\d+", platform_site_code, re.IGNORECASE)
    if not dc_pattern:
        return _skip_result(f"Standart dışı site kodu: {platform_site_code or 'N/A'}")

    # Validate IP
    if not platform_ip:
        return _skip_result("IP address is missing on platform")

    # Find mapping
    platform_mapping = ctx.get("platform_mapping", {})
    mapping_entry = None
    candidates = [
        m for m in platform_mapping.get("mappings", [])
        if isinstance(m, dict) and str(m.get("manufacturer", "")).lower() == manufacturer_name.lower()
    ]
    candidates_sorted = sorted(candidates, key=lambda x: x.get("priority", 999))
    for m in candidates_sorted:
        name_lower = platform_name.lower()
        site_lower = platform_site_code.lower()
        nc = str(m.get("name_contains") or "").lower()
        sc = str(m.get("site_contains") or "").lower()
        name_match = not nc or nc in name_lower
        site_match = not sc or sc in site_lower
        logic = str(m.get("match_logic") or "and").lower()
        if (logic == "or" and (name_match or site_match)) or (logic != "or" and name_match and site_match):
            mapping_entry = m
            break

    if not mapping_entry:
        return _skip_result(f"No platform mapping found for manufacturer {manufacturer_name}")

    device_type = mapping_entry.get("device_type")
    templates_map = ctx.get("templates_map") or {}
    templates = templates_map.get(device_type, [])

    if not templates:
        return _skip_result(f"No templates found for device_type {device_type}")

    host_groups_csv = ",".join(
        list(dict.fromkeys(
            g for t in templates for g in t.get("host_groups", []) if g
        ))
    )

    platform_tags = {
        "IP": platform_ip,
        "Port": platform_port,
        "URL": platform_url,
        "Site": platform_site_code,
        "DC": platform_dc,
        "Manufacturer": manufacturer_name,
        "Created": str(platform.get("created") or ""),
        "Last_Updated": str(platform.get("last_updated") or ""),
        "Loki_Platform_ID": platform_id,
        "Loki_ID": f"P_{platform_id}",
    }

    technical_hostname = zabbix_platform_technical_hostname(platform_name, platform_id)
    zbx_record = {
        "DEVICE_TYPE": device_type,
        "DEVICE_ROLE": "PLATFORM",
        "HOST_IP": platform_ip,
        "HOSTNAME": technical_hostname,
        "HOST_VISIBLE_NAME": platform_name,
        "DC_ID": platform_site_code,
        "HOST_GROUPS": host_groups_csv,
        "TEMPLATE_TYPE": "",
        "HOST_STATUS": 1 if ctx.get("create_platforms_disabled", False) else 0,
        "MACROS": json.dumps(platform_tags),
        "REPORT_LOCATION": platform_dc or platform_site_code,
        "REPORT_SITE": platform_site_code,
        "REPORT_TENANT": "",
        "REPORT_OWNERSHIP": "",
    }

    # Resolve existing host: P_<id> Loki_ID → canonical technical hostname
    loki_key = f"P_{platform_id}"
    zbx_existing = _resolve_existing_host(
        loki_key,
        technical_hostname,
        platform_name,
        ctx.get("by_loki", {}),
        ctx.get("by_hostname", {}),
        ctx.get("by_visible", {}),
    )

    # Canonical host override: if Loki_ID host has different hostname and canonical exists
    if zbx_existing.get("hostid") and zbx_existing.get("host", "") != technical_hostname:
        canonical = ctx.get("by_hostname", {}).get(technical_hostname)
        if isinstance(canonical, dict) and canonical.get("hostid"):
            zbx_existing = canonical

    zbx_scenario = "update" if zbx_existing.get("hostid") else "create"

    return {
        "action": zbx_scenario,
        "platform_id": platform_id,
        "zbx_record": zbx_record,
        "zbx_existing_host": zbx_existing,
        "zbx_scenario": zbx_scenario,
        "current_platform_result": {},
    }


def compare_one_vfw(
    vfw: Dict,
    ctx: Dict,
) -> Dict:
    """
    Compare a single virtual firewall against Zabbix. Returns a plan dict
    compatible with process_virtual_fw_apply.yml.
    """
    vfw_id = str(vfw.get("id", "unknown"))
    hostname_raw = str(vfw.get("hostname") or "").strip()
    ip_port_raw = str(vfw.get("ip_port") or "").strip()

    vendor_obj = vfw.get("vendor")
    vendor_name = (vendor_obj.get("name") or "").strip() if isinstance(vendor_obj, dict) else ""

    mfr_model = vfw.get("manufacturer_model")
    model_name = ""
    manufacturer_name = ""
    if isinstance(mfr_model, dict):
        model_name = str(mfr_model.get("model") or "").strip()
        mfr = mfr_model.get("manufacturer")
        if isinstance(mfr, dict):
            manufacturer_name = str(mfr.get("name") or "").strip()

    lokasyon_obj = vfw.get("lokasyon") or {}
    location_name = str(lokasyon_obj.get("name") or "").strip() if isinstance(lokasyon_obj, dict) else ""
    proje = str(vfw.get("proje") or "").strip()
    fw_status = str(vfw.get("fw_status") or "").strip()

    hostname_visible = zabbix_vfw_display_name(hostname_raw)
    name_prefix_hostgroup = vfw_hostname_prefix_hostgroup(hostname_raw)

    ip_port_parsed = parse_virtual_fw_ip_port(ip_port_raw)
    host_ip = ip_port_parsed.get("ip", "")
    mgmt_port = ip_port_parsed.get("port", "")

    def _skip_result(reason: str) -> Dict:
        return {
            "action": "skip",
            "vfw_id": vfw_id,
            "zbx_record": {},
            "zbx_existing_host": {},
            "zbx_scenario": "skip",
            "current_vfw_result": {
                "hostname": hostname_visible or hostname_raw or "N/A",
                "device_role": "VIRTUAL_FW",
                "status": "eklenemedi",
                "reason": reason,
                "ip": host_ip or "N/A",
                "location": location_name or "N/A",
                "site": location_name or "N/A",
                "tenant": "N/A",
                "ownership": "N/A",
            },
        }

    if not host_ip:
        return _skip_result("IP address is missing or invalid in ip_port")
    if not vendor_name:
        return _skip_result("Vendor is missing on virtual firewall record")
    if not location_name:
        return _skip_result("Location (lokasyon) is missing on virtual firewall record")

    # Find mapping
    vfw_mapping = ctx.get("vfw_mapping") or {}
    mapping_entry = virtual_fw_mapping_match(vfw_mapping.get("mappings", []), vendor_name, model_name)
    if not mapping_entry or not mapping_entry.get("device_type"):
        return _skip_result(f"No virtual_fw_mapping.yml entry for vendor={vendor_name} model={model_name}")

    vfw_device_type = mapping_entry["device_type"]
    templates_map = ctx.get("templates_map") or {}
    templates = templates_map.get(vfw_device_type, [])

    if not templates:
        return _skip_result(f"No templates found for device_type {vfw_device_type}")

    template_host_groups = list(dict.fromkeys(
        g for t in templates for g in t.get("host_groups", []) if g
    ))
    host_groups_csv = ",".join(
        filter(None, [vendor_name, name_prefix_hostgroup, location_name, model_name] + template_host_groups)
    )

    vfw_tags = {
        "Vendor": vendor_name,
        "Location": location_name,
        "Model": model_name,
        "Manufacturer": manufacturer_name,
        "Port": mgmt_port,
        "fw_status": fw_status,
        "proje": proje,
        "Loki_ID": f"VFW_{vfw_id}",
        "Created": str(vfw.get("created") or ""),
        "Last_Updated": str(vfw.get("last_updated") or ""),
    }

    technical_hostname = zabbix_vfw_technical_hostname(hostname_raw, vfw_id)
    zbx_record = {
        "DEVICE_TYPE": vfw_device_type,
        "DEVICE_ROLE": "VIRTUAL_FW",
        "HOST_IP": host_ip,
        "HOSTNAME": technical_hostname,
        "HOST_VISIBLE_NAME": hostname_visible,
        "DC_ID": location_name,
        "HOST_GROUPS": host_groups_csv,
        "TEMPLATE_TYPE": "",
        "HOST_STATUS": 1 if ctx.get("create_virtual_fws_disabled", False) else 0,
        "MACROS": json.dumps(vfw_tags),
        "REPORT_LOCATION": location_name,
        "REPORT_SITE": location_name,
        "REPORT_TENANT": "",
        "REPORT_OWNERSHIP": "",
    }

    loki_key = f"VFW_{vfw_id}"
    zbx_existing = _resolve_existing_host(
        loki_key,
        technical_hostname,
        hostname_visible,
        ctx.get("by_loki", {}),
        ctx.get("by_hostname", {}),
        ctx.get("by_visible", {}),
    )

    # Fallback: legacy NetBox hostname as visible name
    if not zbx_existing.get("hostid") and hostname_raw:
        h = ctx.get("by_visible", {}).get(hostname_raw)
        if isinstance(h, dict) and h.get("hostid"):
            zbx_existing = h

    zbx_scenario = "update" if zbx_existing.get("hostid") else "create"

    return {
        "action": zbx_scenario,
        "vfw_id": vfw_id,
        "zbx_record": zbx_record,
        "zbx_existing_host": zbx_existing,
        "zbx_scenario": zbx_scenario,
        "current_vfw_result": {},
    }


# ---------------------------------------------------------------------------
# Main parallel runner
# ---------------------------------------------------------------------------

def _progress(entity_type: str, item_id: Any, name: str, action: str, error: Optional[str] = None):
    """Emit one JSON-line to stdout (AWX streams this line-by-line)."""
    record = {
        "type": entity_type,
        "id": str(item_id),
        "name": name,
        "action": action,
    }
    if error:
        record["error"] = error
    print(json.dumps(record, ensure_ascii=False), flush=True)


def run_parallel_compare(
    devices: List[Dict],
    platforms: List[Dict],
    vfws: List[Dict],
    ctx: Dict,
    output_dir: str,
    workers: int = 20,
) -> Dict:
    """
    Run compare for all entities in parallel. Write plan files.
    Returns aggregate summary.
    """
    os.makedirs(output_dir, exist_ok=True)

    summary = {
        "devices": {"total": len(devices), "create": 0, "update": 0, "skip": 0, "error": 0},
        "platforms": {"total": len(platforms), "create": 0, "update": 0, "skip": 0, "error": 0},
        "vfws": {"total": len(vfws), "create": 0, "update": 0, "skip": 0, "error": 0},
        "errors": [],
    }

    futures = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for device in devices:
            f = executor.submit(compare_one_device, device, ctx)
            futures[f] = ("device", device.get("id", "unknown"), device.get("name", "unknown"))

        for platform in platforms:
            f = executor.submit(compare_one_platform, platform, ctx)
            futures[f] = ("platform", platform.get("id", "unknown"), platform.get("name") or platform.get("display", "unknown"))

        for vfw in vfws:
            f = executor.submit(compare_one_vfw, vfw, ctx)
            futures[f] = ("vfw", vfw.get("id", "unknown"), vfw.get("hostname", "unknown"))

        for future in as_completed(futures):
            entity_type, item_id, item_name = futures[future]
            try:
                plan = future.result()
                action = plan.get("action", "skip")
                _progress(entity_type, item_id, item_name, action)
                summary[f"{entity_type}s"][action if action in ("create", "update", "skip") else "skip"] += 1

                # Write plan file
                if entity_type == "device":
                    plan_path = os.path.join(output_dir, f"device_plan_{item_id}.json")
                elif entity_type == "platform":
                    plan_path = os.path.join(output_dir, f"platform_plan_{item_id}.json")
                else:
                    plan_path = os.path.join(output_dir, f"vfw_plan_{item_id}.json")
                with open(plan_path, "w", encoding="utf-8") as f_out:
                    json.dump(plan, f_out, ensure_ascii=False)

            except Exception as exc:
                tb = traceback.format_exc()
                error_msg = f"{exc.__class__.__name__}: {exc}"
                _progress(entity_type, item_id, item_name, "error", error=error_msg)
                summary[f"{entity_type}s"]["error"] += 1
                summary["errors"].append({
                    "type": entity_type,
                    "id": str(item_id),
                    "name": item_name,
                    "error": error_msg,
                    "traceback": tb,
                })
                # Write error plan so apply phase can skip gracefully
                error_plan = {
                    "action": "skip",
                    f"{entity_type}_id": str(item_id),
                    "zbx_record": {},
                    "zbx_existing_host": {},
                    "zbx_scenario": "skip",
                    "current_result": {
                        "hostname": str(item_name),
                        "device_role": entity_type.upper(),
                        "status": "eklenemedi",
                        "reason": f"Compare error: {error_msg}",
                        "ip": "N/A",
                        "location": "N/A",
                        "site": "N/A",
                        "tenant": "N/A",
                        "ownership": "N/A",
                    },
                }
                try:
                    if entity_type == "device":
                        plan_path = os.path.join(output_dir, f"device_plan_{item_id}.json")
                    elif entity_type == "platform":
                        plan_path = os.path.join(output_dir, f"platform_plan_{item_id}.json")
                    else:
                        plan_path = os.path.join(output_dir, f"vfw_plan_{item_id}.json")
                    with open(plan_path, "w", encoding="utf-8") as f_out:
                        json.dump(error_plan, f_out, ensure_ascii=False)
                except Exception:
                    pass

    summary_path = os.path.join(output_dir, "compare_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f_sum:
        json.dump(summary, f_sum, ensure_ascii=False, indent=2)

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_json_file(path: Optional[str], default: Any = None) -> Any:
    if not path or not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_yaml_file(path: Optional[str], default: Any = None) -> Any:
    if not path or not os.path.exists(path):
        return default
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or default
    except ImportError:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        try:
            return json.loads(content) or default
        except Exception:
            return default


def main():
    parser = argparse.ArgumentParser(
        description="Parallel compare engine for Zabbix-NetBox sync Phase A"
    )
    parser.add_argument("--devices-json", help="Path to devices JSON array file")
    parser.add_argument("--platforms-json", help="Path to platforms JSON array file")
    parser.add_argument("--vfws-json", help="Path to virtual firewalls JSON array file")
    parser.add_argument("--mappings-dir", required=True, help="Path to mappings/ directory")
    parser.add_argument("--zbx-templates-cache", help="Path to Zabbix templates cache JSON {name: id}")
    parser.add_argument("--zbx-groups-cache", help="Path to Zabbix host groups cache JSON {name: id}")
    parser.add_argument("--zbx-hosts-loki-map", help="Path to Zabbix hosts by Loki_ID JSON")
    parser.add_argument("--zbx-hosts-hostname-map", help="Path to Zabbix hosts by hostname JSON")
    parser.add_argument("--zbx-hosts-visible-map", help="Path to Zabbix hosts by visible_name JSON")
    parser.add_argument("--hmdl-baseline-map", help="Path to HMDL baseline map JSON")
    parser.add_argument("--output-dir", default="/tmp", help="Directory to write plan files (default: /tmp)")
    parser.add_argument("--workers", type=int, default=20, help="Max parallel compare workers (default: 20)")
    parser.add_argument("--create-devices-disabled", action="store_true")
    parser.add_argument("--create-platforms-disabled", action="store_true")
    parser.add_argument("--create-vfws-disabled", action="store_true")
    args = parser.parse_args()

    mappings_dir = args.mappings_dir

    # Load mapping configs
    device_type_mapping = _load_yaml_file(
        os.path.join(mappings_dir, "netbox_device_type_mapping.yml"), {}
    )
    host_groups_config = _load_yaml_file(os.path.join(mappings_dir, "host_groups_config.yml"))
    tags_config = _load_yaml_file(os.path.join(mappings_dir, "tags_config.yml"))
    templates_map = _load_yaml_file(os.path.join(mappings_dir, "templates.yml"), {})
    platform_mapping = _load_yaml_file(
        os.path.join(mappings_dir, "netbox_platform_mapping.yml"), {}
    )
    vfw_mapping = _load_yaml_file(
        os.path.join(mappings_dir, "virtual_fw_mapping.yml"), {}
    )

    # Load Zabbix host maps
    by_loki = _load_json_file(args.zbx_hosts_loki_map, {})
    by_hostname = _load_json_file(args.zbx_hosts_hostname_map, {})
    by_visible = _load_json_file(args.zbx_hosts_visible_map, {})

    ctx: Dict = {
        "device_type_mapping": device_type_mapping,
        "host_groups_config": host_groups_config,
        "tags_config": tags_config,
        "templates_map": templates_map,
        "platform_mapping": platform_mapping,
        "vfw_mapping": vfw_mapping,
        "by_loki": by_loki or {},
        "by_hostname": by_hostname or {},
        "by_visible": by_visible or {},
        "create_devices_disabled": args.create_devices_disabled,
        "create_platforms_disabled": args.create_platforms_disabled,
        "create_virtual_fws_disabled": args.create_vfws_disabled,
    }

    devices = _load_json_file(args.devices_json, []) or []
    platforms = _load_json_file(args.platforms_json, []) or []
    vfws = _load_json_file(args.vfws_json, []) or []

    total = len(devices) + len(platforms) + len(vfws)
    print(json.dumps({
        "type": "start",
        "devices": len(devices),
        "platforms": len(platforms),
        "vfws": len(vfws),
        "workers": args.workers,
        "total": total,
    }, ensure_ascii=False), flush=True)

    summary = run_parallel_compare(
        devices=devices,
        platforms=platforms,
        vfws=vfws,
        ctx=ctx,
        output_dir=args.output_dir,
        workers=args.workers,
    )

    print(json.dumps({"type": "summary", **summary}, ensure_ascii=False), flush=True)

    has_errors = bool(summary.get("errors"))
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
