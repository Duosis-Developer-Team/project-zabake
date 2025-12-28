# Netbox API Discovery Script

## Overview

The `netbox_discovery.py` script analyzes Netbox API structure to discover where data fields from the template mapping CSV can be retrieved. This script helps identify the correct Netbox API endpoints and field mappings needed to build the host list for Zabbix migration.

## Purpose

Based on the template mapping CSV conditions, we need to extract:
- **Device Role** (e.g., "HOST")
- **Manufacturer/Üretici** (e.g., "Lenovo", "HPE", "Dell", "Inspur")
- **Device Type** (e.g., "M6", "M5" suffix)
- **Hostname**
- **IP Address**
- **Site/Location** (for DC_ID mapping)
- **Tags** (for Zabbix macros)
- **Custom Fields** (for Notes)

## Usage

### Basic Usage

```bash
python3 netbox_discovery.py \
  --url https://netbox.example.com \
  --token YOUR_NETBOX_API_TOKEN
```

### With Custom Output File

```bash
python3 netbox_discovery.py \
  --url https://netbox.example.com \
  --token YOUR_NETBOX_API_TOKEN \
  --output custom_report.json
```

### With SSL Verification

```bash
python3 netbox_discovery.py \
  --url https://netbox.example.com \
  --token YOUR_NETBOX_API_TOKEN \
  --verify-ssl
```

## What the Script Does

1. **Tests API Connection**: Verifies connectivity to Netbox API
2. **Discovers Endpoints**: Checks availability of key API endpoints
3. **Analyzes Device Structure**: Examines device object structure and fields
4. **Discovers Device Roles**: Lists all available device roles
5. **Discovers Manufacturers**: Lists all manufacturers in Netbox
6. **Discovers Device Types**: Lists device types with manufacturer information
7. **Discovers Sites**: Lists sites for DC_ID mapping
8. **Discovers Custom Fields**: Lists custom fields available on devices
9. **Discovers Tags**: Lists all tags in Netbox
10. **Analyzes IP Addresses**: Examines how IP addresses are stored and linked
11. **Generates Mapping Report**: Creates comprehensive mapping between CSV fields and Netbox API fields

## Output

The script generates a JSON report containing:

- **endpoints**: Available API endpoints and their status
- **device_structure**: Sample device object with all fields
- **device_roles**: List of device roles
- **manufacturers**: List of manufacturers
- **device_types**: List of device types
- **sites**: List of sites
- **custom_fields**: Custom fields for devices
- **tags**: Available tags
- **ip_analysis**: IP address structure analysis
- **csv_to_netbox_mapping**: Mapping guide from CSV fields to Netbox API fields

## CSV to Netbox Field Mapping

Based on the discovery, the mapping will be:

| CSV Field | Netbox Source | Notes |
|-----------|---------------|-------|
| DEVICE_TYPE | `device_type.manufacturer.name` + `device_type.model` | Match against conditions |
| HOSTNAME | `device.name` | Direct mapping |
| HOST_IP | `device.primary_ip4` | Extract IP from CIDR if needed |
| DC_ID | `device.site.name` or `device.site.slug` | Map to datacenter ID |
| TEMPLATE | Derived from manufacturer + model | Match against templates.csv |
| TYPE | From templates.yml | Based on DEVICE_TYPE |
| TAGS | `device.tags[]` | Convert to Zabbix macro format |
| NOTES | `device.custom_fields` or `device.comments` | Custom field or comments |

## Conditions Mapping

The template CSV conditions map to Netbox fields as follows:

- **Device Role: HOST** → `device.device_role.name == "HOST"`
- **Üretici: Lenovo** → `device.device_type.manufacturer.name == "Lenovo"`
- **Type: M6 (suffix)** → Extract suffix from `device.device_type.model` (e.g., "M6", "M5")

## Requirements

- Python 3.6+
- `requests` library
- Netbox API access with valid token

## Example Output

```
=== Discovering API Endpoints ===
✓ dcim/devices: 150 items
✓ dcim/device-roles: 5 items
✓ dcim/manufacturers: 10 items
...

=== Analyzing Device Structure ===
✓ Device sample found: server-01
  - Device Role: HOST
  - Manufacturer: Lenovo
  - Device Type: ThinkSystem SR650
  - Site: datacenter-01
  - Primary IP: 10.0.0.1/24
  - Tags: 3 tags
  - Custom Fields: 2 fields

=== DISCOVERY SUMMARY ===
Device Roles: 5
Manufacturers: 10
Device Types: 45
Sites: 8
Custom Fields: 2
Tags: 15

✓ Discovery completed successfully!
  Full report saved to: netbox_discovery_report.json
```

## Next Steps

After running the discovery script:

1. Review the generated JSON report
2. Verify the field mappings match your Netbox instance
3. Use the mapping information to build the Netbox-to-CSV conversion script
4. Test the conversion with a small subset of devices
5. Integrate with the existing Zabbix migration workflow

