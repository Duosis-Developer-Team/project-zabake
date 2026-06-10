#!/usr/bin/env python3
"""Compare current vs reconciled configuration_file.json (normalized JSON)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def normalized_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, help="Path to current config JSON")
    parser.add_argument("--reconciled", required=True, help="Path to reconciled config JSON")
    args = parser.parse_args()

    current_path = Path(args.current)
    reconciled_path = Path(args.reconciled)
    changed = normalized_json(current_path) != normalized_json(reconciled_path)
    print(json.dumps({"changed": changed}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
