from matchers.keys import normalize_name, normalize_uuid
from reconcilers.base import ReconcilerBase


class VmwareVmReconciler(ReconcilerBase):
    target_name = "vmware"
    source_name = "vmware"

    def datalake_key(self, row: dict) -> str:
        return normalize_uuid(row.get("uuid")) or normalize_name(row.get("vmname"))

    def netbox_key(self, row: dict) -> str:
        return normalize_uuid(row.get("custom_fields_uuid")) or normalize_name(row.get("name"))

    def is_relevant_netbox_row(self, row: dict) -> bool:
        if not self.vmware_cluster_set:
            return True
        cluster_name = normalize_name(row.get("cluster_name"))
        if not cluster_name:
            return False
        normalized_vmware_clusters = {normalize_name(item) for item in self.vmware_cluster_set if normalize_name(item)}
        return cluster_name in normalized_vmware_clusters
