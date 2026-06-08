#!/usr/bin/env python3
"""Extract Gitea vault defaults.yml tree from production configuration_file.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_collector_types(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def excluded_fields(meta: dict) -> set[str]:
    """Fields managed by NetBox reconcile or computed secondary fields."""
    excluded: set[str] = set()
    ip_field = meta.get("ip_field")
    if ip_field:
        excluded.add(ip_field)
    secondary = meta.get("secondary_fields") or {}
    excluded.update(secondary.keys())
    return excluded


def extract_vault_section(section: dict, meta: dict) -> dict:
    if meta.get("source_type") == "manual_only":
        return dict(section)

    out = {}
    skip = excluded_fields(meta)
    for key, value in section.items():
        if key in skip:
            continue
        out[key] = value
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build vault repo from configuration_file.json")
    parser.add_argument("--config", required=True, help="Path to configuration_file.json")
    parser.add_argument(
        "--collector-types",
        required=True,
        help="Path to collector_types.yml",
    )
    parser.add_argument("--output-dir", required=True, help="Vault repo output directory")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    collector_types = load_collector_types(Path(args.collector_types))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for _ctype, meta in collector_types.items():
        conf_key = meta.get("conf_key")
        vault_key = meta.get("vault_key")
        if not conf_key or not vault_key:
            continue
        section = config.get(conf_key)
        if not section:
            continue

        vault_data = extract_vault_section(section, meta)
        if not vault_data:
            continue

        vault_dir = output_dir / vault_key
        vault_dir.mkdir(parents=True, exist_ok=True)
        defaults_path = vault_dir / "defaults.yml"
        defaults_path.write_text(
            yaml.safe_dump(vault_data, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        created.append(vault_key)

    readme = output_dir / "README.md"
    readme.write_text(
        "# datalake-collectors-vault (Gitea private)\n\n"
        "Generated from DC13 production configuration_file.json.\n"
        "Do not mirror to GitHub.\n",
        encoding="utf-8",
    )

    print(f"Created {len(created)} vault directories: {', '.join(sorted(created))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
