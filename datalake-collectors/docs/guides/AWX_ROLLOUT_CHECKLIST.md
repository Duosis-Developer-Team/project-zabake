# AWX Rollout Checklist (Pilot DC13)

## Pre-flight

- [ ] SQL DDL applied (`SQL/datalake-collectors/*.sql`)
- [ ] `proxy_assignment.yml` — no `REPLACE_*` hosts for pilot DC
- [ ] Gitea `datalake-collectors-vault` populated from vault-template
- [ ] AWX credentials: DB, NetBox, Gitea token, SSH
- [ ] Job Template Extra Variables documented in [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md)

## Pilot run

1. `dry_run: true`, `sync_platforms: true`, `proxy_filter: DC13`
2. Review `hmdl.collector_diff_log` and email
3. `dry_run: false` for DC13
4. Verify NiFi collectors read updated `configuration_file.json`

## Expand

- Repeat per DC; enable `sync_devices: true` after platform mapping validated
