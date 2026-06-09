#!/usr/bin/env python3
"""Run connectivity checks on IPs that would be removed during reconcile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROLE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROLE_DIR / "module_utils"))

import yaml  # noqa: E402

from collector_core import (  # noqa: E402
    group_targets_by_proxy_and_conf,
    parse_ip_list,
    reconcile_section_ips,
)

# Reuse check helpers from tcp_telnet_check
sys.path.insert(0, str(_ROLE_DIR / "files"))
from tcp_telnet_check import check_target, summarize_checks  # noqa: E402


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def removal_candidates(
    current: dict,
    targets: list[dict],
    collector_types: dict,
    proxy_id: str,
) -> list[dict]:
    """Build check targets for IPs present in config but absent from NetBox desired set."""
    proxy_targets = [t for t in targets if t.get("proxy_id") == proxy_id]
    grouped = group_targets_by_proxy_and_conf(proxy_targets)
    desired_by_conf = grouped.get(proxy_id, {})
    checks: list[dict] = []

    for _ctype, meta in collector_types.items():
        if meta.get("source_type") in (None, "manual_only"):
            continue
        conf_key = meta.get("conf_key")
        ip_field = meta.get("ip_field")
        if not conf_key or not ip_field:
            continue
        current_section = current.get(conf_key, {})
        current_ips = parse_ip_list(current_section.get(ip_field, ""))
        desired_ips = desired_by_conf.get(conf_key, [])
        _, diffs = reconcile_section_ips(
            current_section,
            desired_ips,
            ip_field,
            meta.get("ip_format", "comma_string"),
            meta.get("secondary_fields"),
        )
        for diff in diffs:
            if diff.get("action") != "removed":
                continue
            ip = diff["ip"]
            checks.append(
                {
                    "ip": ip,
                    "proxy_id": proxy_id,
                    "collector_type": _ctype,
                    "conf_key": conf_key,
                    "check_ports": meta.get("check_ports") or [],
                }
            )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--targets", required=True)
    parser.add_argument("--collector-types", required=True)
    parser.add_argument("--proxy-id", required=True)
    parser.add_argument("--output", required=True, help="Connectivity map JSON: ip -> status")
    parser.add_argument("--checks-output", help="Detailed check rows JSON")
    parser.add_argument("--icmp-count", type=int, default=3)
    parser.add_argument("--icmp-timeout", type=int, default=1)
    parser.add_argument("--tcp-timeout", type=int, default=3)
    args = parser.parse_args()

    current = json.loads(Path(args.current).read_text(encoding="utf-8"))
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    collector_types = load_yaml(Path(args.collector_types))

    candidates = removal_candidates(current, targets, collector_types, args.proxy_id)
    connectivity: dict[str, str] = {}
    detail_rows: list[dict] = []

    for target in candidates:
        ip = target["ip"]
        checks = check_target(
            target, args.icmp_count, args.icmp_timeout, args.tcp_timeout
        )
        status = summarize_checks(checks)
        connectivity[ip] = status
        for row in checks:
            detail_rows.append(
                {
                    **row,
                    "ip": ip,
                    "proxy_id": args.proxy_id,
                    "collector_type": target.get("collector_type"),
                    "conf_key": target.get("conf_key"),
                    "check_phase": "pre_reconcile",
                    "target_status": status,
                }
            )

    Path(args.output).write_text(json.dumps(connectivity, indent=2), encoding="utf-8")
    if args.checks_output:
        Path(args.checks_output).write_text(
            json.dumps(detail_rows, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
