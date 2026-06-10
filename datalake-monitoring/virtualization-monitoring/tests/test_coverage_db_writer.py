from outputs.coverage_db_writer import (
    coverage_flags,
    coverage_status,
    upsert_cluster_coverage,
    upsert_ibm_host_coverage,
)
from reconcilers.cluster import ClusterReconciler
from reconcilers.ibm_host import IbmHostReconciler


class FakeCursor:
    def __init__(self, sink):
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, query, params):
        self._sink.append((query, params))


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.committed = False

    def cursor(self):
        return FakeCursor(self.calls)

    def commit(self):
        self.committed = True


def test_coverage_status_maps_base_statuses_to_coverage_vocab():
    assert coverage_status("in_both") == "in_both"
    assert coverage_status("only_in_datalake") == "only_datalake"
    assert coverage_status("only_in_loki") == "only_expected"


def test_coverage_flags_expected_and_collected():
    assert coverage_flags("in_both") == (True, True)
    assert coverage_flags("only_expected") == (True, False)
    assert coverage_flags("only_datalake") == (False, True)


def test_upsert_cluster_coverage_writes_expected_collected_rows():
    dl = [{"cluster_name": "dc13-km-cl-01", "datacenter": "DC13", "collection_time": "2026-06-10T00:00:00"}]
    exp = [{"cluster_name": "dc13-km-cl-01"}, {"cluster_name": "dc13-km-cl-09"}]
    result = ClusterReconciler("vmware").reconcile(dl, exp)

    conn = FakeConnection()
    upsert_cluster_coverage(conn, "hmdl.hmdl_datalake_monitoring_clusters", "run-1", "vmware", result, 7)

    assert conn.committed is True
    by_cluster = {params[2]: params for _q, params in conn.calls}
    # params: (run_id, source, cluster_name, cluster_uuid, datacenter, expected, collected, status, ...)
    assert by_cluster["dc13-km-cl-01"][5:8] == (True, True, "in_both")
    assert by_cluster["dc13-km-cl-09"][5:8] == (True, False, "only_expected")


def test_upsert_ibm_host_coverage_marks_only_datalake():
    dl = [{"servername": "dc13-9009-zzz", "mtm": "9009-22A", "collection_time": "2026-06-10T00:00:00"}]
    result = IbmHostReconciler().reconcile(dl, [])

    conn = FakeConnection()
    upsert_ibm_host_coverage(conn, "hmdl.hmdl_datalake_monitoring_ibm_host", "run-1", result, 7)

    assert conn.committed is True
    _q, params = conn.calls[0]
    # params: (run_id, servername, mtm, expected, collected, status, ...)
    assert params[1] == "dc13-9009-zzz"
    assert params[3:6] == (False, True, "only_datalake")
