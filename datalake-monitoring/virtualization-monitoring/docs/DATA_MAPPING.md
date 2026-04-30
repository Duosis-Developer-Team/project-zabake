# Data Mapping

## VMware
- Datalake: `vm_metrics` (`uuid`, `vmname`, `cluster`)
- NetBox: `discovery_netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `vmname` prefix (for example `custA-vm-01` -> `custa`) when explicit customer field is absent.

## Nutanix
- Datalake: `nutanix_vm_metrics` (`vm_uuid`, `vm_name`, `cluster_uuid`, `collection_time`)
- NetBox: `discovery_netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `vm_name` prefix if no explicit customer field exists.

## IBM
- Datalake: `ibm_lpar_general` (`lparname`, `servername`)
- NetBox: `discovery_netbox_virtualization_vm` (`name`, `cluster_name`, `custom_fields_musteri`)
- Customer matching: parsed from `lparname` prefix when needed.
