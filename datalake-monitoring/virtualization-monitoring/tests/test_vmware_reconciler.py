import json
from pathlib import Path

from reconcilers.vmware_vm import VmwareVmReconciler


def test_vmware_reconcile_strong_match():
    fixtures = Path(__file__).parent / "fixtures"
    datalake_rows = json.loads((fixtures / "vmware_rows.json").read_text(encoding="utf-8"))
    netbox_rows = json.loads((fixtures / "netbox_rows.json").read_text(encoding="utf-8"))
    result = VmwareVmReconciler().reconcile(datalake_rows, netbox_rows)
    assert result["summary"]["in_both_strong"] == 1
