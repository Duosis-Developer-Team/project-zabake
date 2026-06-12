#!/usr/bin/env python3
"""
Build Zabbix host.create / host.update API params from compare plans (Phase A).

Used by parallel_compare_engine.py so Phase B only POSTs ready payloads.
"""
from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

_ROLE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_UTILS_CANDIDATES = [
    os.environ.get("ZABBIX_SYNC_MODULE_UTILS", "").strip(),
    os.path.normpath(os.path.join(_ROLE_DIR, "..", "module_utils")),
    "/tmp/module_utils",
    "/tmp",
]
for _candidate in _MODULE_UTILS_CANDIDATES:
    if _candidate and os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)
    elif _candidate and os.path.isfile(os.path.join(_candidate, "zabbix_merge_helpers.py")):
        if _candidate not in sys.path:
            sys.path.insert(0, _candidate)

from zabbix_merge_helpers import (  # noqa: E402
    load_managed_tag_keys,
    merge_host_groups,
    merge_tags,
    resolve_proxy_group_update,
)

_DC_PATTERN = re.compile(r"(DC|AZ|ICT|UZ)\d+", re.IGNORECASE)
_PROXY_SUFFIX = re.compile(r"[-\s]*PROXY.*$", re.IGNORECASE)
# Zabbix host.flags: ZBX_FLAG_DISCOVERY_CREATED — cannot host.update the technical name.
_ZBX_FLAG_DISCOVERY_CREATED = 4


def _is_discovered_host(zbx_existing: Dict[str, Any]) -> bool:
    """Return True when Zabbix created the host via network discovery."""
    try:
        flags = int(zbx_existing.get("flags") or 0)
    except (TypeError, ValueError):
        return False
    return bool(flags & _ZBX_FLAG_DISCOVERY_CREATED)


def _extract_dc_code(location_or_name: str) -> str:
    text = (location_or_name or "").strip().upper()
    match = _DC_PATTERN.search(text)
    return match.group(0).upper() if match else ""


def _proxy_dc_from_group_name(name: str) -> str:
    upper = (name or "").upper()
    stripped = _PROXY_SUFFIX.sub("", upper).strip()
    match = _DC_PATTERN.search(stripped)
    return match.group(0).upper() if match else ""


def build_proxy_group_config(proxy_name_to_id: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build [{name, proxy_groupid, dc_pattern}, ...] from Zabbix proxygroup.get map."""
    out: List[Dict[str, str]] = []
    for name, pgid in (proxy_name_to_id or {}).items():
        out.append({
            "name": str(name),
            "proxy_groupid": str(pgid),
            "dc_pattern": _proxy_dc_from_group_name(str(name)),
        })
    return out


def _parse_macros_field(macros_raw: Any) -> Dict[str, str]:
    if isinstance(macros_raw, dict):
        return {str(k): str(v) for k, v in macros_raw.items()}
    if isinstance(macros_raw, str) and macros_raw.strip():
        try:
            parsed = json.loads(macros_raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            pass
    return {}


def _macros_to_tags(macros: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"tag": k, "value": v} for k, v in macros.items()]


def _effective_managed_keys(ctx: Dict, device_role: str) -> List[str]:
    keys = list(load_managed_tag_keys(ctx.get("tags_config")))
    role = (device_role or "").upper()
    if role == "PLATFORM":
        keys.extend(ctx.get("platform_managed_tag_keys") or [])
    elif role == "VIRTUAL_FW":
        keys.extend(ctx.get("vfw_managed_tag_keys") or [])
    return list(dict.fromkeys(keys))


class ZabbixPayloadBuilder:
    """Resolve templates, groups, proxy, interfaces; build create/update API params."""

    def __init__(self, ctx: Dict[str, Any]) -> None:
        self.ctx = ctx
        self.templates_map: Dict[str, List[Dict]] = ctx.get("templates_map") or {}
        self.template_type_map: Dict[str, Any] = ctx.get("template_type_map") or {}
        self.template_id_cache: Dict[str, str] = {
            str(k): str(v) for k, v in (ctx.get("template_id_cache") or {}).items()
        }
        self.group_id_cache: Dict[str, str] = {
            str(k): str(v) for k, v in (ctx.get("group_id_cache") or {}).items()
        }
        self.proxy_group_config: List[Dict[str, str]] = ctx.get("proxy_group_config") or []
        self.hmdl_baseline_map: Dict[str, Any] = ctx.get("hmdl_baseline_map") or {}

    def _template_rows(self, device_type: str) -> List[Dict]:
        rows = self.templates_map.get(device_type, [])
        return [r for r in rows if isinstance(r, dict)]

    def resolve_template_names_and_types(self, device_type: str) -> Tuple[List[str], List[str], List[Dict]]:
        rows = self._template_rows(device_type)
        names: List[str] = []
        types: List[str] = []
        for row in rows:
            name = row.get("name")
            if name:
                names.append(str(name))
            type_str = str(row.get("type", "") or "").strip()
            for key in ("snmpv2", "snmpv3", "agent", "api", "API", "none"):
                if row.get(key) or type_str == key:
                    types.append(key if key != "API" else "api")
                    break
        return list(dict.fromkeys(names)), list(dict.fromkeys(types)), rows

    def resolve_template_ids(self, names: List[str]) -> Tuple[List[Dict[str, str]], List[str]]:
        found: List[Dict[str, str]] = []
        missing: List[str] = []
        for name in names:
            tid = self.template_id_cache.get(name)
            if tid:
                found.append({"templateid": str(tid)})
            else:
                missing.append(name)
        return found, missing

    def resolve_interface_type(self, template_types: List[str]) -> str:
        if not template_types:
            return "snmpv2"
        return template_types[0]

    def resolve_interface_spec(self, iface_type: str) -> Optional[Dict[str, Any]]:
        entry = self.template_type_map.get(iface_type) or self.template_type_map.get(iface_type.lower())
        if not entry or not isinstance(entry, dict):
            return None
        iface = entry.get("interface")
        if iface is None:
            return None
        return deepcopy(iface) if isinstance(iface, dict) else None

    def resolve_interface_spec_with_override(
        self,
        iface_type: str,
        template_rows: List[Dict],
    ) -> Optional[Dict[str, Any]]:
        """Merge global template_types spec with optional templates.yml interface_override (create-only)."""
        spec = self.resolve_interface_spec(iface_type)
        if spec is None:
            return None
        for row in template_rows:
            override = row.get("interface_override")
            if not isinstance(override, dict):
                continue
            if "details" in override and isinstance(override["details"], dict):
                spec.setdefault("details", {})
                spec["details"].update(deepcopy(override["details"]))
            for field in ("port", "dns"):
                if field in override:
                    spec[field] = override[field]
        return spec

    def build_interface_create(self, zbx_record: Dict, iface_spec: Optional[Dict]) -> List[Dict]:
        if not iface_spec or not isinstance(iface_spec, dict) or "type" not in iface_spec:
            return []
        row = {
            "type": int(iface_spec["type"]),
            "main": 1,
            "useip": 1,
            "ip": zbx_record.get("HOST_IP", ""),
            "dns": iface_spec.get("dns", "") or "",
            "port": str(iface_spec.get("port", 161)),
        }
        if iface_spec.get("details"):
            row["details"] = deepcopy(iface_spec["details"])
        return [row]

    def build_interface_update(
        self,
        zbx_record: Dict,
        iface_spec: Optional[Dict],
        existing_host: Dict,
        interface_type_changed: bool,
    ) -> Tuple[List[Dict], bool]:
        """Returns (interface_update_list, interface_type_locked).

        Update policy: only primary IP may change. port, dns, and SNMP details are
        create-only (from template_types.yml / interface_override) and are never sent
        on host.update.
        """
        if interface_type_changed:
            return [], True
        ifaces = existing_host.get("interfaces") or []
        if not ifaces:
            return [], False
        existing_iface = ifaces[0]
        iface_id = existing_iface.get("interfaceid")
        if not iface_id:
            return [], False
        existing_ip = existing_iface.get("ip") or ""
        new_ip = zbx_record.get("HOST_IP", "") or ""
        if existing_ip == new_ip:
            return [], False
        return [{"interfaceid": str(iface_id), "ip": new_ip}], False

    def resolve_proxy(
        self,
        zbx_record: Dict,
        template_rows: List[Dict],
    ) -> Tuple[str, str, str]:
        """
        Returns (monitored_by, proxy_group_id, matched_proxy_group_name).
        monitored_by: '0' = server, '2' = proxy group
        """
        dc_id = zbx_record.get("DC_ID", "") or ""
        dc_code = _extract_dc_code(dc_id)

        merged_pg_by_dc: Dict[str, str] = {}
        for row in template_rows:
            pg_map = row.get("proxy_group_by_dc")
            if isinstance(pg_map, dict):
                for k, v in pg_map.items():
                    if k and v:
                        merged_pg_by_dc[str(k).strip().upper()] = str(v)

        proxy_group_id = ""
        matched_name = ""
        monitored_by = "0"

        if dc_code:
            for entry in self.proxy_group_config:
                if entry.get("dc_pattern", "").upper() == dc_code:
                    proxy_group_id = str(entry.get("proxy_groupid", ""))
                    matched_name = str(entry.get("name", ""))
                    if proxy_group_id:
                        monitored_by = "2"
                    break

        static_name = merged_pg_by_dc.get(dc_code.upper(), "") if dc_code else ""
        if static_name:
            for entry in self.proxy_group_config:
                if entry.get("name") == static_name:
                    proxy_group_id = str(entry.get("proxy_groupid", ""))
                    matched_name = static_name
                    if proxy_group_id:
                        monitored_by = "2"
                    break

        return monitored_by, proxy_group_id, matched_name

    def resolve_required_group_names(
        self,
        zbx_record: Dict,
        template_rows: List[Dict],
    ) -> List[str]:
        csv = zbx_record.get("HOST_GROUPS", "") or ""
        csv_groups = [g.strip() for g in csv.split(",") if g.strip()]
        template_groups: List[str] = []
        for row in template_rows:
            for g in row.get("host_groups") or []:
                if g:
                    template_groups.append(str(g))
        device_type = zbx_record.get("DEVICE_TYPE", "")
        all_names = csv_groups + template_groups
        if device_type:
            all_names.append(str(device_type))
        return list(dict.fromkeys(all_names))

    def detect_missing_groups(self, required_names: List[str]) -> List[str]:
        missing = []
        for name in required_names:
            if name not in self.group_id_cache:
                missing.append(name)
        return missing

    def format_groups(self, group_names: List[str]) -> List[Dict[str, str]]:
        out = []
        for name in group_names:
            gid = self.group_id_cache.get(name)
            if gid:
                out.append({"groupid": str(gid)})
        return out

    def collect_template_macros(self, template_rows: List[Dict], host_ip: str) -> Tuple[Dict[str, str], List[Dict]]:
        macros: Dict[str, str] = {}
        for row in template_rows:
            for key, val in (row.get("macros") or {}).items():
                processed = str(val).replace("{HOST.IP}", host_ip)
                macros[str(key)] = processed
        formatted = [{"macro": k, "value": v} for k, v in macros.items()]
        return macros, formatted

    def _hmdl_row_for_record(self, zbx_record: Dict) -> Dict[str, Any]:
        device_id = str(
            zbx_record.get("LOKI_DEVICE_ID")
            or _parse_macros_field(zbx_record.get("MACROS", {})).get("Loki_ID", "")
            or ""
        ).replace("P_", "").replace("VFW_", "")
        return self.hmdl_baseline_map.get(device_id, {}) or {}

    def enrich_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Add create_payload, update_payload, missing_groups, needs_update to compare plan."""
        action = plan.get("action", "skip")
        if action not in ("create", "update"):
            plan.setdefault("create_payload", None)
            plan.setdefault("update_payload", None)
            plan.setdefault("missing_groups", [])
            plan.setdefault("needs_update", False)
            plan.setdefault("update_reasons", [])
            plan.setdefault("validation_errors", [])
            return plan

        zbx_record = plan.get("zbx_record") or {}
        zbx_existing = plan.get("zbx_existing_host") or {}
        device_type = zbx_record.get("DEVICE_TYPE", "")
        device_role = zbx_record.get("DEVICE_ROLE", "")

        template_names, template_types, template_rows = self.resolve_template_names_and_types(device_type)
        template_ids, missing_templates = self.resolve_template_ids(template_names)
        iface_type = self.resolve_interface_type(template_types)
        iface_spec = self.resolve_interface_spec(iface_type)
        create_iface_spec = (
            self.resolve_interface_spec_with_override(iface_type, template_rows)
            if action == "create"
            else iface_spec
        )
        monitored_by, proxy_group_id, _ = self.resolve_proxy(zbx_record, template_rows)
        required_groups = self.resolve_required_group_names(zbx_record, template_rows)
        missing_groups = self.detect_missing_groups(required_groups)
        macros_dict, macros_formatted = self.collect_template_macros(
            template_rows, zbx_record.get("HOST_IP", "") or ""
        )
        tags = _macros_to_tags(_parse_macros_field(zbx_record.get("MACROS", {})))
        visible_name = zbx_record.get("HOST_VISIBLE_NAME") or zbx_record.get("HOSTNAME", "")
        validation_errors: List[str] = []

        if not zbx_record.get("HOSTNAME"):
            validation_errors.append("Hostname eksik")
        if not zbx_record.get("HOST_IP"):
            validation_errors.append("IP adresi eksik")
        if missing_templates:
            validation_errors.append(
                "Zabbix'te bulunamayan şablonlar: " + ", ".join(missing_templates)
            )
        elif not template_ids:
            validation_errors.append("Template bulunamadı (Zabbix'te eşleşen şablon yok)")
        dc_code = _extract_dc_code(zbx_record.get("DC_ID", "") or "")
        if dc_code and not proxy_group_id and action == "create":
            validation_errors.append(f"Proxy group bulunamadı (DC_ID: {zbx_record.get('DC_ID', 'N/A')})")

        plan["missing_groups"] = missing_groups
        plan["validation_errors"] = validation_errors

        if validation_errors:
            plan["create_payload"] = None
            plan["update_payload"] = None
            plan["needs_update"] = False
            result_key = (
                "current_device_result"
                if "device_id" in plan
                else ("current_platform_result" if "platform_id" in plan else "current_vfw_result")
            )
            plan[result_key] = {
                "hostname": zbx_record.get("HOSTNAME", "N/A"),
                "device_role": device_role or "N/A",
                "status": "eklenemedi",
                "reason": ", ".join(validation_errors),
                "ip": zbx_record.get("HOST_IP", "N/A"),
                "location": zbx_record.get("REPORT_LOCATION", "N/A"),
                "site": zbx_record.get("REPORT_SITE", "N/A"),
                "tenant": zbx_record.get("REPORT_TENANT", "N/A"),
                "ownership": zbx_record.get("REPORT_OWNERSHIP", "N/A"),
            }
            plan["action"] = "skip"
            plan["zbx_scenario"] = "skip"
            return plan

        if action == "create":
            create_payload: Dict[str, Any] = {
                "host": zbx_record["HOSTNAME"],
                "name": visible_name,
                "status": int(zbx_record.get("HOST_STATUS", 0) or 0),
                "interfaces": self.build_interface_create(zbx_record, create_iface_spec),
                "templates": template_ids,
                "groups": self.format_groups(
                    [g for g in required_groups if g in self.group_id_cache]
                ),
                "monitored_by": int(monitored_by),
            }
            if tags:
                create_payload["tags"] = tags
            if macros_formatted:
                create_payload["macros"] = macros_formatted
            if proxy_group_id and monitored_by == "2":
                create_payload["proxy_groupid"] = int(proxy_group_id)

            plan["create_payload"] = create_payload
            plan["update_payload"] = None
            plan["needs_update"] = False
            plan["planned_operation"] = "create"
            return plan

        # update path
        existing_ifaces = zbx_existing.get("interfaces") or []
        existing_iface = existing_ifaces[0] if existing_ifaces else {}
        existing_type = int(existing_iface.get("type", 0) or 0)
        new_type = int(iface_spec.get("type", 0) or 0) if iface_spec else 0
        interface_type_changed = bool(
            iface_spec and existing_iface and existing_type != new_type
        )
        iface_update, iface_locked = self.build_interface_update(
            zbx_record, iface_spec, zbx_existing, interface_type_changed
        )

        managed_keys = _effective_managed_keys(self.ctx, device_role)
        existing_tags = zbx_existing.get("tags") or []
        merged_tags, tag_change_log = merge_tags(existing_tags, tags, managed_keys)
        tags_needs_update = any(
            e.get("action") in ("added", "updated") for e in tag_change_log
        )

        existing_group_names = [
            g.get("name", "") for g in (zbx_existing.get("groups") or []) if g.get("name")
        ]
        merged_group_names, groups_needs_update = merge_host_groups(
            existing_group_names, required_groups, preserve_manual=True
        )

        hmdl = self._hmdl_row_for_record(zbx_record)
        proxy_decision = resolve_proxy_group_update(
            current_location=zbx_record.get("DC_ID", "") or "",
            last_hmdl_location=hmdl.get("last_location"),
            expected_proxy_group_id=proxy_group_id,
            zabbix_proxy_group_id=str(zbx_existing.get("proxy_groupid", "") or ""),
            last_hmdl_proxy_group_id=hmdl.get("last_proxy_group_id"),
        )
        effective_proxy_id = (
            str(zbx_existing.get("proxy_groupid", "") or "")
            if proxy_decision.get("proxy_manual_change_detected")
            else proxy_group_id
        )
        if effective_proxy_id and monitored_by == "2":
            monitored_by = "2"
        proxy_apply = bool(proxy_decision.get("apply_update"))

        existing_ip = (existing_iface.get("ip") or "") if existing_iface else ""
        update_reasons: List[str] = []
        if existing_ip != zbx_record.get("HOST_IP", ""):
            update_reasons.append(
                f"ip_changed:{existing_ip}->{zbx_record.get('HOST_IP', '')}"
            )
        if zbx_existing.get("host", "") != zbx_record.get("HOSTNAME", ""):
            update_reasons.append("hostname_changed")
        if str(zbx_existing.get("monitored_by", "")) != str(monitored_by):
            update_reasons.append("monitored_by_changed")
        if proxy_apply:
            update_reasons.append("proxy_group_changed")
        if tags_needs_update:
            changed_tags = [
                e.get("key_name", "")
                for e in tag_change_log
                if e.get("action") in ("added", "updated")
            ]
            update_reasons.append(f"tags:{changed_tags}")
        if groups_needs_update:
            update_reasons.append("groups_changed")

        needs_update = bool(
            (existing_ip != zbx_record.get("HOST_IP", ""))
            or (zbx_existing.get("host", "") != zbx_record.get("HOSTNAME", ""))
            or (str(zbx_existing.get("monitored_by", "")) != str(monitored_by))
            or proxy_apply
            or tags_needs_update
            or groups_needs_update
        )
        if needs_update and iface_update and not iface_locked:
            update_reasons.append("interface_changed")
        if iface_locked:
            update_reasons.append("interface_type_locked")

        plan["update_reasons"] = update_reasons

        plan["needs_update"] = needs_update
        plan["proxy_manual_change_detected"] = bool(
            proxy_decision.get("proxy_manual_change_detected")
        )
        plan["planned_operation"] = "update" if needs_update else "none"

        if not needs_update:
            plan["update_payload"] = None
            plan["create_payload"] = None
            result_key = (
                "current_device_result"
                if "device_id" in plan
                else ("current_platform_result" if "platform_id" in plan else "current_vfw_result")
            )
            plan[result_key] = {
                "hostname": zbx_record.get("HOSTNAME", "N/A"),
                "device_role": device_role or "N/A",
                "status": "güncel",
                "reason": "",
                "update_reasons": [],
                "ip": zbx_record.get("HOST_IP", "N/A"),
                "location": zbx_record.get("REPORT_LOCATION", "N/A"),
                "site": zbx_record.get("REPORT_SITE", "N/A"),
                "tenant": zbx_record.get("REPORT_TENANT", "N/A"),
                "ownership": zbx_record.get("REPORT_OWNERSHIP", "N/A"),
            }
            return plan

        update_payload: Dict[str, Any] = {
            "hostid": str(zbx_existing["hostid"]),
            "host": zbx_record["HOSTNAME"],
            "monitored_by": int(monitored_by),
            "proxy_groupid": int(effective_proxy_id or 0),
        }
        if iface_update and not iface_locked:
            update_payload["interfaces"] = iface_update
        if groups_needs_update:
            update_payload["groups"] = self.format_groups(
                [g for g in merged_group_names if g in self.group_id_cache]
            )
        if tags_needs_update:
            update_payload["tags"] = merged_tags

        plan["update_payload"] = update_payload
        plan["create_payload"] = None
        result_key = (
            "current_device_result"
            if "device_id" in plan
            else ("current_platform_result" if "platform_id" in plan else "current_vfw_result")
        )
        plan[result_key] = {
            "hostname": zbx_record.get("HOSTNAME", "N/A"),
            "device_role": device_role or "N/A",
            "status": "güncellenecek",
            "reason": "; ".join(update_reasons) if update_reasons else "",
            "update_reasons": update_reasons,
            "ip": zbx_record.get("HOST_IP", "N/A"),
            "location": zbx_record.get("REPORT_LOCATION", "N/A"),
            "site": zbx_record.get("REPORT_SITE", "N/A"),
            "tenant": zbx_record.get("REPORT_TENANT", "N/A"),
            "ownership": zbx_record.get("REPORT_OWNERSHIP", "N/A"),
        }
        return plan
