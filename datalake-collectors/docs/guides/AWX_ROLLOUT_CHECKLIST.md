# AWX Rollout Checklist — Datalake Collectors (Multi-DC)

## Pre-flight (once)

- [x] SQL DDL applied (`SQL/datalake-collectors/*.sql` + `migrations/002_collector_check_phase.sql`)
- [x] DC13 pilot validated (platform sync, Gitea vault, AWX job)
- [ ] Gitea `datalake-collectors-vault` populated from [vault-template](../../datalake-collectors-vault-template/README.md)
- [ ] AWX credentials: PostgreSQL, NetBox, Gitea token, SSH (per NiFi host)
- [ ] AWX inventory lists every `*-nifi-*` host referenced in [proxy_assignment.yml](../../mappings/proxy_assignment.yml)
- [ ] Job Template extra vars documented in [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md)

Verify proxy hostnames before each rollout wave:

```bash
python3 scripts/verify_proxy_rollout.py
python3 scripts/verify_proxy_rollout.py --dc-filter DC16
```

## Per-DC rollout loop

Replace `<DC>` with `DC16`, `MAIN`, or the next site code.

1. Set real AWX inventory hostnames in `proxy_assignment.yml` (both NiFi nodes when applicable).
2. AWX run: `dry_run: true`, `sync_platforms: true`, `proxy_filter: <DC>`, `removal_guard_enabled: true`
3. Review email + `hmdl.collector_diff_log`, `hmdl.collector_sync_log`, `hmdl.collector_check_log`
4. Confirm **blocked removals** are expected (IPs still reachable but absent from NetBox)
5. AWX run: `dry_run: false`, same filters
6. Optional: `deploy_scripts: true` to rsync platform collector scripts from `datalake/collectors/`
7. Verify both NiFi nodes have identical `configuration_file.json` hash
8. Confirm NiFi collectors ingest with updated IPs

## DC status

| DC | Proxy IDs | NiFi nodes | Pilot / prod | Notes |
|----|-----------|------------|--------------|-------|
| DC13 | DC13-NIFI1 | 1 | **Prod validated** | AWX host `dc13-nifi-1`, ssh `root` |
| DC16 | DC16-NIFI1, DC16-NIFI2 | 2 | Pending | Replace `REPLACE_DC16_NIFI*` in proxy_assignment |
| MAIN | MAIN-NIFI1, MAIN-NIFI2 | 2 | Pending | Replace `REPLACE_MAIN_NIFI*` in proxy_assignment |

## Expand

- Repeat per DC row above
- Enable `sync_devices: true` after platform mapping validated on all target DCs

See [DC_ROLLOUT_GUIDE.md](DC_ROLLOUT_GUIDE.md) for operational detail.
