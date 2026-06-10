from reconcilers.ibm_host import IbmHostReconciler


def test_ibm_host_in_both():
    datalake_rows = [{"servername": "dc13-9009-abc", "mtm": "9009-22A"}]
    expected_rows = [{"servername": "dc13-9009-abc", "mtm": "9009-22A"}]
    result = IbmHostReconciler().reconcile(datalake_rows, expected_rows)
    assert result["target"] == "ibm_host"
    assert result["summary"]["in_both"] == 1
    assert result["summary"]["cluster_mismatch"] == 0
    assert result["summary"]["customer_mismatch"] == 0


def test_ibm_host_only_expected():
    result = IbmHostReconciler().reconcile([], [{"servername": "dc13-9009-xyz"}])
    assert result["summary"]["only_in_loki"] == 1


def test_ibm_host_only_datalake():
    result = IbmHostReconciler().reconcile([{"servername": "dc13-9009-zzz"}], [])
    assert result["summary"]["only_in_datalake"] == 1
