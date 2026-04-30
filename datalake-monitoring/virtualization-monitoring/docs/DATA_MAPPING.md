# Data Mapping

## VMware
- Datalake: `vm_metrics` (`uuid`, `vmname`, `cluster`, `customerid`)
- NetBox: `netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)

## Nutanix
- Datalake: `nutanix_vm_metrics` (`vm_uuid`, `vm_name`, `cluster_name`, `customerid`)
- NetBox: `netbox_virtualization_vm` (`custom_fields_uuid`, `name`, `cluster_name`, `custom_fields_musteri`)

## IBM
- Datalake: `ibm_lpar_general` (`lparname`, `servername`, `customerid`)
- NetBox: `netbox_virtualization_vm` (`name`, `cluster_name`, `custom_fields_musteri`)
