#!/usr/bin/env python3
"""Fetch NetBox platforms or devices and emit JSON for Ansible."""

import argparse
import json
import sys

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def fetch_paginated(session, url: str, verify_ssl: bool) -> list:
    results = []
    next_url = url
    while next_url:
        resp = session.get(next_url, verify=verify_ssl, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        next_url = data.get("next")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--netbox-url", required=True)
    parser.add_argument("--netbox-token", required=True)
    parser.add_argument("--entity", choices=["platforms", "devices"], required=True)
    parser.add_argument("--verify-ssl", default="false")
    parser.add_argument("--location-filter", default="")
    args = parser.parse_args()

    base = args.netbox_url.rstrip("/")
    session = requests.Session()
    session.headers.update(
        {"Authorization": f"Token {args.netbox_token}", "Accept": "application/json"}
    )
    verify = args.verify_ssl.lower() == "true"
    location_filter = (args.location_filter or "").strip().lower()

    if args.entity == "platforms":
        url = f"{base}/api/dcim/platforms/?limit=100&cf_izlenmeli=Evet&cf_izlenmeli=null"
        items = fetch_paginated(session, url, verify)
    else:
        url = f"{base}/api/dcim/devices/?limit=100&status=active"
        items = fetch_paginated(session, url, verify)

    if location_filter:
        filtered = []
        for item in items:
            cf = item.get("custom_fields") or {}
            site = (cf.get("Site") or cf.get("DC") or "").lower()
            loc = ""
            if item.get("location"):
                loc = (item["location"].get("name") or "").lower()
            if location_filter in site or location_filter in loc:
                filtered.append(item)
        items = filtered

    json.dump(items, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
