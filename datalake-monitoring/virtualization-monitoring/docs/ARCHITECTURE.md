# Architecture

AWX runs `playbooks/vm_reconciliation.yaml` on localhost.

Role workflow:
1. execute Python reconciliation
2. optionally upsert to reconciliation table
3. optionally send SMTP report

Python reconciliation:
- reads datalake VM/LPAR entities
- reads latest NetBox VM inventory snapshot
- resolves Nutanix `cluster_uuid -> cluster_name`
- classifies environment:
  - `classic_vmware` when VMware cluster name contains `KM`
  - `hyperconv_vmware` for VMware clusters not containing `KM`
  - `hyperconv_nutanix` for Nutanix VM rows
  - `power_ibm` for IBM LPAR rows
- matches and classifies differences (`in_both`, `cluster_mismatch`, `customer_mismatch`, `only_in_loki`, `only_in_datalake`)
- writes JSON + summary JSON + combined CSV
- renders summary email body and sends SMTP email with CSV attachment
