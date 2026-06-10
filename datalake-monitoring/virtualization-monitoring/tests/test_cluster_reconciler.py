from reconcilers.cluster import ClusterReconciler


def test_cluster_in_both_when_expected_and_collected():
    datalake_rows = [{"cluster_name": "dc13-km-cl-01", "datacenter": "DC13"}]
    expected_rows = [{"cluster_name": "dc13-km-cl-01"}]
    result = ClusterReconciler("vmware").reconcile(datalake_rows, expected_rows)
    assert result["target"] == "vmware_cluster"
    assert result["summary"]["in_both"] == 1
    assert result["summary"]["only_in_datalake"] == 0
    assert result["summary"]["only_in_loki"] == 0


def test_cluster_only_expected_when_not_collected():
    expected_rows = [{"cluster_name": "dc13-km-cl-09"}]
    result = ClusterReconciler("vmware").reconcile([], expected_rows)
    assert result["summary"]["only_in_loki"] == 1


def test_cluster_only_datalake_when_not_in_inventory():
    datalake_rows = [{"cluster_name": "ahv-prod-a", "datacenter": "DC13"}]
    result = ClusterReconciler("nutanix").reconcile(datalake_rows, [])
    assert result["target"] == "nutanix_cluster"
    assert result["summary"]["only_in_datalake"] == 1


def test_cluster_never_reports_cluster_or_customer_mismatch():
    # Coverage reconciliation only cares about presence, not sub-cluster/customer match.
    datalake_rows = [{"cluster_name": "dc13-km-cl-01", "datacenter": "DC13"}]
    expected_rows = [{"cluster_name": "dc13-km-cl-01"}]
    result = ClusterReconciler("vmware").reconcile(datalake_rows, expected_rows)
    assert result["summary"]["cluster_mismatch"] == 0
    assert result["summary"]["customer_mismatch"] == 0
