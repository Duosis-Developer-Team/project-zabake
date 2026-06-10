# AWX Guide — Datalake Collector Sync

English summary. Full Turkish reference: [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md).

## Job template (standard name)

| Field | Value |
|-------|--------|
| **Name** | `hmdl-datalake-collector-sync` |
| **Playbook** | `datalake-collectors/playbooks/datalake_collector_sync.yaml` |
| **Inventory** | `NiFi_Prod_Envanter` (SSH delegation + localhost) |
| **Credentials** | `NiFi_Prod_Root` + DB / NetBox / Gitea via Extra Vars |

Finalize naming on AWX: `python3 scripts/finalize_hmdl_collector_awx_template.py`

## AWX inventory vs proxy mapping

Adding hosts to AWX inventory **does not** update collector targets automatically. The playbook reads **`mappings/proxy_assignment.yml`** from SCM.

After inventory changes:

```bash
cd project-zabake/datalake-collectors
python3 scripts/sync_proxy_assignment_from_awx.py
python3 scripts/verify_proxy_rollout.py
# commit + AWX project sync, then run the job template
```

## Defaults

- `sync_platforms: true` (Phase 1)
- `sync_devices: false` (Phase 2)
- `dry_run: true` (safe first run)
- `proxy_filter: ""` → all active proxies from NetBox targets

## Before production

1. Sync `proxy_assignment.yml` from AWX (`sync_proxy_assignment_from_awx.py`)
2. Populate `datalake-collectors-vault` on Gitea (private)
3. Run SQL DDL under `SQL/datalake-collectors/`
4. Pilot with `dry_run: true`, then `dry_run: false` per DC
