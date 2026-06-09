#!/usr/bin/env python3
"""Build rsync manifest for collector script deployment to Proxy NiFi nodes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def remote_dir(script_path: str, remote_base: str) -> str:
    rel = script_path.replace("datalake/collectors/", "").replace("\\", "/")
    rel = rel.rstrip("/")
    if not rel:
        return remote_base
    parent = Path(rel).parent
    if str(parent) == ".":
        return remote_base
    return f"{remote_base.rstrip('/')}/{parent.as_posix()}"


def local_dir(script_path: str, src_root: Path) -> Path:
    rel = script_path.replace("datalake/collectors/", "").replace("\\", "/")
    rel = rel.rstrip("/")
    parent = Path(rel).parent
    if str(parent) == ".":
        return src_root
    return src_root / parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collector-types", required=True)
    parser.add_argument("--src", required=True, help="Local datalake/collectors root")
    parser.add_argument("--remote-base", default="/Datalake_Project")
    parser.add_argument("--types", required=True, help="Comma-separated collector type names")
    parser.add_argument("--manifest-output", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    collector_types = load_yaml(Path(args.collector_types))
    type_names = [t.strip() for t in args.types.split(",") if t.strip()]
    src_root = Path(args.src)
    deploy_paths: list[dict] = []
    seen: set[str] = set()

    for ctype in type_names:
        meta = collector_types.get(ctype, {})
        script_path = meta.get("script_path") or ""
        if not script_path or script_path.endswith("/"):
            continue
        local_path = local_dir(script_path, src_root)
        remote_path = remote_dir(script_path, args.remote_base)
        key = f"{local_path}|{remote_path}"
        if key in seen:
            continue
        seen.add(key)
        if not local_path.exists():
            print(f"warning: missing local collector path {local_path}", file=sys.stderr)
            continue
        deploy_paths.append(
            {
                "collector_type": ctype,
                "script_path": script_path,
                "src": str(local_path.resolve()),
                "dest": remote_path,
            }
        )

    manifest = {
        "dry_run": args.dry_run,
        "deploy_paths": deploy_paths,
        "count": len(deploy_paths),
    }
    Path(args.manifest_output).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"count": len(deploy_paths)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
