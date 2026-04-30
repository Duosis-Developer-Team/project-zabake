# Virtualization Monitoring

Phase-1 reconciliation module for:
- VMware VMs (`vm_metrics`)
- Nutanix VMs (`nutanix_vm_metrics`)
- IBM LPARs (`ibm_lpar_general`)

Comparison target:
- NetBox VM inventory table (`discovery_netbox_virtualization_vm`)

Customer code behavior:
- explicit customer columns are not required
- customer code is derived from VM/LPAR name prefix when needed

Execution model:
- AWX -> Ansible playbook -> Python reconciler CLI
