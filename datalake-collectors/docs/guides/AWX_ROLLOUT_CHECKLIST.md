# AWX Rollout Checklist — Datalake Collectors (Multi-DC)

## Pre-flight (once)

- [x] SQL DDL applied (`SQL/datalake-collectors/*.sql` + `migrations/002_collector_check_phase.sql`)
- [x] DC13 pilot validated (platform sync, Gitea vault, AWX job)
- [x] Gitea `Admin/datalake-collectors-vault` populated from DC13 `configuration_file.json`
- [x] `proxy_assignment.yml` synced from AWX inventory **NiFi_Prod_Envanter** (23 NiFi hosts, 12 sites — run `scripts/sync_proxy_assignment_from_awx.py` after inventory changes)
- [x] AWX Job Template **`hmdl-datalake-collector-sync`** (id 55) uses inventory **NiFi_Prod_Envanter** + credential **NiFi_Prod_Root** (id 7)
- [x] `localhost` host in NiFi inventory uses `ansible_connection: local` (AWX EE)
- [x] Reconcile/deploy delegate tasks set `ansible_connection: ssh` + `ansible_host` (localhost play + slurp fix)
- [ ] Job extra var `gitea_vault_url`: `http://10.134.16.135:3000/Admin/datalake-collectors-vault.git`

Verify readiness:

```bash
python3 scripts/verify_proxy_rollout.py
python3 scripts/sync_proxy_assignment_from_awx.py --dry-run   # after AWX inventory edits
```

## Per-DC rollout loop

1. AWX run: `dry_run: true`, `sync_platforms: true`, `proxy_filter: <DC>`, `removal_guard_enabled: true`
2. Review email + `hmdl.collector_diff_log`, `hmdl.collector_sync_log`
3. AWX run: `dry_run: false`, same filters
4. On dual-NiFi DCs: compare `md5sum /Datalake_Project/configuration_file.json` on both nodes
5. Confirm NiFi collectors ingest with updated config

## DC status (AWX NiFi_Prod_Envanter)

| DC | Proxy IDs | NiFi hosts | Nodes | Rollout |
|----|-----------|------------|-------|---------|
| DC11 | DC11-NIFI1/2 | 10.6.116.250, .251 | 2 | Pending |
| DC12 | DC12-NIFI1/2 | 10.35.16.250, .251 | 2 | Pending |
| DC13 | DC13-NIFI1 | 10.134.16.10 | 1 | **Validated** |
| DC14 | DC14-NIFI1/2 | 10.50.16.250, .251 | 2 | Pending |
| DC15 | DC15-NIFI1/2 | 10.40.16.250, .251 | 2 | Pending |
| DC16 | DC16-NIFI1/2 | 10.60.16.250, .251 | 2 | dry_run OK (job 109841) |
| DC17 | DC17-NIFI1/2 | 10.90.16.250, .251 | 2 | Pending |
| AZ11 | AZ11-NIFI1/2 | 10.81.18.250, .251 | 2 | Pending |
| ICT11 | ICT11-NIFI1/2 | 10.70.16.250, .251 | 2 | Pending |
| DC18 | DC18-NIFI1/2 | 10.134.16.207, .208 | 2 | Pending |
| ICT21 | ICT21-NIFI1/2 | 10.125.16.2, .3 | 2 | Pending |
| UZ11 | UZ11-NIFI1/2 | 10.85.16.13, .14 | 2 | Pending |

Recommended order after DC13: **DC16 → DC15 → DC14 → DC12 → DC11 → DC17 → DC18 → AZ11 → ICT11 → ICT21 → UZ11**

Refresh vault from latest DC13 config (also syncs proxy assignment):

```bash
python3 ../../../scripts/setup_gitea_vault_and_proxy.py
```

Or proxy assignment only:

```bash
cd datalake-collectors && python3 scripts/sync_proxy_assignment_from_awx.py
```

See [DC_ROLLOUT_GUIDE.md](DC_ROLLOUT_GUIDE.md).
