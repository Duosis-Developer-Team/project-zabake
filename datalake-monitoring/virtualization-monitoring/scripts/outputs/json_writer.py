import json
from pathlib import Path


def write_json_report(output_dir: str, run_id: str, payload: dict) -> str:
    path = Path(output_dir) / f"vm_reconciliation_{run_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)
