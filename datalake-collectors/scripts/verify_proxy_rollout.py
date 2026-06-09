#!/usr/bin/env python3
"""Validate proxy_assignment.yml and print AWX rollout readiness per DC."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROLE_UTILS = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/module_utils"
)
sys.path.insert(0, str(ROLE_UTILS))

from collector_core import filter_proxy_ids, normalize_proxy_assignment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify proxy assignment for AWX rollout")
    parser.add_argument(
        "--proxy-assignment",
        default=str(
            Path(__file__).resolve().parents[1] / "mappings/proxy_assignment.yml"
        ),
    )
    parser.add_argument("--dc-filter", default="", help="Optional DC code filter")
    args = parser.parse_args()

    data = yaml.safe_load(Path(args.proxy_assignment).read_text(encoding="utf-8")) or {}
    dc_map, lookup = normalize_proxy_assignment(data)
    proxy_ids = filter_proxy_ids(lookup, args.dc_filter)

    report = []
    for pid in proxy_ids:
        cfg = lookup[pid]
        host = cfg.get("proxy_nifi_host", "")
        ready = host and "REPLACE_" not in host
        report.append(
            {
                "proxy_id": pid,
                "dc_code": cfg.get("dc_code"),
                "proxy_nifi_host": host,
                "ssh_user": cfg.get("ssh_user"),
                "ready_for_rollout": ready,
            }
        )

    summary = {
        "dc_map": dc_map,
        "total_proxies": len(report),
        "ready_proxies": sum(1 for r in report if r["ready_for_rollout"]),
        "proxies": report,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["ready_proxies"] == summary["total_proxies"] else 1


if __name__ == "__main__":
    sys.exit(main())
