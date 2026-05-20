# Vault Repo Guide — datalake-collectors-vault

## Rules

- Repository exists **only on Gitea** (private).
- Contains **passwords, API tokens, manual-only section bodies**.
- `per_device/<vault_key>/<ip>.yml` for host-specific credential overrides.
- `manual_extras/` for data NetBox cannot provide (e.g. NetBackup hostnames list).

## defaults.yml per collector

| Directory | Maps to conf_key |
|-----------|------------------|
| vmware | VmWare |
| nutanix | Nutanix |
| ibm_hmc | IBM-HMC |
| zabbix_connection | Zabbix (manual-only) |
| loki_connection | Loki (manual-only) |

Use keys matching production `configuration_file.json` field names (see CONFIG_FORMAT.md).

## Manual-only sections

Playbook merges vault `defaults.yml` into these sections without changing structure from production:

- **Zabbix** — API URL, group IDs, template lists
- **Loki** — address, endpoints, api_token
- **ServiceCore** — api_url, api_key
- **Dynamics365** — tenant/client/secret
- **Netbackup_old** — bearer_token, legacy URLs

## Template

Copy from [datalake-collectors-vault-template](../../../datalake-collectors-vault-template/).
