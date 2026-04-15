"""
NetBox DCIM location hierarchy helpers for zabbix-netbox sync.

Authoritative reference for unit tests; Ansible-embedded Python in
`roles/netbox_zabbix_sync/tasks/process_device.yml` and
`fetch_all_devices.yml` must stay aligned with this module.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Set

import requests


def resolve_root_location_name(
    device: Dict[str, Any],
    netbox_url: str,
    netbox_token: str,
    verify_ssl: bool,
    *,
    session: Optional[requests.Session] = None,
    max_depth: int = 32,
) -> str:
    """
    Return the root (top-level) NetBox location name for host groups / DC_ID.

    Walks parent pointers until ``parent`` is null. Falls back to site name
    when no location or on unrecoverable errors.
    """
    http = session or requests
    base = netbox_url.rstrip("/")
    headers = {
        "Authorization": f"Token {netbox_token}",
        "Accept": "application/json",
    }

    location_obj = device.get("location")
    if not location_obj:
        site = device.get("site") or {}
        return site.get("name", "") or ""

    current_id: Optional[int] = None
    current_name = ""

    if isinstance(location_obj, dict):
        current_id = location_obj.get("id")
        current_name = location_obj.get("name", "") or ""
    elif isinstance(location_obj, int):
        current_id = location_obj

    if not current_id:
        if isinstance(location_obj, dict) and location_obj.get("name"):
            return str(location_obj.get("name", ""))
        site = device.get("site") or {}
        return site.get("name", "") or ""

    visited: Set[int] = set()

    for _ in range(max_depth):
        if current_id in visited:
            break
        visited.add(current_id)

        try:
            response = http.get(
                f"{base}/api/dcim/locations/{current_id}/",
                headers=headers,
                verify=verify_ssl,
                timeout=10,
            )
            if response.status_code != 200:
                break
            loc_data = response.json()
            current_name = loc_data.get("name", current_name)
            parent = loc_data.get("parent")

            if parent is None:
                return current_name
            if isinstance(parent, dict):
                current_id = parent.get("id")
                if not current_id:
                    break
            elif isinstance(parent, int):
                current_id = parent
            else:
                break
        except Exception:
            break

    if current_name:
        return current_name
    if isinstance(location_obj, dict) and location_obj.get("name"):
        return str(location_obj.get("name", ""))
    site = device.get("site") or {}
    return site.get("name", "") or ""


def bfs_collect_descendant_location_ids(
    netbox_url: str,
    netbox_token: str,
    root_location_id: int,
    verify_ssl: bool,
    *,
    session: Optional[requests.Session] = None,
) -> List[int]:
    """
    Return ordered list of location IDs: root plus all descendants (BFS).

    Uses ``GET /api/dcim/locations/?parent_id=`` with pagination (``next``).
    """
    http = session or requests
    base = netbox_url.rstrip("/")
    headers = {
        "Authorization": f"Token {netbox_token}",
        "Accept": "application/json",
    }

    result: List[int] = [root_location_id]
    seen: Set[int] = {root_location_id}
    queue: deque[int] = deque([root_location_id])

    while queue:
        pid = queue.popleft()
        child_url: Optional[str] = (
            f"{base}/api/dcim/locations/?parent_id={pid}&limit=1000"
        )
        while child_url:
            response = http.get(
                child_url,
                headers=headers,
                verify=verify_ssl,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            for loc in data.get("results", []):
                cid = loc.get("id")
                if cid is None or cid in seen:
                    continue
                seen.add(cid)
                result.append(cid)
                queue.append(cid)
            child_url = data.get("next")

    return result
