## Zabbix Migration on Ansible AWX - End-to-End Guide

This guide explains how to run the CSV-driven Zabbix migration pipeline on Ansible AWX, including required credentials, inventories, job templates, variables, and environment-specific parameters.

### 1) Prerequisites
- AWX can reach your Zabbix API endpoint (HTTP/HTTPS) and target `ansible_worker` hosts.
- The SCM Project is synced (this repository) and the `community.general` collection is available on the AWX execution environment.
- Zabbix API user with permission to create/update hosts, link templates, and manage macros.

### 2) Files and Structure
- Playbook entry: `zabbix-migration/playbooks/zabbix_migration.yaml`
- Role: `zabbix-migration/roles/zabbix_migration`
- Mappings:
  - `zabbix-migration/mappings/templates.yml` (DEVICE_TYPE → templates + type)
  - `zabbix-migration/mappings/template_types.yml` (type → interface spec)
  - `zabbix-migration/mappings/datacenters.yml` (DC_ID → proxy/proxy_group)
- Input CSV: provide path via variable `zbx_migration_csv` (example: `zabbix-migration/examples/hosts.csv`).

### 3) Inventory
- Define inventory with a group (or host) matching playbook target: `ansible_worker`.
- Ensure SSH connectivity if tasks run on remote hosts (usually not required for pure API calls, but kept for consistency).

### 4) Credentials (AWX)
- Create a Credential of type “Machine” if you need SSH to target hosts.
- Create a Credential of type “Custom” or use “Vault/Environment” to store:
  - `zabbix_user`
  - `zabbix_password`
  - Optionally `zabbix_auth` if you prefer pre-generated token instead of login.

### 5) Execution Environment
- Include `community.general` collection. If missing, add to EE image or run:
  - `ansible-galaxy collection install community.general`

### 6) AWX Project
- Add a Project pointing to this repository.
- Set the playbook to `zabbix-migration/playbooks/zabbix_migration.yaml`.

### 7) Job Template
- Inventory: select the inventory that contains `ansible_worker`.
- Project: select this repository’s project.
- Playbook: `zabbix-migration/playbooks/zabbix_migration.yaml`.
- Credentials: add the Zabbix API credential (and Machine credential if needed).
- Extra Variables (YAML):
```
zbx_migration_csv: "/var/lib/awx/projects/project-zabake/zabbix-migration/examples/hosts.csv"
zabbix_url: "https://your-zabbix.local/zabbix/api_jsonrpc.php"
zabbix_validate_certs: false
# If you prefer login:
zabbix_user: "awx-api-user"
zabbix_password: "{{ vault_zabbix_password }}"
# Or if you provide a token directly:
# zabbix_auth: "<existing_token>"
```

### 8) Run Pipeline
1. Confirm mappings are correct for your environment:
   - `mappings/templates.yml` (template names must exist in Zabbix)
   - `mappings/template_types.yml` (SNMP v2/v3 details match your policy)
   - `mappings/datacenters.yml` (DC_ID keys match your CSV and Zabbix proxy/proxy groups)
2. Provide the CSV path via `zbx_migration_csv`.
3. Launch the Job Template.

### 9) Outputs and Idempotency
- The role will:
  - Read CSV rows by header
  - Login to Zabbix (if `zabbix_auth` not provided) and obtain token
  - Resolve templates for each `DEVICE_TYPE` via `templates.yml`
  - Resolve interface spec via `template_types.yml` (SNMP v2/v3/agent/api)
  - Resolve proxy/proxy group from `datacenters.yml`
  - Create or update host, link templates, ensure interface and macros
- Safe to re-run; it will update existing hosts instead of creating duplicates.

### 10) Environment-specific Parameters (List)
- Zabbix API:
  - `zabbix_url` (scheme, host, path)
  - `zabbix_validate_certs` (true/false; set true in production with proper CA)
  - `zabbix_user`, `zabbix_password` or `zabbix_auth` (token)
- Input data:
  - `zbx_migration_csv` (absolute path within AWX project checkout or accessible path)
- Inventory and hosts:
  - Inventory group/host `ansible_worker` presence
- Mappings:
  - `templates.yml` template names must match your Zabbix templates
  - `template_types.yml` SNMP credentials and settings (v2 community; v3 security/auth/priv)
  - `datacenters.yml` DC_ID keys and proxy/proxy_group IDs

### 11) Troubleshooting
- 401/permission errors: check `zabbix_user` role/permissions or token validity.
- Template resolution empty: template names in `templates.yml` must match exactly those in Zabbix.
- DC mapping missing: ensure `DC_ID` in CSV matches a key in `datacenters.yml`.
- SSL errors: set `zabbix_validate_certs: false` for testing; prefer valid certificates in production.

### 12) Security Recommendations
- Store all secrets in AWX Credentials or Ansible Vault.
- Restrict AWX RBAC for Job Templates that touch Zabbix.
- Enable logging/auditing on Zabbix for change tracking.


