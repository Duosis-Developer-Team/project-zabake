#!/usr/bin/env python3
"""HMDL collector schema: ensure tables, upsert targets, write logs."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None


DDL_STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS hmdl",
]


def connect(args):
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required for HMDL DB operations")
    return psycopg2.connect(
        host=args.db_host,
        port=args.db_port,
        dbname=args.db_name,
        user=args.db_user,
        password=args.db_password,
    )


def cmd_ensure_schema(conn) -> None:
    # project-zabake/SQL/datalake-collectors (role files -> playbooks -> datalake-collectors -> ..)
    sql_dir = Path(__file__).resolve().parents[4].parent / "SQL" / "datalake-collectors"
    files = [
        "collector_definition.sql",
        "collector_target.sql",
        "collector_sync_log.sql",
        "collector_diff_log.sql",
        "collector_check_log.sql",
    ]
    with conn.cursor() as cur:
        for ddl_file in files:
            path = sql_dir / ddl_file
            if path.exists():
                cur.execute(path.read_text(encoding="utf-8"))
    conn.commit()


def cmd_upsert_targets(conn, args) -> None:
    targets = json.loads(Path(args.targets_file).read_text(encoding="utf-8"))
    collector_types = json.loads(Path(args.collector_types_file).read_text(encoding="utf-8"))
    if isinstance(collector_types, dict) and not any(k in collector_types for k in ("VmWare", "Nutanix")):
        pass
    # collector_types may be raw yaml-exported; keys are collector type names
    with conn.cursor() as cur:
        for ctype, meta in collector_types.items():
            if not isinstance(meta, dict):
                continue
            cur.execute(
                """
                INSERT INTO hmdl.collector_definition
                    (collector_type, conf_key, script_path, ip_field, ip_format,
                     source_type, check_ports, vault_key)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (collector_type) DO UPDATE SET
                    conf_key = EXCLUDED.conf_key,
                    script_path = EXCLUDED.script_path,
                    ip_field = EXCLUDED.ip_field,
                    ip_format = EXCLUDED.ip_format,
                    source_type = EXCLUDED.source_type,
                    check_ports = EXCLUDED.check_ports,
                    vault_key = EXCLUDED.vault_key,
                    updated_at = NOW()
                """,
                (
                    ctype,
                    meta.get("conf_key", ctype),
                    meta.get("script_path"),
                    meta.get("ip_field"),
                    meta.get("ip_format"),
                    meta.get("source_type", "platform"),
                    meta.get("check_ports") or [],
                    meta.get("vault_key"),
                ),
            )
        conn.commit()

        for t in targets:
            cur.execute(
                "SELECT id FROM hmdl.collector_definition WHERE collector_type = %s",
                (t["collector_type"],),
            )
            row = cur.fetchone()
            if not row:
                continue
            cid = row[0]
            cur.execute(
                """
                INSERT INTO hmdl.collector_target
                    (collector_id, netbox_entity_id, host_entity_type, ip, dc_code,
                     proxy_id, entity_name, manufacturer, status, last_seen_in_netbox)
                VALUES (%s, %s, %s, %s::inet, %s, %s, %s, %s, 'active', NOW())
                ON CONFLICT (collector_id, ip, proxy_id) DO UPDATE SET
                    netbox_entity_id = EXCLUDED.netbox_entity_id,
                    host_entity_type = EXCLUDED.host_entity_type,
                    entity_name = EXCLUDED.entity_name,
                    manufacturer = EXCLUDED.manufacturer,
                    dc_code = EXCLUDED.dc_code,
                    status = 'active',
                    last_seen_in_netbox = NOW(),
                    updated_at = NOW()
                """,
                (
                    cid,
                    t.get("netbox_entity_id"),
                    t.get("host_entity_type", "platform"),
                    t["ip"],
                    t.get("dc_code"),
                    t["proxy_id"],
                    t.get("entity_name"),
                    t.get("manufacturer"),
                ),
            )
        conn.commit()


def cmd_write_diffs(conn, args) -> None:
    diffs = json.loads(Path(args.diffs_file).read_text(encoding="utf-8"))
    with conn.cursor() as cur:
        for d in diffs:
            cur.execute(
                """
                INSERT INTO hmdl.collector_diff_log
                    (run_id, proxy_id, conf_key, action, ip, reason)
                VALUES (%s, %s, %s, %s, %s::inet, %s)
                """,
                (
                    args.run_id,
                    d.get("proxy_id", ""),
                    d.get("conf_key"),
                    d.get("action"),
                    d.get("ip"),
                    d.get("reason"),
                ),
            )
        conn.commit()


def cmd_write_checks(conn, args) -> None:
    checks = json.loads(Path(args.checks_file).read_text(encoding="utf-8"))
    with conn.cursor() as cur:
        for c in checks:
            cur.execute(
                """
                INSERT INTO hmdl.collector_check_log
                    (run_id, proxy_id, ip, check_type, port, status, latency_ms, error_text)
                VALUES (%s, %s, %s::inet, %s, %s, %s, %s, %s)
                """,
                (
                    args.run_id,
                    c.get("proxy_id", ""),
                    c["ip"],
                    c["check_type"],
                    c.get("port"),
                    c["status"],
                    c.get("latency_ms"),
                    c.get("error_text"),
                ),
            )
            cur.execute(
                """
                UPDATE hmdl.collector_target SET
                    last_check_status = %s,
                    last_check_at = NOW()
                WHERE ip = %s::inet AND proxy_id = %s
                """,
                (c.get("target_status", c["status"]), c["ip"], c.get("proxy_id", "")),
            )
        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-host", required=True)
    parser.add_argument("--db-port", type=int, default=5432)
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-password", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure-schema")

    p_up = sub.add_parser("upsert-targets")
    p_up.add_argument("--targets-file", required=True)
    p_up.add_argument("--collector-types-file", required=True)

    p_d = sub.add_parser("write-diffs")
    p_d.add_argument("--run-id", required=True)
    p_d.add_argument("--diffs-file", required=True)

    p_c = sub.add_parser("write-checks")
    p_c.add_argument("--run-id", required=True)
    p_c.add_argument("--checks-file", required=True)

    args = parser.parse_args()
    conn = connect(args)
    try:
        if args.command == "ensure-schema":
            cmd_ensure_schema(conn)
        elif args.command == "upsert-targets":
            cmd_upsert_targets(conn, args)
        elif args.command == "write-diffs":
            cmd_write_diffs(conn, args)
        elif args.command == "write-checks":
            cmd_write_checks(conn, args)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
