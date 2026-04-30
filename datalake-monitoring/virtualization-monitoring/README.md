# Virtualization Monitoring

Phase-1 reconciliation module for:
- VMware VMs (`vm_metrics`)
- Nutanix VMs (`nutanix_vm_metrics`)
- IBM LPARs (`ibm_lpar_general`)

Comparison target:
- NetBox VM inventory table (`netbox_virtualization_vm`)

Execution model:
- AWX -> Ansible playbook -> Python reconciler CLI
