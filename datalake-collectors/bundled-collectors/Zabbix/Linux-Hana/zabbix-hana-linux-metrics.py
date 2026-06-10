#!/usr/bin/env python3
"""Zabbix Hana Linux host metrics collector for NiFi."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.hana_linux_parser import parse_hana_linux_items
from lib.template_filter import filter_linux_agent_hosts
from lib.zabbix_client import ZabbixClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def build_api_url(ip: str | None, url: str | None) -> str:
    if url:
        return url
    if not ip:
        raise ValueError("Either --url or --ip must be provided")
    if ip.startswith("http://") or ip.startswith("https://"):
        return ip if ip.endswith("api_jsonrpc.php") else f"{ip.rstrip('/')}/api_jsonrpc.php"
    return f"http://{ip}/api_jsonrpc.php"


def main() -> None:
    parser = argparse.ArgumentParser(description="Zabbix Hana Linux host metrics collector")
    parser.add_argument("--ip", required=False, help="Zabbix server IP or full API URL")
    parser.add_argument("--url", required=False, help="Zabbix API URL")
    parser.add_argument("--user", required=True, help="Zabbix username")
    parser.add_argument("--password", required=True, help="Zabbix password")
    parser.add_argument("--group", default="Hana Linux", help="Zabbix host group name")
    parser.add_argument("--host-batch-size", type=int, default=20, help="Hosts per item.get batch")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout in seconds")
    parser.add_argument("--limit-hosts", type=int, default=None, help="Limit hosts for testing")
    parser.add_argument("--output", required=False, help="Optional output file path")
    parser.add_argument(
        "--include-all-hosts",
        action="store_true",
        help="Skip Linux agent template filter (debug only)",
    )
    args = parser.parse_args()

    api_url = build_api_url(args.ip, args.url)
    collection_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    client = ZabbixClient(
        api_url=api_url,
        username=args.user,
        password=args.password,
        timeout=args.timeout,
        host_batch_size=args.host_batch_size,
    )

    results: list[dict] = []
    try:
        client.login()
        group_id = client.get_group_id(args.group)
        hosts = client.get_hosts(group_id, limit_hosts=args.limit_hosts)
        if not args.include_all_hosts:
            hosts = filter_linux_agent_hosts(hosts)
        logger.info("Processing %s hosts from group '%s'", len(hosts), args.group)

        host_ids = [host["hostid"] for host in hosts]
        items_by_host = client.get_items_for_hosts(host_ids)

        for host in hosts:
            host_items = items_by_host.get(host["hostid"], [])
            results.append(
                parse_hana_linux_items(host, host_items, collection_timestamp)
            )
    finally:
        client.logout()

    logger.info("Generated %s records", len(results))
    json_data = json.dumps(results, ensure_ascii=False, separators=(",", ":"))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(json_data)
        logger.info("Wrote output to %s", args.output)
    else:
        print(json_data)


if __name__ == "__main__":
    main()
