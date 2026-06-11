#!/usr/bin/env python3
"""Backfill hmdl.proxy_node from prod sync logs and proxy_assignment.yml."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT.parents[1] / "SQL" / "datalake-collectors" / "proxy_node.sql"
YAML_FILE = ROOT / "mappings" / "proxy_assignment.yml"
HMDL_DB = (
    ROOT
    / "playbooks"
    / "roles"
    / "datalake_collector_sync"
    / "files"
    / "hmdl_collector_db.py"
)


def _load_yaml_proxies() -> dict[str, dict]:
    raw = yaml.safe_load(YAML_FILE.read_text(encoding="utf-8")) or {}
    by_id: dict[str, dict] = {}
    for _key, block in raw.items():
        if not isinstance(block, dict):
            continue
        dc_code = str(block.get("dc_code") or _key).upper()
        for proxy in block.get("proxies") or []:
            if not isinstance(proxy, dict) or not proxy.get("id"):
                continue
            pid = str(proxy["id"])
            by_id[pid] = {
                "dc_code": dc_code,
                "proxy_nifi_host": str(proxy.get("proxy_nifi_host") or ""),
                "ssh_user": str(proxy.get("ssh_user") or "root"),
                "conf_path": str(
                    proxy.get("conf_path") or "/Datalake_Project/configuration_file.json"
                ),
                "gitea_audit_path": str(proxy.get("gitea_audit_path") or ""),
            }
    return by_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-host", required=True)
    parser.add_argument("--db-port", type=int, default=5432)
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("psycopg2 required", file=sys.stderr)
        return 1

    yaml_proxies = _load_yaml_proxies()
    conn = psycopg2.connect(
        host=args.db_host,
        port=args.db_port,
        dbname=args.db_name,
        user=args.db_user,
        password=args.db_password,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_FILE.read_text(encoding="utf-8"))
        conn.commit()

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (proxy_id)
                    proxy_id,
                    run_id,
                    awx_job_id,
                    finished_at
                FROM hmdl.collector_sync_log
                WHERE dry_run = FALSE
                ORDER BY proxy_id, finished_at DESC NULLS LAST, id DESC
                """
            )
            sync_rows = [dict(r) for r in cur.fetchall()]

        upserted = 0
        skipped = 0
        for row in sync_rows:
            pid = str(row["proxy_id"])
            meta = yaml_proxies.get(pid)
            if not meta or not meta.get("proxy_nifi_host"):
                print(f"skip {pid}: missing proxy_assignment.yml entry", file=sys.stderr)
                skipped += 1
                continue
            if args.dry_run:
                print(json.dumps({"proxy_id": pid, **meta, "run_id": row["run_id"]}))
                upserted += 1
                continue
            cmd = [
                sys.executable,
                str(HMDL_DB),
                "--db-host",
                args.db_host,
                "--db-port",
                str(args.db_port),
                "--db-name",
                args.db_name,
                "--db-user",
                args.db_user,
                "--db-password",
                args.db_password,
                "upsert-proxy-node",
                "--run-id",
                str(row["run_id"]),
                "--proxy-id",
                pid,
                "--dc-code",
                meta["dc_code"],
                "--proxy-nifi-host",
                meta["proxy_nifi_host"],
                "--ssh-user",
                meta["ssh_user"],
                "--conf-path",
                meta["conf_path"],
                "--gitea-audit-path",
                meta["gitea_audit_path"],
                "--dry-run",
                "false",
                "--awx-job-id",
                str(row.get("awx_job_id") or ""),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(result.stderr or result.stdout, file=sys.stderr)
                return result.returncode
            upserted += 1

        print(f"backfill complete: upserted={upserted} skipped={skipped}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
