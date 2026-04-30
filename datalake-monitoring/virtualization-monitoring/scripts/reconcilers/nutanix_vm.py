from matchers.keys import normalize_name, normalize_uuid
from reconcilers.base import ReconcilerBase


class NutanixVmReconciler(ReconcilerBase):
    target_name = "nutanix"

    def datalake_key(self, row: dict) -> str:
        return normalize_uuid(row.get("vm_uuid")) or normalize_name(row.get("vm_name"))

    def netbox_key(self, row: dict) -> str:
        return normalize_uuid(row.get("custom_fields_uuid")) or normalize_name(row.get("name"))
