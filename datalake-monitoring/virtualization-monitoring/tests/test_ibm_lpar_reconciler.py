from reconcilers.ibm_lpar import IbmLparReconciler


def test_ibm_lpar_reconcile_name_match():
    datalake_rows = [{"lparname": "LPAR-A", "cluster": "srv-a", "customer_code": "cust"}]
    netbox_rows = [{"name": "lpar-a", "cluster_name": "srv-a", "custom_fields_musteri": "cust"}]
    result = IbmLparReconciler().reconcile(datalake_rows, netbox_rows)
    assert result["summary"]["in_both_strong"] == 1
