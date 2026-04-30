from matchers.keys import normalize_name, normalize_uuid
from reconcilers.base import ReconcilerBase


class NutanixVmReconciler(ReconcilerBase):
    target_name = "nutanix"
    source_name = "nutanix"

    def datalake_key(self, row: dict) -> str:
        return normalize_uuid(row.get("vm_uuid")) or normalize_name(row.get("vm_name"))

    def netbox_key(self, row: dict) -> str:
        return normalize_uuid(row.get("custom_fields_uuid")) or normalize_name(row.get("name"))

    def is_relevant_netbox_row(self, row: dict) -> bool:
        if not self.nutanix_cluster_set:
            return True
        cluster_name = normalize_name(row.get("cluster_name"))
        if not cluster_name:
            return False
        normalized_nutanix_clusters = {normalize_name(item) for item in self.nutanix_cluster_set if normalize_name(item)}
        return cluster_name in normalized_nutanix_clusters
