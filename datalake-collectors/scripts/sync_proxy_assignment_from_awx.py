#!/usr/bin/env python3
"""Build proxy_assignment.yml from AWX NiFi_Prod_Envanter inventory groups."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

# AWX inventory group name -> proxy_assignment dc_code key
DEFAULT_GROUP_DC_MAP: dict[str, str] = {
    "NiFi_DC11": "DC11",
    "NiFi_DC12": "DC12",
    "NiFi_DC13_MAIN": "DC13",
    "NiFi_DC14": "DC14",
    "NiFi_DC15": "DC15",
    "NiFi_DC16": "DC16",
    "NiFi_DC17": "DC17",
    "NiFi_DC18": "DC18",
    "NiFi_DCAZ11": "AZ11",
    "NiFi_DCICT11": "ICT11",
    "NiFi_DCICT21": "ICT21",
    "NiFi_UZ11": "UZ11",
}

DEFAULT_PROXY_ASSIGNMENT = (
    Path(__file__).resolve().parents[1] / "mappings" / "proxy_assignment.yml"
)
DEFAULT_LOCAL_ENV = (
    Path(__file__).resolve().parents[3] / ".cursor" / "local-environment.local.json"
)


def load_awx_config(local_env_path: Path) -> dict[str, Any]:
    env = json.loads(local_env_path.read_text(encoding="utf-8"))
    awx = env.get("awx") or {}
    required = ("base_url", "admin_user", "admin_password")
    missing = [key for key in required if not awx.get(key)]
    if missing:
        raise RuntimeError(f"Missing AWX keys in {local_env_path}: {', '.join(missing)}")
    return awx


def awx_session(awx: dict[str, Any]) -> tuple[str, tuple[str, str]]:
    return awx["base_url"].rstrip("/"), (awx["admin_user"], awx["admin_password"])


def resolve_inventory_id(base: str, auth: tuple[str, str], awx: dict[str, Any]) -> int:
    if awx.get("inventory_nifi_prod_id"):
        return int(awx["inventory_nifi_prod_id"])
    inventory_name = awx.get("inventory_nifi_prod", "NiFi_Prod_Envanter")
    response = requests.get(
        f"{base}/api/v2/inventories/",
        auth=auth,
        params={"name": inventory_name},
        timeout=60,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise RuntimeError(f"AWX inventory not found: {inventory_name}")
    return int(results[0]["id"])


def fetch_awx_group_hosts(
    base: str,
    auth: tuple[str, str],
    inventory_id: int,
) -> dict[str, list[str]]:
    groups = requests.get(
        f"{base}/api/v2/inventories/{inventory_id}/groups/",
        auth=auth,
        params={"page_size": 200},
        timeout=60,
    )
    groups.raise_for_status()
    result: dict[str, list[str]] = {}
    for group in groups.json().get("results") or []:
        hosts = requests.get(
            f"{base}/api/v2/groups/{group['id']}/all_hosts/",
            auth=auth,
            params={"page_size": 100},
            timeout=60,
        )
        hosts.raise_for_status()
        result[group["name"]] = sorted(
            host["name"] for host in hosts.json().get("results") or []
        )
    return result


def build_proxy_assignment(
    group_hosts: dict[str, list[str]],
    group_dc_map: dict[str, str],
) -> dict[str, Any]:
    assignment: dict[str, Any] = {}
    unmapped_groups: list[str] = []

    for group_name, hosts in sorted(group_hosts.items()):
        dc_code = group_dc_map.get(group_name)
        if not dc_code:
            if hosts:
                unmapped_groups.append(group_name)
            continue
        if not hosts:
            continue

        proxies = []
        for idx, host in enumerate(hosts, start=1):
            proxies.append(
                {
                    "id": f"{dc_code}-NIFI{idx}",
                    "proxy_nifi_host": host,
                    "ssh_user": "root",
                    "conf_path": "/Datalake_Project/configuration_file.json",
                    "gitea_audit_path": (
                        f"proxies/{dc_code.lower()}/nifi{idx}/configuration_file.json"
                    ),
                }
            )
        assignment[dc_code] = {"dc_code": dc_code, "proxies": proxies}

    if unmapped_groups:
        raise RuntimeError(
            "AWX inventory groups have hosts but no dc_code mapping: "
            + ", ".join(sorted(unmapped_groups))
            + ". Update DEFAULT_GROUP_DC_MAP or pass --group-dc-map."
        )
    return assignment


def render_proxy_assignment_yaml(assignment: dict[str, Any]) -> str:
    header = (
        "---\n"
        "# DC / site code -> Proxy NiFi SSH targets (AWX inventory: NiFi_Prod_Envanter).\n"
        "# Host names are AWX inventory entries (IP addresses).\n"
        "# Regenerate with: python3 scripts/sync_proxy_assignment_from_awx.py\n\n"
    )
    return header + yaml.safe_dump(assignment, sort_keys=False, allow_unicode=True)


def summarize_assignment(assignment: dict[str, Any]) -> dict[str, Any]:
    proxies = []
    for dc_code, entry in assignment.items():
        for proxy in entry.get("proxies") or []:
            proxies.append(
                {
                    "dc_code": dc_code,
                    "proxy_id": proxy.get("id"),
                    "proxy_nifi_host": proxy.get("proxy_nifi_host"),
                }
            )
    return {
        "dc_count": len(assignment),
        "proxy_count": len(proxies),
        "proxies": proxies,
    }


def compare_assignments(current: dict[str, Any], updated: dict[str, Any]) -> dict[str, Any]:
    def flatten(data: dict[str, Any]) -> dict[str, str]:
        flat: dict[str, str] = {}
        for entry in data.values():
            for proxy in entry.get("proxies") or []:
                flat[str(proxy.get("id"))] = str(proxy.get("proxy_nifi_host") or "")
        return flat

    before = flatten(current)
    after = flatten(updated)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        proxy_id
        for proxy_id in set(before) & set(after)
        if before[proxy_id] != after[proxy_id]
    )
    return {
        "added": [{"proxy_id": pid, "host": after[pid]} for pid in added],
        "removed": [{"proxy_id": pid, "host": before[pid]} for pid in removed],
        "changed": [
            {"proxy_id": pid, "from": before[pid], "to": after[pid]} for pid in changed
        ],
        "unchanged_count": len(set(before) & set(after)) - len(changed),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync mappings/proxy_assignment.yml from AWX NiFi inventory"
    )
    parser.add_argument(
        "--local-env",
        default=str(DEFAULT_LOCAL_ENV),
        help="Path to .cursor/local-environment.local.json",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_PROXY_ASSIGNMENT),
        help="Target proxy_assignment.yml path",
    )
    parser.add_argument(
        "--group-dc-map",
        default="",
        help="Optional JSON object overriding AWX group -> dc_code mapping",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary and diff without writing the file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    local_env_path = Path(args.local_env)
    output_path = Path(args.output)

    group_dc_map = dict(DEFAULT_GROUP_DC_MAP)
    if args.group_dc_map:
        group_dc_map.update(json.loads(args.group_dc_map))

    awx = load_awx_config(local_env_path)
    base, auth = awx_session(awx)
    inventory_id = resolve_inventory_id(base, auth, awx)
    group_hosts = fetch_awx_group_hosts(base, auth, inventory_id)
    assignment = build_proxy_assignment(group_hosts, group_dc_map)
    summary = summarize_assignment(assignment)

    current: dict[str, Any] = {}
    if output_path.exists():
        current = yaml.safe_load(output_path.read_text(encoding="utf-8")) or {}

    diff = compare_assignments(current, assignment)
    print(json.dumps({"summary": summary, "diff": diff}, indent=2))

    if args.dry_run:
        return 0

    output_path.write_text(render_proxy_assignment_yaml(assignment), encoding="utf-8")
    print(f"Updated {output_path} ({summary['proxy_count']} proxies across {summary['dc_count']} DCs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
