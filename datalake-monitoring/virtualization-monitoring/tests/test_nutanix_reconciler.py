from reconcilers.nutanix_vm import NutanixVmReconciler


def test_nutanix_reconcile_only_datalake():
    datalake_rows = [{"vm_uuid": "n1", "vm_name": "cust-nut-01", "cluster": "ahv-a"}]
    netbox_rows = []
    result = NutanixVmReconciler().reconcile(datalake_rows, netbox_rows)
    assert result["summary"]["only_in_datalake"] == 1
