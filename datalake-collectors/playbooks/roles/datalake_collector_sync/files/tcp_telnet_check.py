#!/usr/bin/env python3
"""ICMP ping and TCP port connectivity checks for collector targets."""

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


def icmp_ping(host: str, count: int = 3, timeout_sec: int = 1) -> dict:
    host_clean = host.split("/")[0]
    try:
        proc = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout_sec), host_clean],
            capture_output=True,
            text=True,
            timeout=count * timeout_sec + 5,
        )
        ok = proc.returncode == 0
        latency_ms = None
        if ok and "time=" in proc.stdout:
            for line in proc.stdout.splitlines():
                if "time=" in line:
                    part = line.split("time=")[1].split()[0]
                    try:
                        latency_ms = int(float(part.replace("ms", "")))
                    except ValueError:
                        pass
                    break
        return {
            "check_type": "icmp",
            "port": None,
            "status": "ok" if ok else "unreachable",
            "latency_ms": latency_ms,
            "error_text": None if ok else (proc.stderr or proc.stdout or "ping failed")[:500],
        }
    except subprocess.TimeoutExpired:
        return {
            "check_type": "icmp",
            "port": None,
            "status": "timeout",
            "latency_ms": None,
            "error_text": "ping timeout",
        }
    except FileNotFoundError:
        return {
            "check_type": "icmp",
            "port": None,
            "status": "skipped",
            "latency_ms": None,
            "error_text": "ping command not found",
        }


def tcp_check(host: str, port: int, timeout_sec: int = 3) -> dict:
    host_clean = host.split("/")[0]
    start = time.monotonic()
    try:
        with socket.create_connection((host_clean, port), timeout=timeout_sec):
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "check_type": "telnet",
                "port": port,
                "status": "ok",
                "latency_ms": latency_ms,
                "error_text": None,
            }
    except socket.timeout:
        return {
            "check_type": "telnet",
            "port": port,
            "status": "timeout",
            "latency_ms": None,
            "error_text": f"connection timeout on port {port}",
        }
    except ConnectionRefusedError:
        return {
            "check_type": "telnet",
            "port": port,
            "status": "refused",
            "latency_ms": None,
            "error_text": f"connection refused on port {port}",
        }
    except OSError as exc:
        return {
            "check_type": "telnet",
            "port": port,
            "status": "unreachable",
            "latency_ms": None,
            "error_text": str(exc)[:500],
        }


def check_target(target: dict, icmp_count: int, icmp_timeout: int, tcp_timeout: int) -> list[dict]:
    ip = target["ip"]
    ports = target.get("check_ports") or []
    results = [icmp_ping(ip, icmp_count, icmp_timeout)]
    for port in ports:
        results.append(tcp_check(ip, int(port), tcp_timeout))
    return results


def summarize_checks(check_rows: list[dict]) -> str:
    if any(r["status"] in ("unreachable", "timeout", "refused") for r in check_rows if r["check_type"] == "icmp"):
        return "icmp_fail"
    if any(r["status"] != "ok" and r["check_type"] == "telnet" for r in check_rows):
        return "telnet_fail"
    if all(r["status"] in ("ok", "skipped") for r in check_rows):
        return "ok"
    return "partial"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True, help="JSON file with target list")
    parser.add_argument("--output", required=True, help="JSON output path")
    parser.add_argument("--icmp-count", type=int, default=3)
    parser.add_argument("--icmp-timeout", type=int, default=1)
    parser.add_argument("--tcp-timeout", type=int, default=3)
    parser.add_argument("--check-phase", default="post_reconcile")
    args = parser.parse_args()

    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    output_rows = []
    for t in targets:
        checks = check_target(t, args.icmp_count, args.icmp_timeout, args.tcp_timeout)
        for c in checks:
            output_rows.append(
                {
                    "ip": t["ip"],
                    "proxy_id": t.get("proxy_id"),
                    "collector_type": t.get("collector_type"),
                    "conf_key": t.get("conf_key"),
                    "check_phase": args.check_phase,
                    **c,
                    "target_status": summarize_checks(checks),
                }
            )
    Path(args.output).write_text(json.dumps(output_rows, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
