# datalake-collectors-vault (Gitea-only template)

Copy this directory structure into a **private** Gitea repository named `datalake-collectors-vault`.
Do **not** mirror this repo to GitHub.

## Layout

```
datalake-collectors-vault/
  vmware/defaults.yml
  nutanix/defaults.yml
  ...
  manual_extras/netbackup/hostnames.yml
  per_device/ilo_redfish/<ip>.yml   # optional overrides
```

## defaults.yml format

Use placeholder values in templates; replace with real secrets only in Gitea.

```yaml
user: "zabbix@blt.vc"
password: "REPLACE_ME"
```

## Manual-only sections

Populate full section content for: `zabbix_connection`, `loki_connection`, `servicecore`, `dynamics365`, `netbackup_old`.

See [VAULT_REPO_GUIDE.md](../datalake-collectors/docs/guides/VAULT_REPO_GUIDE.md).
