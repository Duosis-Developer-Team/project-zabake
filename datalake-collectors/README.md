# datalake-collectors (HMDL)

NetBox-driven lifecycle for `configuration_file.json` on Main/Proxy NiFi nodes.

## Features

- **Platform-first sync** (Phase 1): NetBox `dcim/platforms` → collector targets → IP reconcile
- **Device sync** (Phase 2): enable `sync_devices: true`
- **Gitea vault repo** for secrets (never in GitHub-mirrored mappings)
- **HMDL Postgres** audit: `hmdl.collector_target`, diff log, check log
- **ICMP + TCP** connectivity report and email (zabbix-netbox SMTP standard)

## Quick start

```bash
ansible-playbook playbooks/datalake_collector_sync.yaml \
  -e discovery_db_host=HOST -e discovery_db_name=DB \
  -e discovery_db_user=USER -e discovery_db_password=PASS \
  -e netbox_url=https://loki.example.com/ -e netbox_token=TOKEN \
  -e gitea_vault_url=https://gitea.example/owner/datalake-collectors-vault.git \
  -e gitea_vault_token=TOKEN \
  -e dry_run=true -e sync_platforms=true
```

## Documentation

See [docs/guides/00-DOCUMENTATION_INDEX.md](docs/guides/00-DOCUMENTATION_INDEX.md).

## SQL

[../SQL/datalake-collectors/README.md](../SQL/datalake-collectors/README.md)

## Vault template

[../datalake-collectors-vault-template/README.md](../datalake-collectors-vault-template/README.md)
