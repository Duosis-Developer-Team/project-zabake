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
