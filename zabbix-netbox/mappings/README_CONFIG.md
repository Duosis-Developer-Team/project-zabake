# Host Groups and Tags YAML Configuration Guide

## Overview

This guide explains how to configure host groups and tags for Zabbix hosts using YAML configuration files. The configuration-driven approach allows you to modify which Netbox attributes are extracted and how they are mapped to Zabbix without changing any code.

## Configuration Files

### 1. `host_groups_config.yml`

Controls which host groups are added to Zabbix hosts.

**Location:** `zabbix-netbox/mappings/host_groups_config.yml`

#### Structure

```yaml
host_groups:
  sources:
    - name: "unique_identifier"
      type: "source_type"
      enabled: true/false
      priority: number
      # Additional fields depending on type
  
  settings:
    separator: ","
    skip_empty: true
    unique: true
    trim: true
```

#### Source Types

**1. `mapping_result`**
- Uses the device type determined from `netbox_device_type_mapping.yml`
- Example: "Lenovo IPMI", "Dell IPMI"

```yaml
- name: "device_type_mapping"
  type: "mapping_result"
  enabled: true
  priority: 1
```

**2. `netbox_attribute`**
- Extracts value from Netbox device attribute using dot notation
- Supports fallback paths

```yaml
- name: "site"
  type: "netbox_attribute"
  enabled: true
  priority: 2
  path: "site.name"
  fallback: "location.name"  # Optional
```

**3. `custom_field`**
- Extracts value from Netbox custom field

```yaml
- name: "ownership"
  type: "custom_field"
  enabled: true
  priority: 3
  field_name: "Sahiplik"
```

**4. `computed`**
- Uses a computed function for complex logic
- Available functions: `get_location_name`

```yaml
- name: "location"
  type: "computed"
  enabled: true
  priority: 2
  compute_function: "get_location_name"
```

**5. `template_mapping`**
- Extracts host groups from template mappings in `templates.yml`

```yaml
- name: "template_groups"
  type: "template_mapping"
  enabled: true
  priority: 4
  source_file: "templates.yml"
  attribute: "host_groups"
```

### 2. `tags_config.yml`

Controls which tags are added to Zabbix hosts.

**Location:** `zabbix-netbox/mappings/tags_config.yml`

#### Structure

```yaml
tags:
  definitions:
    - tag_name: "Tag_Name"
      source_type: "source_type"
      enabled: true/false
      # Additional fields depending on source_type
  
  settings:
    skip_empty: true
    skip_none: true
    trim: true
    treat_empty_as_none: true
```

#### Source Types

**1. `netbox_attribute`**
- Extracts from Netbox device attribute
- Supports fallback and transformation

```yaml
- tag_name: "Manufacturer"
  source_type: "netbox_attribute"
  path: "device_type.manufacturer.name"
  enabled: true
  fallback: "device_type.display"  # Optional
  transform: "to_string"  # Optional: to_string
```

**2. `custom_field`**
- Extracts from Netbox custom field

```yaml
- tag_name: "Contact"
  source_type: "custom_field"
  field_name: "Sahiplik"
  enabled: true
```

**3. `computed`**
- Uses computed function
- Available functions: `extract_hall`, `get_location_name`

```yaml
# Example 1: Hall extraction
- tag_name: "Hall"
  source_type: "computed"
  compute_function: "extract_hall"
  priority_paths:
    - "location.description"
    - "location.name"
  enabled: true

# Example 2: Location hierarchy
- tag_name: "Location"
  source_type: "computed"
  compute_function: "get_location_name"
  enabled: true
  description: "Location from hierarchy: parent.name -> location.name -> site.name"
```

**4. `array_expansion`**
- Expands array into multiple tags with prefix
- Used for Netbox tags

```yaml
- tag_name: "Loki_Tag_"
  source_type: "array_expansion"
  path: "tags"
  prefix: "Loki_Tag_"
  enabled: true
```

## Common Use Cases

### Example 1: Add a New Tag

**Goal:** Add device serial number as a tag

**Steps:**
1. Edit `tags_config.yml`
2. Add new definition:

```yaml
- tag_name: "Serial_Number"
  source_type: "netbox_attribute"
  path: "serial"
  enabled: true
```

3. No code changes needed! ✅

### Example 2: Disable a Host Group Source

**Goal:** Stop adding ownership as a host group

**Steps:**
1. Edit `host_groups_config.yml`
2. Find the ownership source
3. Change `enabled: true` to `enabled: false`

```yaml
- name: "ownership"
  type: "custom_field"
  enabled: false  # Changed from true
  priority: 3
  field_name: "Sahiplik"
```

### Example 3: Add Custom Field as Tag

**Goal:** Add "Environment" custom field as a tag

**Steps:**
1. Edit `tags_config.yml`
2. Add new definition:

```yaml
- tag_name: "Environment"
  source_type: "custom_field"
  field_name: "Environment"
  enabled: true
  description: "Environment from Netbox custom field"
```

### Example 4: Change Priority Order

**Goal:** Make location appear before device type in host groups

**Steps:**
1. Edit `host_groups_config.yml`
2. Change priority numbers (lower = higher priority):

```yaml
- name: "location"
  priority: 1  # Changed from 2

- name: "device_type_mapping"
  priority: 2  # Changed from 1
```

## Path Syntax

Use dot notation to access nested attributes:

```yaml
# Simple path
path: "name"

# Nested path
path: "device_type.manufacturer.name"

# Deep nesting
path: "location.parent.name"
```

## Fallback Mechanism

If the primary path doesn't exist or is empty, fallback paths are tried:

```yaml
path: "device_type.model"
fallback: "device_type.display"
# Or multiple fallbacks:
fallback:
  - "device_type.model"
  - "device_type.display"
  - "name"
```

## Settings

### Host Groups Settings

- **separator**: Character to join host groups (default: `,`)
- **skip_empty**: Skip empty values (default: `true`)
- **unique**: Remove duplicates (default: `true`)
- **trim**: Trim whitespace (default: `true`)

### Tags Settings

- **skip_empty**: Skip empty string values (default: `true`)
- **skip_none**: Skip None values (default: `true`)
- **trim**: Trim whitespace (default: `true`)
- **treat_empty_as_none**: Treat empty strings as None (default: `true`)

## Testing

### Unit Tests

Run unit tests to verify configuration parsing:

```bash
cd zabbix-netbox/tests
python test_yaml_config.py
```

### Integration Tests

Run integration tests to compare config-driven vs hardcoded results:

```bash
cd zabbix-netbox/tests
python test_integration.py
```

## Troubleshooting

### Config not being used

**Problem:** YAML config exists but changes don't take effect

**Solutions:**
1. Verify file path in `defaults/main.yml`:
   ```yaml
   host_groups_config_path: "{{ playbook_dir }}/../mappings/host_groups_config.yml"
   tags_config_path: "{{ playbook_dir }}/../mappings/tags_config.yml"
   ```

2. Check YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('host_groups_config.yml'))"
   ```

3. Check playbook logs for config loading errors

### Missing tags or host groups

**Problem:** Expected tag or host group not appearing

**Solutions:**
1. Check if source is enabled: `enabled: true`
2. Verify the path exists in Netbox device data
3. Test path extraction:
   ```python
   from test_yaml_config import extract_by_path
   device = {...}  # Your device data
   result = extract_by_path(device, "your.path.here")
   print(result)
   ```

### Duplicate groups

**Problem:** Same host group appears multiple times

**Solution:** Ensure `unique: true` in settings:
```yaml
settings:
  unique: true
```

## Backward Compatibility

If config files don't exist, the system falls back to hardcoded logic automatically. This ensures:
- Existing deployments continue to work
- Gradual migration is possible
- No breaking changes

## Advanced Examples

### Conditional Tag Based on Value

While not directly supported, you can disable a tag source and let the computed function handle the condition logic.

### Dynamic Prefix

Array expansion supports dynamic prefixes:

```yaml
- tag_name: "Custom_Tag_"
  source_type: "array_expansion"
  path: "custom_fields.tags_array"
  prefix: "Custom_Tag_"
  enabled: true
```

### Nested Custom Field

Access nested custom field data:

```yaml
- tag_name: "SubField"
  source_type: "netbox_attribute"
  path: "custom_fields.parent_field.sub_field"
  enabled: true
```

## Reference

### Complete Netbox Attribute Paths

Common paths you can use:

- `id` - Device ID
- `name` - Device name
- `serial` - Serial number
- `device_type.manufacturer.name` - Manufacturer
- `device_type.model` - Model
- `device_type.display` - Display name
- `site.name` - Site name
- `location.name` - Location name
- `location.description` - Location description
- `location.parent.name` - Parent location name
- `rack.name` - Rack name
- `rack.role.name` - Rack role
- `cluster.name` - Cluster name
- `tenant.name` - Tenant name
- `role.name` - Device role
- `primary_ip4.address` - Primary IPv4 address
- `tags` - Array of tags
- `custom_fields.FIELD_NAME` - Custom field value

## Support

For issues or questions:
1. Check logs in `/tmp/netbox_device_processor.py`
2. Run unit tests to verify configuration
3. Refer to the main project documentation
