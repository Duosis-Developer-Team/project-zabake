# AWX Guide — Datalake Collector Sync

English summary. Full Turkish reference: [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md).

## Job template

- **Playbook:** `datalake-collectors/playbooks/datalake_collector_sync.yaml`
- **Inventory:** localhost
- **Credentials:** PostgreSQL, NetBox API token, Gitea vault token, SSH to proxy NiFi hosts

## Defaults

- `sync_platforms: true` (Phase 1)
- `sync_devices: false` (Phase 2)
- `dry_run: true` (safe first run)

## Before production

1. Replace `REPLACE_*` hosts in `mappings/proxy_assignment.yml`
2. Populate `datalake-collectors-vault` on Gitea (private)
3. Run SQL DDL under `SQL/datalake-collectors/`
4. Pilot with `dry_run: true`, then `dry_run: false`
