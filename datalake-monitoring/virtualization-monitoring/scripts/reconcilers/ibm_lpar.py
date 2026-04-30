from matchers.keys import normalize_name
from reconcilers.base import ReconcilerBase


class IbmLparReconciler(ReconcilerBase):
    target_name = "ibm_lpar"

    def datalake_key(self, row: dict) -> str:
        return normalize_name(row.get("lparname"))

    def netbox_key(self, row: dict) -> str:
        return normalize_name(row.get("name"))
