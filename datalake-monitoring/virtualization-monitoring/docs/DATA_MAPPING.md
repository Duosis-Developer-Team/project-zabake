# Data Mapping

## VMware
- Datalake: `vm_metrics` (`uuid`, `vmname`, `cluster`)
- NetBox: `discovery_netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `vmname` prefix (for example `custA-vm-01` -> `custa`) when explicit customer field is absent.
- Environment mapping: `cluster ILIKE '%KM%'` -> `classic_vmware`, otherwise `hyperconv_vmware`.

## Nutanix
- Datalake: `nutanix_vm_metrics` (`vm_uuid`, `vm_name`, `cluster_uuid`, `collection_time`)
- Cluster resolution: `nutanix_vm_metrics.cluster_uuid` is resolved to `nutanix_cluster_metrics.cluster_name`.
- NetBox: `discovery_netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `vm_name` prefix if no explicit customer field exists.
- Environment mapping: all Nutanix rows are `hyperconv_nutanix`.

## IBM
- Datalake: `ibm_lpar_general` (`lparname`, `servername`)
- NetBox: `discovery_netbox_virtualization_vm` (`name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `lparname` prefix when needed.
- Environment mapping: all IBM rows are `power_ibm` (cluster comparison not mandatory for classification).

## Cluster coverage (Phase 2 — VMware + Nutanix)

Per-cluster coverage: is each inventory cluster actually collected into the datalake?

- VMware collected: `cluster_metrics` (`cluster` AS cluster_name, `datacenter`, `"timestamp"`/`collection_time`)
- VMware expected: `discovery_vmware_inventory_cluster` (`name` AS cluster_name, `status`, `last_observed`)
- Nutanix collected: `nutanix_cluster_metrics` (`cluster_name`, `cluster_uuid`, `datacenter_name`, `collection_time`)
- Nutanix expected: `discovery_nutanix_inventory_cluster` (`name`, `component_uuid`, `last_observed`)
- Match key: cluster name (`normalize_name`). Result table: `hmdl.hmdl_datalake_coverage_cluster`
  (`source` = vmware|nutanix). Status: `in_both` | `only_expected` | `only_datalake`.

## Host coverage (Phase 4 — IBM Power)

- Collected: `ibm_server_general` (`server_details_servername` AS servername, `server_details_mtm`,
  freshness via `"time"` — no collection_time column).
- Expected: `discovery_ibm_inventory` (`servername`, `mtm`, `collection_time`) WHERE `asset_type = 'server'`.
- Match key: `server_details_servername` ↔ `servername`. Result table:
  `hmdl.hmdl_datalake_coverage_ibm_host`. Status: `in_both` | `only_expected` | `only_datalake`.

## CSV output columns
- `run_id`
- `generated_at`
- `source`
- `environment`
- `vm_uuid`
- `vm_name`
- `datalake_cluster`
- `loki_cluster`
- `cluster_match` (`Y`, `N`, `N/A`)
- `customer`
- `status`
