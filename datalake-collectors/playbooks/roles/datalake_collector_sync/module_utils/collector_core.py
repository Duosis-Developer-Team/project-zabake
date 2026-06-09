"""
Core logic for HMDL datalake collector sync: mapping, IP reconcile, vault merge.
"""

from __future__ import annotations

import copy
import ipaddress
import re
from typing import Any


def _norm(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip()


def _lower(s: Any) -> str:
    return _norm(s).lower()


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_ip_list(raw: Any) -> list[str]:
    """Parse comma-separated IP/host string into ordered unique list."""
    if raw is None:
        return []
    text = _norm(raw)
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"[,;\s]+", text) if p.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def format_ip_list(ips: list[str], ip_format: str) -> str:
    """Format IP list for configuration_file.json field."""
    if not ips:
        return ""
    if ip_format == "single_string":
        return ips[0]
    return ",".join(ips)


def extract_dc_code(site_or_dc: str) -> str:
    """Extract DC13-style code from NetBox Site/DC custom field."""
    if not site_or_dc:
        return ""
    m = re.search(r"(DC|AZ|ICT|UZ)\d+", str(site_or_dc), re.IGNORECASE)
    return m.group(0).upper() if m else ""


def normalize_proxy_assignment(
    proxy_assignment: dict,
) -> tuple[dict[str, list[str]], dict[str, dict]]:
    """
    Normalize proxy_assignment.yml (legacy single-host or multi-NiFi schema).

    Returns:
        dc_to_proxy_ids: dc_code -> ordered proxy_id list
        proxy_lookup: proxy_id -> SSH/conf settings for reconcile
    """
    dc_to_proxy_ids: dict[str, list[str]] = {}
    proxy_lookup: dict[str, dict] = {}

    for dc_key, entry in (proxy_assignment or {}).items():
        if not isinstance(entry, dict):
            continue

        if entry.get("proxies"):
            dc_code = _norm(entry.get("dc_code") or dc_key)
            dc_to_proxy_ids.setdefault(dc_code, [])
            for proxy in entry.get("proxies") or []:
                if not isinstance(proxy, dict):
                    continue
                proxy_id = _norm(proxy.get("id") or f"{dc_code}-NIFI")
                proxy_lookup[proxy_id] = {
                    "id": proxy_id,
                    "proxy_nifi_host": proxy.get("proxy_nifi_host", ""),
                    "ssh_user": proxy.get("ssh_user", "nifi"),
                    "conf_path": proxy.get(
                        "conf_path", "/Datalake_Project/configuration_file.json"
                    ),
                    "gitea_audit_path": proxy.get("gitea_audit_path", ""),
                    "dc_key": dc_key,
                    "dc_code": dc_code,
                }
                if proxy_id not in dc_to_proxy_ids[dc_code]:
                    dc_to_proxy_ids[dc_code].append(proxy_id)
            continue

        # Legacy single-host entry keyed by DC code
        dc_code = _norm(entry.get("dc_code") or dc_key)
        proxy_id = _norm(entry.get("proxy_id") or dc_key)
        proxy_lookup[proxy_id] = {
            "id": proxy_id,
            "proxy_nifi_host": entry.get("proxy_nifi_host", ""),
            "ssh_user": entry.get("ssh_user", "nifi"),
            "conf_path": entry.get(
                "conf_path", "/Datalake_Project/configuration_file.json"
            ),
            "gitea_audit_path": entry.get("gitea_audit_path", ""),
            "dc_key": dc_key,
            "dc_code": dc_code,
        }
        dc_to_proxy_ids.setdefault(dc_code, []).append(proxy_id)

    return dc_to_proxy_ids, proxy_lookup


def resolve_dc_code(dc_code: str, proxy_assignment: dict) -> str:
    """Resolve NetBox DC code to proxy_assignment dc_code key."""
    dc_to_proxy_ids, _ = normalize_proxy_assignment(proxy_assignment)
    if dc_code and dc_code in dc_to_proxy_ids:
        return dc_code
    for key in dc_to_proxy_ids:
        if key != "MAIN" and dc_code and dc_code.startswith(key):
            return key
    if "MAIN" in dc_to_proxy_ids:
        return "MAIN"
    return dc_code or "MAIN"


def resolve_proxy_ids(dc_code: str, proxy_assignment: dict) -> list[str]:
    """Map NetBox DC code to all proxy NiFi node IDs for that site."""
    dc_to_proxy_ids, proxy_lookup = normalize_proxy_assignment(proxy_assignment)
    resolved = resolve_dc_code(dc_code, proxy_assignment)
    if resolved in dc_to_proxy_ids:
        return list(dc_to_proxy_ids[resolved])
    if dc_to_proxy_ids:
        return list(next(iter(dc_to_proxy_ids.values())))
    return [resolved or "MAIN"]


def resolve_proxy_id(dc_code: str, proxy_assignment: dict) -> str:
    """Backward-compatible: first proxy id for a DC code."""
    ids = resolve_proxy_ids(dc_code, proxy_assignment)
    return ids[0] if ids else (dc_code or "MAIN")


def filter_proxy_ids(
    proxy_lookup: dict[str, dict],
    proxy_filter: str = "",
) -> list[str]:
    """Filter proxy ids by exact id or dc_code match."""
    if not proxy_filter:
        return sorted(proxy_lookup.keys())
    filt = _norm(proxy_filter)
    out = [
        pid
        for pid, cfg in proxy_lookup.items()
        if pid == filt or _norm(cfg.get("dc_code")) == filt or _norm(cfg.get("dc_key")) == filt
    ]
    return sorted(out)


def match_platform_mapping(
    manufacturer: str,
    platform_name: str,
    site: str,
    mappings: list[dict],
) -> dict | None:
    """First matching platform mapping row by priority."""
    mfr = _lower(manufacturer)
    name_l = _lower(platform_name)
    site_l = _lower(site)
    sorted_rows = sorted(mappings, key=lambda r: int(r.get("priority", 999)))
    for row in sorted_rows:
        row_mfr = _lower(row.get("manufacturer", ""))
        if row_mfr and row_mfr != mfr:
            continue
        if row.get("name_contains") and _lower(row["name_contains"]) not in name_l:
            continue
        if row.get("site_contains") and _lower(row["site_contains"]) not in site_l:
            continue
        return row
    return None


def _condition_match(value: Any, expected: Any) -> bool:
    if expected is None:
        return True
    val = _lower(value)
    for exp in _as_list(expected):
        if _lower(exp) == val:
            return True
    return False


def match_device_mapping(device: dict, mappings: list[dict]) -> dict | None:
    """Match NetBox device dict to collector_type mapping row."""
    role = ""
    if device.get("device_role"):
        role = device["device_role"].get("name") or device["device_role"].get("slug") or ""
    mfr = ""
    if device.get("device_type") and device["device_type"].get("manufacturer"):
        mfr = device["device_type"]["manufacturer"].get("name", "")
    model = device.get("device_type", {}).get("model", "") or ""

    sorted_rows = sorted(mappings, key=lambda r: int(r.get("priority", 999)))
    for row in sorted_rows:
        cond = row.get("conditions") or {}
        if not _condition_match(role, cond.get("device_role")):
            continue
        if not _condition_match(mfr, cond.get("manufacturer")):
            continue
        mc = cond.get("model_contains")
        if mc:
            model_l = _lower(model)
            if not any(_lower(k) in model_l for k in _as_list(mc)):
                continue
        return row
    return None


def extract_platform_ip(platform: dict) -> str:
    cf = platform.get("custom_fields") or {}
    ip = cf.get("ip_addresses") or cf.get("IP") or ""
    if isinstance(ip, list):
        return ip[0] if ip else ""
    return _norm(ip)


def extract_device_ip(device: dict, ip_field_source: str) -> str:
    if ip_field_source == "management_ip":
        cf = device.get("custom_fields") or {}
        ip = cf.get("mgmt_ip") or cf.get("management_ip") or ""
        if ip:
            return _norm(ip)
    primary = device.get("primary_ip4") or device.get("primary_ip") or {}
    if isinstance(primary, dict):
        return _norm(primary.get("address", "").split("/")[0])
    return _norm(primary).split("/")[0] if primary else ""


def build_secondary_field(template: str, ips: list[str]) -> str:
    """Build comma-separated secondary field e.g. link from https://{ip}:7443."""
    if not ips:
        return ""
    parts = []
    for ip in ips:
        host = ip.split("/")[0]
        parts.append(template.replace("{ip}", host))
    return ",".join(parts)


def merge_vault_into_section(
    section: dict,
    vault_defaults: dict,
    other_fields: dict | None,
    ips: list[str],
    ip_field: str,
    ip_format: str,
    secondary_fields: dict | None = None,
) -> dict:
    """Build section dict with vault credentials and formatted IP field."""
    out = copy.deepcopy(section) if section else {}
    out.update(copy.deepcopy(vault_defaults))
    if other_fields:
        for k, v in other_fields.items():
            if isinstance(v, str) and "{{ vault." in v:
                key = v.replace("{{ vault.", "").replace(" }}", "").strip()
                out[k] = vault_defaults.get(key, vault_defaults.get("user", ""))
            else:
                out[k] = v
    out[ip_field] = format_ip_list(ips, ip_format)
    if secondary_fields:
        for field_name, tmpl in secondary_fields.items():
            out[field_name] = build_secondary_field(str(tmpl), ips)
    return out


def reconcile_section_ips(
    current_section: dict,
    desired_ips: list[str],
    ip_field: str,
    ip_format: str,
    secondary_fields: dict | None = None,
    connectivity_map: dict[str, str] | None = None,
) -> tuple[dict, list[dict]]:
    """
    Smart-merge: update only ip_field (and computed secondary_fields).
    When connectivity_map marks a removal candidate as ok, keep the IP (removal_blocked).
    Returns (updated_section, diff_entries).
    """
    section = copy.deepcopy(current_section) if current_section else {}
    current_ips = parse_ip_list(section.get(ip_field, ""))
    desired_set = set(desired_ips)
    current_set = set(current_ips)
    connectivity_map = connectivity_map or {}

    diffs: list[dict] = []
    for ip in sorted(desired_set - current_set):
        diffs.append({"action": "added", "ip": ip, "reason": "new_in_netbox"})
    for ip in sorted(current_set - desired_set):
        if connectivity_map.get(ip) == "ok":
            diffs.append(
                {
                    "action": "removal_blocked",
                    "ip": ip,
                    "reason": "still_reachable",
                }
            )
        else:
            diffs.append(
                {"action": "removed", "ip": ip, "reason": "missing_from_netbox"}
            )
    for ip in sorted(current_set & desired_set):
        diffs.append({"action": "preserved", "ip": ip, "reason": "unchanged"})

    blocked = {d["ip"] for d in diffs if d["action"] == "removal_blocked"}
    effective_desired = desired_set | blocked

    merged: list[str] = []
    seen: set[str] = set()
    for ip in current_ips:
        if ip in effective_desired and ip not in seen:
            merged.append(ip)
            seen.add(ip)
    for ip in desired_ips:
        if ip not in seen:
            merged.append(ip)
            seen.add(ip)

    section[ip_field] = format_ip_list(merged, ip_format)
    if secondary_fields:
        for field_name, tmpl in secondary_fields.items():
            section[field_name] = build_secondary_field(str(tmpl), merged)
    return section, diffs


def reconcile_proxy_config(
    current_config: dict,
    desired_by_conf_key: dict[str, dict],
    collector_types: dict,
    preserve_unknown: bool = True,
    connectivity_map: dict[str, str] | None = None,
) -> tuple[dict, list[dict]]:
    """
    Reconcile full configuration_file.json.
    desired_by_conf_key: conf_key -> partial section (with ip_field already set).
    """
    result = copy.deepcopy(current_config) if current_config else {}
    all_diffs: list[dict] = []

    for conf_key, desired_section in desired_by_conf_key.items():
        ctype = _find_collector_type_by_conf_key(collector_types, conf_key)
        if not ctype:
            continue
        meta = collector_types[ctype]
        if meta.get("source_type") == "manual_only":
            continue
        ip_field = meta.get("ip_field")
        if not ip_field:
            continue
        ip_format = meta.get("ip_format", "comma_string")
        secondary = meta.get("secondary_fields")
        current_section = result.get(conf_key, {})
        desired_ips = parse_ip_list(desired_section.get(ip_field, ""))
        updated, diffs = reconcile_section_ips(
            current_section,
            desired_ips,
            ip_field,
            ip_format,
            secondary,
            connectivity_map,
        )
        # Merge non-IP fields from desired (vault/other_fields) without wiping manual keys
        for k, v in desired_section.items():
            if k != ip_field and k not in (secondary or {}):
                updated[k] = v
        result[conf_key] = updated
        for d in diffs:
            d["conf_key"] = conf_key
            d["collector_type"] = ctype
            all_diffs.append(d)

    if preserve_unknown:
        for key in current_config:
            if key not in result:
                result[key] = current_config[key]

    return result, all_diffs


def _find_collector_type_by_conf_key(collector_types: dict, conf_key: str) -> str | None:
    for ctype, meta in collector_types.items():
        if meta.get("conf_key") == conf_key:
            return ctype
    return None


def group_targets_by_proxy_and_conf(
    targets: list[dict],
) -> dict[str, dict[str, list[str]]]:
    """
    targets: list of {proxy_id, conf_key, ip}
    Returns: proxy_id -> conf_key -> [ips]
    """
    grouped: dict[str, dict[str, list[str]]] = {}
    for t in targets:
        proxy = t["proxy_id"]
        ck = t["conf_key"]
        ip = t["ip"]
        grouped.setdefault(proxy, {}).setdefault(ck, [])
        if ip and ip not in grouped[proxy][ck]:
            grouped[proxy][ck].append(ip)
    return grouped


def is_valid_ip_or_host(value: str) -> bool:
    v = _norm(value)
    if not v:
        return False
    host = v.split("/")[0]
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return bool(re.match(r"^[\w.\-]+$", host))
