#!/usr/bin/env python3
"""CLI: reconcile configuration_file.json IP fields from desired state JSON."""

import argparse
import json
import sys
from pathlib import Path

# Allow import from role module_utils when run standalone
_ROLE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROLE_DIR / "module_utils"))

from collector_core import (  # noqa: E402
    group_targets_by_proxy_and_conf,
    merge_vault_into_section,
    reconcile_proxy_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile proxy configuration JSON")
    parser.add_argument("--current", required=True, help="Path to current configuration_file.json")
    parser.add_argument("--collector-types", required=True, help="Path to collector_types.yml (JSON export)")
    parser.add_argument("--targets", required=True, help="Path to targets JSON list")
    parser.add_argument("--vault-sections", default="{}", help="JSON map conf_key -> vault defaults")
    parser.add_argument("--output", required=True, help="Output reconciled JSON path")
    parser.add_argument("--diff-output", help="Output diff JSON path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    current = json.loads(Path(args.current).read_text(encoding="utf-8"))
    collector_types = json.loads(Path(args.collector_types).read_text(encoding="utf-8"))
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    vault_sections = json.loads(args.vault_sections)

    grouped = group_targets_by_proxy_and_conf(targets)
    # This script handles one proxy at a time; targets should be filtered externally
    desired_by_conf: dict = {}
    for conf_key, ips in grouped.get(targets[0]["proxy_id"] if targets else "", {}).items():
        ctype = None
        meta = None
        for ct, m in collector_types.items():
            if m.get("conf_key") == conf_key:
                ctype, meta = ct, m
                break
        if not meta or meta.get("source_type") == "manual_only":
            continue
        vault = vault_sections.get(conf_key, {})
        desired_by_conf[conf_key] = merge_vault_into_section(
            current.get(conf_key, {}),
            vault,
            meta.get("other_fields"),
            ips,
            meta["ip_field"],
            meta.get("ip_format", "comma_string"),
            meta.get("secondary_fields"),
        )

    reconciled, diffs = reconcile_proxy_config(current, desired_by_conf, collector_types)

    if args.diff_output:
        Path(args.diff_output).write_text(json.dumps(diffs, indent=2), encoding="utf-8")

    if not args.dry_run:
        Path(args.output).write_text(
            json.dumps(reconciled, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        Path(args.output).write_text(
            json.dumps({"dry_run": True, "diffs": diffs, "would_write": reconciled}, indent=2),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
