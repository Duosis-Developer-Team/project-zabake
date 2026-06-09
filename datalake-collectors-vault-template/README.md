# datalake-collectors-vault (Gitea-only template)

Copy this directory structure into a **private** Gitea repository named `datalake-collectors-vault`.
Do **not** mirror this repo to GitHub.

## Layout

```
datalake-collectors-vault/
  vmware/defaults.yml
  nutanix/defaults.yml
  ibm_hmc/defaults.yml
  ibm_virtualize/defaults.yml
  veeam/defaults.yml
  zerto/defaults.yml
  netbackup/defaults.yml
  ilo_redfish/defaults.yml
  inspur_redfish/defaults.yml
  s3icos/defaults.yml
  ibm_san/defaults.yml
  zabbix_connection/defaults.yml
  loki_connection/defaults.yml
  servicecore/defaults.yml
  dynamics365/defaults.yml
  netbackup_old/defaults.yml
  manual_extras/netbackup/hostnames.yml
  per_device/ilo_redfish/<ip>.yml   # optional overrides
```

## defaults.yml format

Use placeholder values in templates; replace with real secrets only in Gitea.

```yaml
user: "zabbix@blt.vc"
password: "REPLACE_ME"
```

## Populate from production

Use the extraction script against a pilot `configuration_file.json`:

```bash
python3 scripts/extract_vault_from_config.py \
  --config /path/to/configuration_file.json \
  --collector-types mappings/collector_types.yml \
  --output-dir /tmp/datalake-collectors-vault
```

Then push the output tree to Gitea (private repo).

## Manual-only sections

Populate full section content for: `zabbix_connection`, `loki_connection`, `servicecore`, `dynamics365`, `netbackup_old`.

See [VAULT_REPO_GUIDE.md](../datalake-collectors/docs/guides/VAULT_REPO_GUIDE.md).
