#!/usr/bin/env python3
"""Reconcile configuration per proxy from targets + vault + current config."""

import argparse
import json
import sys
from pathlib import Path

_ROLE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROLE_DIR / "module_utils"))

import yaml  # noqa: E402

from collector_core import (  # noqa: E402
    group_targets_by_proxy_and_conf,
    merge_vault_into_section,
    reconcile_proxy_config,
)


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def vault_for_conf_key(conf_key: str, collector_types: dict, vault_by_dir: dict) -> dict:
    for _ctype, meta in collector_types.items():
        if meta.get("conf_key") == conf_key:
            vk = meta.get("vault_key", "")
            return vault_by_dir.get(vk, {})
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    parser.add_argument("--targets", required=True)
    parser.add_argument("--collector-types", required=True)
    parser.add_argument("--vault-json", default="{}", help="Path to vault_by_dir.json file")
    parser.add_argument("--proxy-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--diff-output", required=True)
    args = parser.parse_args()

    current = json.loads(Path(args.current).read_text(encoding="utf-8"))
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    collector_types = load_yaml(args.collector_types)
    vault_path = Path(args.vault_json)
    vault_by_dir = json.loads(vault_path.read_text(encoding="utf-8")) if vault_path.exists() else {}

    proxy_targets = [t for t in targets if t.get("proxy_id") == args.proxy_id]
    grouped = group_targets_by_proxy_and_conf(proxy_targets)
    conf_ips = grouped.get(args.proxy_id, {})

    desired_by_conf = {}
    for conf_key, ips in conf_ips.items():
        meta = None
        for _ct, m in collector_types.items():
            if m.get("conf_key") == conf_key:
                meta = m
                break
        if not meta or meta.get("source_type") == "manual_only":
            continue
        vault = vault_for_conf_key(conf_key, collector_types, vault_by_dir)
        desired_by_conf[conf_key] = merge_vault_into_section(
            current.get(conf_key, {}),
            vault,
            meta.get("other_fields"),
            ips,
            meta["ip_field"],
            meta.get("ip_format", "comma_string"),
            meta.get("secondary_fields"),
        )

    # Inject manual-only sections from vault (full replace of section keys from vault only)
    for _ct, meta in collector_types.items():
        if meta.get("source_type") != "manual_only":
            continue
        ck = meta.get("conf_key")
        vk = meta.get("vault_key", "")
        if vk in vault_by_dir:
            desired_by_conf[ck] = copy_manual_section(current.get(ck, {}), vault_by_dir[vk])

    reconciled, diffs = reconcile_proxy_config(current, desired_by_conf, collector_types)
    for d in diffs:
        d["proxy_id"] = args.proxy_id

    Path(args.output).write_text(
        json.dumps(reconciled, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    Path(args.diff_output).write_text(json.dumps(diffs, indent=2), encoding="utf-8")
    return 0


def copy_manual_section(current: dict, vault: dict) -> dict:
    """Manual-only: merge vault over current, do not touch IP fields."""
    out = dict(current) if current else {}
    out.update(vault)
    return out


if __name__ == "__main__":
    sys.exit(main())
