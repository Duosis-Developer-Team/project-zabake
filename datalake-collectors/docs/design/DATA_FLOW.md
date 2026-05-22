# Data Flow

## Phase 1 — Platforms (default)

1. `fetch_platforms_loki.yml` → NetBox `/api/dcim/platforms/`
2. `apply_platform_collector_mapping.yml` → targets with `host_entity_type: platform`
3. `read_vault.yml` → Gitea vault credentials
4. `upsert_hmdl_target.yml` → `hmdl.collector_target`
5. `reconcile_proxy.yml` per proxy → update `VMwareIP`, `PRISM_IP`, etc.
6. `run_basic_checks.yml` → ICMP/TCP
7. `send_report.yml` → email

## Phase 2 — Devices

Enable `sync_devices: true`. Same flow with `fetch_devices_loki.yml` and device mapping YAML.
