# Installation Guide — datalake-collectors

## Prerequisites

- PostgreSQL with `hmdl` schema access
- NetBox (Loki) API token with read on platforms/devices
- Gitea private repo `datalake-collectors-vault` populated
- SSH from AWX to Proxy NiFi nodes
- Python 3 + `requests`, `PyYAML` on AWX EE; optional `psycopg2` for HMDL logging

## Step 1 — Database

```bash
cd project-zabake/SQL/datalake-collectors
psql -h HOST -U USER -d DB -f collector_definition.sql
psql -h HOST -U USER -d DB -f collector_target.sql
psql -h HOST -U USER -d DB -f collector_sync_log.sql
psql -h HOST -U USER -d DB -f collector_diff_log.sql
psql -h HOST -U USER -d DB -f collector_check_log.sql
```

## Step 2 — Mappings and proxy assignment

Sync from AWX inventory (recommended):

```bash
cd datalake-collectors
python3 scripts/sync_proxy_assignment_from_awx.py --dry-run
python3 scripts/sync_proxy_assignment_from_awx.py
```

Or edit [mappings/proxy_assignment.yml](../../mappings/proxy_assignment.yml) manually for `proxy_nifi_host` overrides.

Review [mappings/netbox_platform_collector_mapping.yml](../../mappings/netbox_platform_collector_mapping.yml) for your NetBox manufacturers.

## Step 3 — Vault repo

Follow [VAULT_REPO_GUIDE.md](VAULT_REPO_GUIDE.md). Never commit real passwords to GitHub.

## Step 4 — AWX Job Template

See [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md). First run: `dry_run: true`, `sync_platforms: true`.

## Step 5 — Enable device sync (Phase 2)

When platform sync is stable, set `sync_devices: true` and validate [netbox_device_collector_mapping.yml](../../mappings/netbox_device_collector_mapping.yml).

## Step 6 — Production rollout

1. `dry_run: true` on one DC (`proxy_filter: DC13`)
2. Review email report and `hmdl.collector_diff_log`
3. `dry_run: false` for same DC
4. Repeat per DC in `proxy_assignment.yml`
