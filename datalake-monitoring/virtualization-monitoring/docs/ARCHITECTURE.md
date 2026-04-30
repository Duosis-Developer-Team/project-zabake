# Architecture

AWX runs `playbooks/vm_reconciliation.yaml` on localhost.

Role workflow:
1. execute Python reconciliation
2. optionally upsert to reconciliation table
3. optionally send SMTP report

Python reconciliation:
- reads datalake VM/LPAR entities
- reads latest NetBox VM inventory snapshot
- matches and classifies differences
- writes machine-readable JSON report
