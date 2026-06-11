import json
import types
from pathlib import Path

import main


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def close(self):
        pass


def test_upsert_coverage_routes_targets_to_correct_tables(tmp_path, monkeypatch):
    payload = {
        "run_id": "run-1",
        "window_days": 7,
        "coverage_targets": [
            {"target": "vmware_cluster", "summary": {}, "details": []},
            {"target": "nutanix_cluster", "summary": {}, "details": []},
            {"target": "ibm_host", "summary": {}, "details": []},
        ],
    }
    input_file = tmp_path / "payload.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")

    cluster_calls = []
    ibm_calls = []
    monkeypatch.setattr(main, "load_settings", lambda: types.SimpleNamespace(
        reconciliation_db=None))
    monkeypatch.setattr(main, "connect", lambda _cfg: FakeConn())
    monkeypatch.setattr(main, "_run_sql_file", lambda conn, filename: None)
    monkeypatch.setattr(
        main, "upsert_cluster_coverage",
        lambda conn, table, source, tp: cluster_calls.append((table, source)),
    )
    monkeypatch.setattr(
        main, "upsert_ibm_host_coverage",
        lambda conn, table, tp: ibm_calls.append(table),
    )

    args = types.SimpleNamespace(
        input_file=str(input_file),
        clusters_table="hmdl.hmdl_datalake_coverage_cluster",
        ibm_host_table="hmdl.hmdl_datalake_coverage_ibm_host",
    )
    result = main.run_upsert_coverage(args)

    assert result["status"] == "ok"
    assert ("hmdl.hmdl_datalake_coverage_cluster", "vmware") in cluster_calls
    assert ("hmdl.hmdl_datalake_coverage_cluster", "nutanix") in cluster_calls
    assert ibm_calls == ["hmdl.hmdl_datalake_coverage_ibm_host"]
