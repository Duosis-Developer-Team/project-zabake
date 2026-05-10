from reconcilers.vmware_vm import VmwareVmReconciler


def test_cluster_mismatch_single_row_output():
    datalake_rows = [
        {
            "uuid": "abc-1",
            "vmname": "cust-vm-01",
            "cluster": "km-cluster-a",
            "customer_code": "cust",
        }
    ]
    netbox_rows = [
        {
            "custom_fields_uuid": "abc-1",
            "name": "cust-vm-01",
            "cluster_name": "km-cluster-b",
            "custom_fields_musteri": "cust",
        }
    ]

    reconciler = VmwareVmReconciler(vmware_cluster_set={"km-cluster-a", "km-cluster-b"})
    result = reconciler.reconcile(datalake_rows, netbox_rows)

    assert result["summary"]["cluster_mismatch"] == 1
    assert result["summary"]["only_in_loki"] == 0
    assert result["summary"]["only_in_datalake"] == 0
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["status"] == "cluster_mismatch"
    assert row["datalake_cluster"] == "km-cluster-a"
    assert row["loki_cluster"] == "km-cluster-b"
    assert row["cluster_match"] == "N"
