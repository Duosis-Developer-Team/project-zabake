from matchers.keys import normalize_name
from reconcilers.base import ReconcilerBase


class IbmLparReconciler(ReconcilerBase):
    target_name = "ibm_lpar"
    source_name = "ibm_lpar"

    def datalake_key(self, row: dict) -> str:
        return normalize_name(row.get("lparname"))

    def netbox_key(self, row: dict) -> str:
        return normalize_name(row.get("name"))

    def is_relevant_netbox_row(self, row: dict) -> bool:
        name = normalize_name(row.get("name"))
        if not name:
            return False
        if self.ibm_lpar_name_set:
            return name in self.ibm_lpar_name_set
        cluster_name = normalize_name(row.get("cluster_name"))
        vmware_clusters = {normalize_name(item) for item in self.vmware_cluster_set if normalize_name(item)}
        nutanix_clusters = {normalize_name(item) for item in self.nutanix_cluster_set if normalize_name(item)}
        return cluster_name not in vmware_clusters and cluster_name not in nutanix_clusters
