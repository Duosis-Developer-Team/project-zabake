# Virtualization Monitoring

VM/LPAR reconciliation module for:
- VMware VMs (`vm_metrics`)
- Nutanix VMs (`nutanix_vm_metrics`)
- IBM LPARs (`ibm_lpar_general`)

Single source of truth:
- Loki / NetBox VM inventory table (`discovery_netbox_virtualization_vm`)

Customer code behavior:
- explicit customer columns are not required
- customer code is derived from VM/LPAR name prefix when needed

Execution model:
- AWX -> Ansible playbook -> Python reconciler CLI

Outputs:
- JSON report: `vm_reconciliation_<run_id>.json`
- Summary JSON: `vm_reconciliation_<run_id>_summary.json`
- Combined CSV attachment candidate: `vm_reconciliation_<run_id>.csv`
- Email body files: `vm_reconciliation_<run_id>.html` and `vm_reconciliation_<run_id>.txt`

Status values:
- `in_both`
- `cluster_mismatch`
- `customer_mismatch`
- `only_in_loki`
- `only_in_datalake`
