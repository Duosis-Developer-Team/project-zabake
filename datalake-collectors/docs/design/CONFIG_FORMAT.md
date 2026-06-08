# configuration_file.json format

Production format uses **comma-separated strings** for multi-IP fields (not JSON arrays). NiFi flows iterate one IP per execution.

## NetBox-managed sections

| conf_key | ip_field | ip_format |
|----------|----------|-----------|
| Veeam | ips | comma_string |
| VmWare | VMwareIP | comma_string |
| IBM-Virtualize | host | comma_string (+ link computed) |
| IBM-HMC | hmc_hostname | comma_string |
| Nutanix | PRISM_IP | comma_string |
| Netbackup | IpAddress | comma_string |
| Zerto | IpAddress | comma_string |
| ILO-Redfish | IpAddress | comma_string |
| Inspur-Redfish | IpAddress | comma_string |
| s3icos | IpAddress | single_string |
| IBM-SAN | IpAddress | single_string |

## Manual-only sections (vault repo)

Zabbix, Loki, ServiceCore, Dynamics365, Netbackup_old — reconciler does not change IP fields; full section merged from `datalake-collectors-vault`.

## Example

See [datalake/collectors/configuration_file.json.example](../../../../datalake/collectors/configuration_file.json.example).
