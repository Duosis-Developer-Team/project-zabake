# Data Flow

## Phase 1 — Platforms (default)

1. `fetch_platforms_loki.yml` → NetBox `/api/dcim/platforms/`
2. `apply_platform_collector_mapping.yml` → targets with `host_entity_type: platform` (fan-out to all NiFi nodes per DC)
3. `read_vault.yml` → Gitea vault credentials
4. `upsert_hmdl_target.yml` → `hmdl.collector_target`
5. Pre-reconcile ICMP/TCP on removal candidates → `removal_blocked` when still reachable
6. `reconcile_proxy.yml` per proxy → update `VMwareIP`, `PRISM_IP`, etc.
7. Optional `deploy_collector_scripts.yml` → rsync platform scripts to NiFi
8. `run_basic_checks.yml` → post-reconcile ICMP/TCP
9. `send_report.yml` → email

## Phase 2 — Devices

Enable `sync_devices: true`. Same flow with `fetch_devices_loki.yml` and device mapping YAML.
