# HMDL datalake-collectors audit tables (`hmdl` schema)

DDL for NetBox-driven collector configuration distribution to Proxy NiFi nodes.

## Tables

| Table | Purpose |
|-------|---------|
| `collector_definition` | Collector type catalog (conf_key, ip_field, vault_key) |
| `collector_target` | Per IP × collector × proxy inventory |
| `collector_sync_log` | Per-run reconcile summary |
| `collector_diff_log` | Per-IP added/removed audit |
| `collector_check_log` | ICMP/TCP check results |

## Apply

```bash
psql -h HOST -U USER -d DB -f collector_definition.sql
psql -h HOST -U USER -d DB -f collector_target.sql
psql -h HOST -U USER -d DB -f collector_sync_log.sql
psql -h HOST -U USER -d DB -f collector_diff_log.sql
psql -h HOST -U USER -d DB -f collector_check_log.sql
```

Playbooks also run `CREATE TABLE IF NOT EXISTS` when `hmdl_log_enabled: true`.

## Related docs

- [datalake-collectors/docs/guides/INSTALLATION_GUIDE.md](../../datalake-collectors/docs/guides/INSTALLATION_GUIDE.md)
- [datalake-collectors/README.md](../../datalake-collectors/README.md)
