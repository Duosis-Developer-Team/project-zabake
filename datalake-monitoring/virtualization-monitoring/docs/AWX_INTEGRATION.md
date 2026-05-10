# AWX Integration

Job template:
- Project: `project-zabake`
- Playbook: `datalake-monitoring/virtualization-monitoring/playbooks/vm_reconciliation.yaml`
- Inventory: localhost inventory

Required variables:
- `datalake_db.host`
- `datalake_db.name`
- `datalake_db.user`
- `datalake_db.password`

Optional flags:
- `mail.enabled`
- `reconciliation_db.enabled`
- `gui_replay.enabled`

Email output behavior:
- render step prepares HTML/TEXT summary files from reconciliation JSON
- SMTP step sends the summary and attaches `vm_reconciliation_<run_id>.csv`
