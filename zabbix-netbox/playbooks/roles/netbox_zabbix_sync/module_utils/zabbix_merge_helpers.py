#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helpers for HMDL Zabbix sync: managed vs manual field merge and proxy group decisions.

Bundled by Ansible via role module_utils/ (import as ansible.module_utils.zabbix_merge_helpers).
"""

from __future__ import annotations

from typing import Any


def load_managed_tag_keys(tags_config: dict | None) -> list[str]:
    """Return tag names defined in tags_config.yml (enabled definitions only)."""
    if not tags_config:
        return []
    definitions = tags_config.get("tags", {}).get("definitions", [])
    keys: list[str] = []
    for item in definitions:
        if not item.get("enabled", True):
            continue
        name = item.get("tag_name")
        if name:
            keys.append(str(name))
    return keys


def is_managed_tag(tag_name: str, managed_keys: list[str]) -> bool:
    if tag_name in managed_keys:
        return True
    if tag_name.startswith("Loki_Tag_"):
        return True
    return False


def merge_tags(
    existing_tags: list[dict[str, Any]],
    new_managed_tags: list[dict[str, Any]],
    managed_keys: list[str] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """
    Preserve manual tags; replace managed tags from source data.

    Returns (merged_tags, change_log).
    """
    managed_keys = managed_keys or []
    existing_map = {
        str(t.get("tag", "")): str(t.get("value", ""))
        for t in (existing_tags or [])
        if t.get("tag")
    }
    manual_tags = [
        {"tag": name, "value": value}
        for name, value in existing_map.items()
        if not is_managed_tag(name, managed_keys)
    ]
    new_map: dict[str, str] = {}
    for t in new_managed_tags or []:
        tag = t.get("tag") if isinstance(t, dict) else None
        val = t.get("value") if isinstance(t, dict) else None
        if tag is None:
            continue
        sval = "" if val is None else str(val).strip()
        if sval == "":
            continue
        new_map[str(tag)] = sval

    change_log: list[dict[str, Any]] = []
    for tag, new_val in new_map.items():
        old_val = existing_map.get(tag)
        if old_val is None:
            action = "added"
        elif old_val != new_val:
            action = "updated"
        else:
            action = "unchanged"
        change_log.append(
            {
                "key_name": tag,
                "old_value": old_val,
                "new_value": new_val,
                "action": action,
                "object_type": "tag",
            }
        )

    merged = manual_tags + [{"tag": k, "value": v} for k, v in new_map.items()]
    return merged, change_log


def merge_host_groups(
    existing_group_names: list[str],
    required_managed_names: list[str],
    preserve_manual: bool = True,
) -> tuple[list[str], bool]:
    """
    Set managed host groups from source; optionally preserve manual Zabbix groups.

    When preserve_manual is False (e.g. DEVICE_ROLE PLATFORM), the merged list is
    exactly the required managed names — existing wrong groups are not kept.

    Returns (merged_group_names, needs_update).
    """
    existing = [g for g in (existing_group_names or []) if g]
    required = [g for g in (required_managed_names or []) if g]
    required_unique = list(dict.fromkeys(required))
    if preserve_manual:
        required_set = set(required_unique)
        manual = [g for g in existing if g not in required_set]
        merged = list(dict.fromkeys(required_unique + manual))
    else:
        merged = required_unique
    needs_update = sorted(existing) != sorted(merged)
    return merged, needs_update


def merge_macros(
    existing_macros: list[dict[str, Any]],
    new_managed_macros: list[dict[str, Any]],
    managed_macro_keys: list[str] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Preserve macros outside managed set; update managed macro keys from templates."""
    managed_keys = set(managed_macro_keys or [])
    existing_map: dict[str, str] = {}
    for m in existing_macros or []:
        key = m.get("macro")
        if key:
            existing_map[str(key)] = str(m.get("value", ""))

    manual = [
        {"macro": k, "value": v}
        for k, v in existing_map.items()
        if k not in managed_keys
    ]
    new_map: dict[str, str] = {}
    for m in new_managed_macros or []:
        key = m.get("macro") if isinstance(m, dict) else None
        if key:
            new_map[str(key)] = str(m.get("value", ""))

    change_log: list[dict[str, Any]] = []
    for key, new_val in new_map.items():
        old_val = existing_map.get(key)
        if old_val is None:
            action = "added"
        elif old_val != new_val:
            action = "updated"
        else:
            action = "unchanged"
        change_log.append(
            {
                "key_name": key,
                "old_value": old_val,
                "new_value": new_val,
                "action": action,
                "object_type": "macro",
            }
        )

    merged = manual + [{"macro": k, "value": v} for k, v in new_map.items()]
    return merged, change_log


def should_preserve_visible_name(
    expected_visible_name: str,
    zabbix_visible_name: str,
    last_hmdl_visible_name: str | None,
) -> tuple[bool, str]:
    """
    If Zabbix visible name differs from last automation value, treat as manual edit.

    Returns (preserve, reason).
    """
    expected = (expected_visible_name or "").strip()
    current = (zabbix_visible_name or "").strip()
    last = (last_hmdl_visible_name or "").strip() if last_hmdl_visible_name else expected

    if current == expected:
        return False, ""
    if last and current != last:
        return True, "visible_name manually changed in Zabbix"
    return False, ""


def resolve_proxy_group_update(
    *,
    current_location: str,
    last_hmdl_location: str | None,
    expected_proxy_group_id: str,
    zabbix_proxy_group_id: str,
    last_hmdl_proxy_group_id: str | None,
) -> dict[str, Any]:
    """
    Decide whether to update proxy group on Zabbix host.

    - Location changed (vs HMDL log) -> update to expected
    - Location unchanged but Zabbix proxy != expected and != last HMDL -> manual, preserve
    - Otherwise update if Zabbix differs from expected
    """
    cur_loc = (current_location or "").strip()
    last_loc = (last_hmdl_location or "").strip()
    exp_pg = str(expected_proxy_group_id or "").strip()
    zbx_pg = str(zabbix_proxy_group_id or "").strip()
    last_pg = str(last_hmdl_proxy_group_id or "").strip() if last_hmdl_proxy_group_id else exp_pg

    location_changed = bool(last_loc) and cur_loc != last_loc
    if not last_loc and cur_loc:
        location_changed = False

    if location_changed:
        apply_update = exp_pg != zbx_pg
        return {
            "apply_update": apply_update,
            "proxy_manual_change_detected": False,
            "proxy_location_change": True,
            "expected_proxy_group_id": exp_pg,
            "actual_proxy_group_id": zbx_pg,
            "reason": "location_changed",
        }

    # Log recorded correct proxy; Zabbix diverged -> treat as manual override
    if last_pg and exp_pg == last_pg and zbx_pg != last_pg:
        return {
            "apply_update": False,
            "proxy_manual_change_detected": True,
            "proxy_location_change": False,
            "expected_proxy_group_id": exp_pg,
            "actual_proxy_group_id": zbx_pg,
            "reason": "proxy manually changed in Zabbix",
        }

    apply_update = exp_pg != zbx_pg
    return {
        "apply_update": apply_update,
        "proxy_manual_change_detected": False,
        "proxy_location_change": False,
        "expected_proxy_group_id": exp_pg,
        "actual_proxy_group_id": zbx_pg,
        "reason": "sync" if apply_update else "no_change",
    }
