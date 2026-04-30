from matchers.keys import normalize_name, normalize_uuid
from reconcilers.base import ReconcilerBase


class VmwareVmReconciler(ReconcilerBase):
    target_name = "vmware"

    def datalake_key(self, row: dict) -> str:
        return normalize_uuid(row.get("uuid")) or normalize_name(row.get("vmname"))

    def netbox_key(self, row: dict) -> str:
        return normalize_uuid(row.get("custom_fields_uuid")) or normalize_name(row.get("name"))
