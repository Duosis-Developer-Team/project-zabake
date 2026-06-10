from matchers.keys import normalize_name
from reconcilers.base import ReconcilerBase


class IbmHostReconciler(ReconcilerBase):
    """Host-level coverage for IBM Power servers.

    Datalake (collected) = ibm_server_general.server_details_servername;
    expected = discovery_ibm_inventory.servername (asset_type='server').
    Match key is the physical server name; presence is all that matters.
    """

    target_name = "ibm_host"
    source_name = "ibm_host"

    def datalake_key(self, row: dict) -> str:
        return normalize_name(row.get("servername"))

    def netbox_key(self, row: dict) -> str:
        return normalize_name(row.get("servername"))

    def cluster_matches(self, datalake: dict, netbox: dict) -> bool:
        return True

    def customer_matches(self, datalake: dict, netbox: dict) -> bool:
        return True
