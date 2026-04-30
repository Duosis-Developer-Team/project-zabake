import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


def _json_default_serializer(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def write_json_report(output_dir: str, run_id: str, payload: dict) -> str:
    path = Path(output_dir) / f"vm_reconciliation_{run_id}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, default=_json_default_serializer),
        encoding="utf-8",
    )
    return str(path)
