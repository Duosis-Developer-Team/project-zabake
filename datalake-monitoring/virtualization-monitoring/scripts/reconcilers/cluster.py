from matchers.keys import normalize_name
from reconcilers.base import ReconcilerBase


class ClusterReconciler(ReconcilerBase):
    """Cluster-level coverage: is each expected cluster actually collected?

    `source` is the platform ('vmware' | 'nutanix'); target_name is
    '<source>_cluster'. Presence is the only thing that matters, so
    cluster/customer sub-matching is disabled.
    """

    def __init__(self, source: str) -> None:
        super().__init__()
        self.source_name = source
        self.target_name = f"{source}_cluster"

    def datalake_key(self, row: dict) -> str:
        return normalize_name(row.get("cluster_name"))

    def netbox_key(self, row: dict) -> str:
        return normalize_name(row.get("cluster_name"))

    def cluster_matches(self, datalake: dict, netbox: dict) -> bool:
        return True

    def customer_matches(self, datalake: dict, netbox: dict) -> bool:
        return True
