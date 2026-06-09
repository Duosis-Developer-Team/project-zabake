#!/usr/bin/env python3
"""Export normalized proxy lookup JSON from proxy_assignment.yml."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROLE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROLE_DIR / "module_utils"))

import yaml  # noqa: E402

from collector_core import normalize_proxy_assignment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy-assignment", required=True)
    args = parser.parse_args()
    data = yaml.safe_load(Path(args.proxy_assignment).read_text(encoding="utf-8")) or {}
    _, lookup = normalize_proxy_assignment(data)
    print(json.dumps(lookup, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
