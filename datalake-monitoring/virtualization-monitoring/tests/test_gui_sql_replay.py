from sql_loader.gui_replay import build_gui_replay_snapshot


class DummyConnection:
    pass


def test_gui_sql_replay_internal_sql_snapshot(monkeypatch):
    calls = []

    def fake_fetch_all(_conn, query, params=()):
        calls.append((query, params))
        if "nutanix_vm_metrics" in query:
            return [{"count": 7}]
        if "vm_metrics" in query:
            return [{"count": 10}]
        return [{"count": 3}]

    monkeypatch.setattr("sql_loader.gui_replay.fetch_all", fake_fetch_all)
    snapshot = build_gui_replay_snapshot(DummyConnection(), 7)
    assert snapshot["source"] == "internal_sql_replay"
    assert snapshot["vmware_distinct_vm_count"] == 10
    assert snapshot["nutanix_distinct_vm_count"] == 7
    assert snapshot["ibm_distinct_lpar_count"] == 3
    assert len(calls) == 3
