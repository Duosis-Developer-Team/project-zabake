# Template Macros Guide

## Overview

This guide explains how to configure host macros for Zabbix templates in the Netbox-Zabbix integration. This feature is particularly useful for API-based templates that require authentication credentials and connection parameters.

## Features

- **Automatic IP Injection**: Use `{HOST.IP}` variable in macro values to automatically inject the device's IP address
- **Multiple Templates Support**: Each device type can have multiple templates with different interface types (SNMP, API, etc.)
- **Macro Merging**: During updates, new macros are merged with existing ones without losing manual configurations
- **Change Detection**: System only updates hosts when macro values actually change

## Configuration

### Template Macro Format

In the `zabbix-netbox/mappings/templates.yml` file, you can define macros for each template:

```yaml
Device Type:
  - name: Template Name
    type: interface_type
    macros:
      "{$MACRO_NAME}": "macro_value"
      "{$API_URL}": "https://{HOST.IP}/"
```

### Supported Variables

- `{HOST.IP}`: Replaced with the device's primary IP address from Netbox

### Examples

#### HPE IPMI with Redfish API

```yaml
HPE IPMI:
  - name: BLT - HPE ProLiant DL380 by SNMP
    type: snmpv2
  - name: HPE iLO by HTTP
    type: api
    macros:
      "{$REDFISH.API.URL}": "https://{HOST.IP}/"
      "{$REDFISH.PASSWORD}": "change_me"
      "{$REDFISH.USER}": "zabbix"
```

#### Dell iDRAC with Redfish API

```yaml
Dell IPMI:
  - name: BLT - Dell iDRAC SNMP
    type: snmpv2
  - name: Dell iDRAC by Redfish
    type: api
    macros:
      "{$IDRAC.API.URL}": "https://{HOST.IP}/"
      "{$IDRAC.PASSWORD}": "change_me"
      "{$IDRAC.USER}": "root"
```

#### FortiGate Firewall with HTTP API

```yaml
Fortigate Firewall:
  - name: FortiGate by HTTP
    type: api
    macros:
      "{$FORTIGATE.API.URL}": "https://{HOST.IP}/"
      "{$FORTIGATE.API.KEY}": "change_me"
```

## Usage Flow

### 1. Host Creation

When a new host is created in Zabbix:
1. System reads template definitions from `templates.yml`
2. Collects all macros from all templates assigned to the device
3. Replaces `{HOST.IP}` with actual device IP address
4. Creates host with macros attached

### 2. Host Update

When an existing host is updated:
1. System fetches existing macros from Zabbix
2. Collects new macros from template definitions
3. Merges new macros with existing ones (new values take precedence)
4. Replaces `{HOST.IP}` with actual device IP address
5. Updates host only if macro values have changed

### 3. Change Detection

The system intelligently detects changes:
- Compares new macro values with existing ones
- Only updates if values differ
- Reports changed macros in update summary
- Preserves manually configured macros not defined in templates

## Security Considerations

⚠️ **Important**: The `change_me` values in macro examples are placeholders. You should:

1. **Never commit real passwords** to the templates.yml file
2. **Use secure credential management** for production environments
3. **Consider these options**:
   - Store credentials in AWX/Tower as encrypted variables
   - Use Ansible Vault for sensitive data
   - Update macro passwords directly in Zabbix UI after host creation
   - Use environment-specific configuration files

## Best Practices

### 1. Organizing Templates

For devices that support multiple monitoring methods:

```yaml
Device Type:
  - name: Device by SNMP
    type: snmpv2
  - name: Device by API
    type: api
    macros:
      "{$API.URL}": "https://{HOST.IP}/"
      "{$API.TOKEN}": "placeholder"
```

### 2. Naming Conventions

Follow consistent naming patterns:
- Use uppercase for macro names: `{$REDFISH.API.URL}`
- Use descriptive names that indicate the purpose
- Include vendor/protocol prefix: `{$REDFISH.*}`, `{$IDRAC.*}`, `{$FORTIGATE.*}`

### 3. Default Values

Provide sensible defaults:
- Use `change_me` for password fields to make them obvious
- Use `{HOST.IP}` for URL fields to automate IP injection
- Set common usernames (e.g., `zabbix`, `root`, `admin`)

### 4. Documentation

Document each macro in your internal wiki:
- What it does
- Required format
- Where to get the actual value
- Security implications

## Troubleshooting

### Macros Not Applied

If macros are not being applied to hosts:

1. **Check Template Configuration**: Verify macros are correctly defined in `templates.yml`
2. **Verify Syntax**: Ensure YAML formatting is correct (proper indentation, quotes)
3. **Check Logs**: Review Ansible playbook output for errors
4. **Test Variable Replacement**: Verify `{HOST.IP}` is being replaced correctly

### Update Not Triggered

If host update doesn't trigger for macro changes:

1. **Verify Values Changed**: System only updates if macro values actually differ
2. **Check Existing Macros**: Use Zabbix UI to see current macro values
3. **Force Update**: Temporarily change macro value to trigger update

### Wrong IP Address

If `{HOST.IP}` resolves to wrong address:

1. **Check Netbox**: Verify primary IP is set correctly in Netbox
2. **Verify Device Processing**: Check device processing Python script output
3. **Test Manually**: Use Netbox API to verify primary_ip4 field

## Advanced Usage

### Multiple Variables

You can combine multiple variables:

```yaml
macros:
  "{$API.URL}": "https://{HOST.IP}:8443/api"
  "{$API.ENDPOINT}": "{HOST.IP}:8080"
```

### Complex URLs

For complex URL structures:

```yaml
macros:
  "{$REDFISH.API.URL}": "https://{HOST.IP}/redfish/v1"
  "{$REDFISH.SYSTEMS}": "https://{HOST.IP}/redfish/v1/Systems"
```

### Port Specifications

Include ports in URLs:

```yaml
macros:
  "{$IDRAC.API.URL}": "https://{HOST.IP}:443/"
  "{$CUSTOM.API.PORT}": "8443"
```

## Implementation Details

### Files Modified

1. **templates.yml**: Template and macro definitions
2. **zabbix_host_operations.yml**: Macro processing and host operations logic

### Processing Flow

```
templates.yml → Load mappings → Extract macros → Replace variables → Format for API → Create/Update host
```

### Macro Processing Steps

1. Load template mappings from YAML
2. Extract macros from all templates for device type
3. Replace `{HOST.IP}` with actual IP address
4. Format macros for Zabbix API (convert dict to list format)
5. For updates: merge with existing macros
6. Send to Zabbix API

## Future Enhancements

Potential improvements for future versions:

- Support for additional variables: `{HOST.NAME}`, `{LOCATION}`, etc.
- Macro inheritance from device type mappings
- Template-specific macro overrides
- Encrypted macro support
- Macro validation before applying
- Bulk macro updates

## Support

For issues or questions:
1. Check this documentation
2. Review example configurations
3. Test with simple cases first
4. Check Ansible playbook output
5. Verify Zabbix API calls in logs
