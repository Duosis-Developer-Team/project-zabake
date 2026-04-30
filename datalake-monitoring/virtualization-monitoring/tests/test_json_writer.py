from datetime import datetime, timezone
from pathlib import Path
import json

from outputs.json_writer import write_json_report


def test_json_writer_serializes_datetime(tmp_path: Path):
    payload = {
        "run_id": "test",
        "generated_at": datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
        "targets": [{"summary": {}, "details": [{"collection_time": datetime(2026, 4, 30, 12, 1)}]}],
    }
    output_file = write_json_report(str(tmp_path), "test", payload)
    parsed = json.loads(Path(output_file).read_text(encoding="utf-8"))
    assert parsed["generated_at"].startswith("2026-04-30T12:00:00")
    assert parsed["targets"][0]["details"][0]["collection_time"].startswith("2026-04-30T12:01:00")
