# Netbox to Zabbix Data Mapping Documentation

## Overview

This document describes the complete data flow from Netbox (Loki) to Zabbix, including API endpoints, data parsing, field transformations, and final Zabbix host creation/update.

**Data Flow:**
```
Netbox API → Python Parsing → Device Info → Zabbix API
```

---

## 1. Netbox API Data Sources

### 1.1 Primary Device Endpoint

**Endpoint:** `GET /api/dcim/devices/`

**Parameters:**
- `limit`: 1000 (pagination)
- `location_id`: Optional (filters by location)

**Response Structure:**
```json
{
  "count": 100,
  "next": "https://loki.example.com/api/dcim/devices/?offset=1000",
  "previous": null,
  "results": [
    {
      "id": 12365,
      "name": "c1h1ict11",
      "device_type": {
        "id": 123,
        "model": "ThinkAgile HX7531",
        "manufacturer": {
          "name": "LENOVO"
        }
      },
      "role": {
        "name": "HOST"
      },
      "site": {
        "name": "ALMANYA"
      },
      "location": {
        "id": 17,
        "name": "ICT11",
        "description": "DATA HALL 1"
      },
      "tenant": {
        "name": "Customer A"
      },
      "primary_ip4": {
        "id": 5678,
        "address": "10.70.1.22/24"
      },
      "cluster": {
        "name": "vCluster01"
      },
      "rack": {
        "name": "R101",
        "role": {
          "name": "Production"
        }
      },
      "custom_fields": {
        "Sorumlu_Ekip": "NOC Team",
        "Kurulum_Tarihi": "2024-01-15"
      },
      "tags": [
        {"name": "production", "slug": "production"},
        {"name": "critical", "slug": "critical"}
      ]
    }
  ]
}
```

### 1.2 Location Resolution Endpoint

**Endpoint:** `GET /api/dcim/locations/`

**Parameters:**
- `name`: Location name (for filtering)
- `parent_id`: Parent location ID (for child lookup)

**Purpose:** Resolve location hierarchy (parent locations)

### 1.3 IP Address Endpoint (Optional)

**Endpoint:** `GET /api/ipam/ip-addresses/{ip_id}/`

**Purpose:** Fetch IP address details if not expanded in device response

---

## 2. Data Parsing and Transformation

### 2.1 Hostname Extraction

**Source Field:** `device.name`

**Parsing Logic:**
```python
hostname = device.get('name', '')
```

**Zabbix Field:** `host` (hostname)

**Example:**
```
Netbox: device.name = "c1h1ict11"
↓
Zabbix: host = "c1h1ict11"
```

---

### 2.2 IP Address Extraction

**Source Field:** `device.primary_ip4.address`

**Parsing Logic:**
```python
def get_primary_ip(device):
    primary_ip4 = device.get('primary_ip4')
    if not primary_ip4:
        return None
    
    # If expanded dict
    if isinstance(primary_ip4, dict):
        address = primary_ip4.get('address', '')
        if address:
            return address.split('/')[0]  # Remove CIDR suffix
        
        # Fallback: fetch from IP API
        ip_id = primary_ip4.get('id')
        if ip_id:
            response = requests.get(f"{netbox_url}/api/ipam/ip-addresses/{ip_id}/")
            ip_data = response.json()
            address = ip_data.get('address', '')
            return address.split('/')[0]
    
    return None
```

**Zabbix Field:** `interfaces[].ip`

**Example:**
```
Netbox: device.primary_ip4.address = "10.70.1.22/24"
↓
Parse: Remove CIDR → "10.70.1.22"
↓
Zabbix: interfaces[0].ip = "10.70.1.22"
```

---

### 2.3 Location (DC_ID) Extraction

**Source Fields:**
1. `device.location.name` (primary)
2. `device.location.parent.name` (if parent exists)
3. `device.site.name` (fallback)

**Parsing Logic:**
```python
def get_location_name(device):
    location_obj = device.get('location')
    
    # Try to get location with parent hierarchy
    if location_obj:
        if isinstance(location_obj, dict):
            location_id = location_obj.get('id')
            if location_id:
                # Fetch full location data
                response = requests.get(f"{netbox_url}/api/dcim/locations/{location_id}/")
                loc_data = response.json()
                
                # Check if location has parent
                parent_id = loc_data.get('parent', {}).get('id')
                if parent_id:
                    # Fetch parent location
                    parent_response = requests.get(f"{netbox_url}/api/dcim/locations/{parent_id}/")
                    parent_data = parent_response.json()
                    return parent_data.get('name', '')  # Use parent name
                
                # No parent, use current location
                return loc_data.get('name', '')
            
            # Location dict with name
            return location_obj.get('name', '')
    
    # Fallback to site name
    site = device.get('site', {})
    return site.get('name', '')
```

**Zabbix Field:** `DC_ID` (used for proxy group matching)

**Example:**
```
Netbox: 
  - device.location.name = "ICT11"
  - device.location.parent = null
↓
DC_ID = "ICT11"
↓
Zabbix: proxy_groupid = 1 (matched "Dcict11-Proxy Group")
```

---

### 2.4 Device Type Determination

**Source Fields:**
- `device.role.name` (must be "HOST")
- `device.device_type.manufacturer.name`
- `device.device_type.model`
- `device.name`

**Parsing Logic:**
```python
def determine_device_type(device, device_type_mapping):
    mappings = device_type_mapping.get('mappings', [])
    sorted_mappings = sorted(mappings, key=lambda x: x.get('priority', 999))
    
    for mapping in sorted_mappings:
        conditions = mapping.get('conditions', {})
        
        # Check all conditions
        all_match = True
        for condition_key, condition_value in conditions.items():
            if condition_key == 'device_role':
                role = device.get('role', {}).get('name', '')
                if role.upper() != condition_value.upper():
                    all_match = False
                    break
            
            elif condition_key == 'manufacturer':
                manufacturer = device.get('device_type', {}).get('manufacturer', {}).get('name', '')
                if manufacturer.upper() != condition_value.upper():
                    all_match = False
                    break
            
            # ... other conditions (model_contains, model_suffix, name_contains)
        
        if all_match:
            return mapping.get('device_type')
    
    return None
```

**Mapping File:** `zabbix-migration/mappings/netbox_device_type_mapping.yml`

**Example Mapping:**
```yaml
mappings:
  - device_type: "Lenovo IPMI"
    priority: 1
    conditions:
      device_role: "HOST"
      manufacturer: "LENOVO"
    templates:
      - "BLT - Lenovo ICT XCC Monitoring"
```

**Zabbix Field:** Determines which templates to assign

**Example:**
```
Netbox:
  - device.role.name = "HOST"
  - device.device_type.manufacturer.name = "LENOVO"
  - device.device_type.model = "ThinkAgile HX7531"
↓
Match: "Lenovo IPMI" mapping
↓
Zabbix: templates = [{"templateid": "10682"}]  # "BLT - Lenovo ICT XCC Monitoring"
```

---

## 3. Host Groups Extraction

**Source Fields:**
1. Device Type (from mapping)
2. Location (parent or current)
3. Tenant/Contact

**Parsing Logic:**
```python
def extract_host_groups(device, device_type):
    groups = []
    
    # 1. Device type (from mapping)
    if device_type:
        groups.append(device_type)  # e.g., "Lenovo IPMI"
    
    # 2. Location (parent if exists, otherwise location or site)
    location_name = get_location_name(device)
    if location_name:
        groups.append(location_name)  # e.g., "ICT11"
    
    # 3. Contact (Ownership from custom_fields.Sahiplik)
    custom_fields = device.get('custom_fields', {})
    if custom_fields.get('Sahiplik'):
        groups.append(custom_fields['Sahiplik'])  # e.g., "TEAM VIRTUALIZATION"
    
    return ','.join(groups)
```

**Zabbix Field:** `groups[]` (host group IDs after resolution)

**Example:**
```
Netbox:
  - device_type (determined) = "Lenovo IPMI"
  - device.location.name = "ICT11"
  - device.custom_fields.Sahiplik = "TEAM VIRTUALIZATION"
↓
Host Groups String: "Lenovo IPMI,ICT11,TEAM VIRTUALIZATION"
↓
Resolve to IDs:
  - "Lenovo IPMI" → groupid: 45
  - "ICT11" → groupid: 17
  - "TEAM VIRTUALIZATION" → groupid: 102 (created if not exists)
↓
Zabbix: groups = [{"groupid": "45"}, {"groupid": "17"}, {"groupid": "102"}]
```

---

## 4. Tags Extraction

### 4.1 Standard Tags

**Parsing Logic:**
```python
def extract_tags(device):
    tags = {}
    
    # Manufacturer
    manufacturer = device.get('device_type', {}).get('manufacturer', {})
    if manufacturer.get('name'):
        tags['Manufacturer'] = manufacturer['name']
    
    # Device Type (Model)
    device_type = device.get('device_type', {})
    if device_type.get('model'):
        tags['Device_Type'] = device_type['model']
    elif device_type.get('display'):
        tags['Device_Type'] = device_type['display']
    
    # Location Detail
    location = device.get('location', {})
    site = device.get('site', {})
    if location.get('name'):
        tags['Location_Detail'] = location['name']
    elif site.get('name'):
        tags['Location_Detail'] = site['name']
    
    # City
    if site.get('name'):
        tags['City'] = site['name']
    
    # Tenant (Organization/Company)
    tenant = device.get('tenant', {})
    if tenant.get('name'):
        tags['Tenant'] = tenant['name']
    
    # Contact (Ownership from custom_fields.Sahiplik) - IMPORTANT: Also added as host group
    custom_fields = device.get('custom_fields', {})
    if custom_fields.get('Sahiplik'):
        tags['Contact'] = custom_fields['Sahiplik']
    
    # Responsible Team
    if custom_fields.get('Sorumlu_Ekip'):
        tags['Sorumlu_Ekip'] = custom_fields['Sorumlu_Ekip']
    
    # Loki ID (PRIMARY UNIQUE IDENTIFIER)
    if device.get('id'):
        tags['Loki_ID'] = str(device['id'])
    
    # Rack Information
    rack = device.get('rack')
    if rack and isinstance(rack, dict):
        if rack.get('name'):
            tags['Rack_Name'] = rack['name']
        rack_role = rack.get('role', {})
        if rack_role.get('name'):
            tags['Rack_Type'] = rack_role['name']
    
    # Cluster
    cluster = device.get('cluster')
    if cluster and isinstance(cluster, dict) and cluster.get('name'):
        tags['Cluster'] = cluster['name']
    
    # Hall (Location Description)
    if location and isinstance(location, dict):
        if location.get('description'):
            tags['Hall'] = location['description']
        elif location.get('name'):
            tags['Hall'] = location['name']
    
    # Installation Date
    if custom_fields.get('Kurulum_Tarihi'):
        tags['Kurulum_Tarihi'] = custom_fields['Kurulum_Tarihi']
    
    return tags
```

**Zabbix Field:** `tags[]`

**Example:**
```
Netbox:
  - device.id = 12365
  - device.device_type.manufacturer.name = "LENOVO"
  - device.device_type.model = "ThinkAgile HX7531"
  - device.location.name = "ICT11"
  - device.location.description = "DATA HALL 1"
  - device.site.name = "ALMANYA"
  - device.tenant.name = "Company ABC"
  - device.custom_fields.Sahiplik = "TEAM VIRTUALIZATION"
  - device.cluster.name = "vCluster01"
  - device.rack.name = "R101"
  - device.custom_fields.Sorumlu_Ekip = "NOC Team"
  - device.custom_fields.Kurulum_Tarihi = "2024-01-15"
↓
Tags Object:
{
  "Manufacturer": "LENOVO",
  "Device_Type": "ThinkAgile HX7531",
  "Location_Detail": "ICT11",
  "City": "ALMANYA",
  "Tenant": "Company ABC",
  "Contact": "TEAM VIRTUALIZATION",
  "Sorumlu_Ekip": "NOC Team",
  "Loki_ID": "12365",
  "Rack_Name": "R101",
  "Cluster": "vCluster01",
  "Hall": "DATA HALL 1",
  "Kurulum_Tarihi": "2024-01-15"
}
↓
Zabbix Format:
tags = [
  {"tag": "Manufacturer", "value": "LENOVO"},
  {"tag": "Device_Type", "value": "ThinkAgile HX7531"},
  {"tag": "Location_Detail", "value": "ICT11"},
  {"tag": "City", "value": "ALMANYA"},
  {"tag": "Tenant", "value": "Company ABC"},
  {"tag": "Contact", "value": "TEAM VIRTUALIZATION"},
  {"tag": "Sorumlu_Ekip", "value": "NOC Team"},
  {"tag": "Loki_ID", "value": "12365"},
  {"tag": "Rack_Name", "value": "R101"},
  {"tag": "Cluster", "value": "vCluster01"},
  {"tag": "Hall", "value": "DATA HALL 1"},
  {"tag": "Kurulum_Tarihi", "value": "2024-01-15"}
]
```

### 4.2 Loki Native Tags

**Source Field:** `device.tags[]` (Netbox's native tags array)

**Parsing Logic:**
```python
# Loki tags (from Netbox device tags array)
loki_tags = []
device_tags = device.get('tags', [])
for tag in device_tags:
    if isinstance(tag, dict):
        tag_name = tag.get('name', '') or tag.get('slug', '')
        if tag_name:
            loki_tags.append(tag_name)

# Returned separately from standard tags
```

**Zabbix Field:** Appended to `tags[]`

**Example:**
```
Netbox:
  - device.tags = [
      {"name": "production", "slug": "production"},
      {"name": "critical", "slug": "critical"}
    ]
↓
Zabbix (appended to tags):
  {"tag": "production", "value": "production"},
  {"tag": "critical", "value": "critical"}
```

---

## 5. Zabbix Host Matching Logic

### 5.1 Primary Matching: Loki_ID

**Priority:** 1 (Highest)

**Logic:**
```yaml
- name: Check if host exists in Zabbix by Loki_ID
  set_fact:
    zbx_existing_host: "{{ zabbix_hosts_by_loki_id.get(device_info.tags.Loki_ID | string) }}"
  when: 
    - zabbix_hosts_by_loki_id is defined
    - device_info.tags.Loki_ID is defined
    - zabbix_hosts_by_loki_id.get(device_info.tags.Loki_ID | string) is not none
```

**How It Works:**
1. Fetch all Zabbix hosts with their tags
2. Build mapping: `{Loki_ID: host_object}`
3. Check if device's Loki_ID exists in mapping
4. If found → Set `zbx_existing_host` (UPDATE scenario)

**Why Loki_ID is PRIMARY:**
- ✅ **Unique**: Netbox device ID is globally unique
- ✅ **Immutable**: Device ID never changes
- ✅ **Reliable**: Hostname can change, Loki_ID cannot

### 5.2 Fallback Matching: Hostname

**Priority:** 2 (Fallback only if Loki_ID not found)

**Logic:**
```yaml
- name: Fallback to hostname matching if Loki_ID not found
  set_fact:
    zbx_existing_host: "{{ zabbix_hosts_by_hostname.get(netbox_device.name) }}"
  when:
    - zbx_existing_host is not defined or zbx_existing_host == {} or zbx_existing_host.hostid is not defined
    - zabbix_hosts_by_hostname is defined
    - zabbix_hosts_by_hostname.get(netbox_device.name) is not none
```

**How It Works:**
1. Only runs if Loki_ID matching failed
2. Build mapping: `{hostname: host_object}`
3. Check if device's hostname exists in mapping
4. If found → Set `zbx_existing_host` (UPDATE scenario)

### 5.3 Scenario Determination

**Logic:**
```yaml
- name: Determine scenario (create or update)
  set_fact:
    zbx_scenario: "{{ 'update' if (zbx_existing_host is defined and zbx_existing_host is not none and zbx_existing_host.hostid is defined) else 'create' }}"
```

**Outcomes:**
- `zbx_scenario = "update"`: Host exists in Zabbix (matched by Loki_ID or hostname)
- `zbx_scenario = "create"`: Host does not exist (new host)

---

## 6. Zabbix API Field Mapping

### 6.1 Host Creation (scenario: create)

**API Method:** `host.create`

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "host.create",
  "params": {
    "host": "c1h1ict11",                    // from device.name
    "name": "c1h1ict11",                    // from device.name
    "groups": [                              // from extract_host_groups()
      {"groupid": "45"},                     // "Lenovo IPMI"
      {"groupid": "17"}                      // "ICT11"
    ],
    "templates": [                           // from device_type mapping
      {"templateid": "10682"}                // "BLT - Lenovo ICT XCC Monitoring"
    ],
    "interfaces": [                          // from get_primary_ip()
      {
        "type": 2,                           // 2 = SNMP (from template)
        "main": 1,
        "useip": 1,
        "ip": "10.70.1.22",                 // from device.primary_ip4.address
        "dns": "",
        "port": "161",                       // from interface spec
        "details": {
          "version": 2,
          "community": "{$SNMP_COMMUNITY}"
        }
      }
    ],
    "tags": [                                // from extract_tags()
      {"tag": "Manufacturer", "value": "LENOVO"},
      {"tag": "Device_Type", "value": "ThinkAgile HX7531"},
      {"tag": "Loki_ID", "value": "12365"},
      // ... all other tags
    ],
    "monitored_by": 1,                       // 1 = Proxy
    "proxy_groupid": 1                       // from DC_ID → proxy group matching
  },
  "auth": "auth_token",
  "id": 1
}
```

### 6.2 Host Update (scenario: update)

**API Method:** `host.update`

**Request Body (only continuous fields):**
```json
{
  "jsonrpc": "2.0",
  "method": "host.update",
  "params": {
    "hostid": "10084",                       // from zbx_existing_host.hostid
    "host": "c1h2ict11",                     // always update (continuous field)
    "name": "c1h2ict11",                     // always update (continuous field)
    "interfaces": [                          // only if IP changed
      {
        "interfaceid": "30",                 // from zbx_existing_host.interfaces[0].interfaceid
        "ip": "10.70.1.22"                  // new IP
      }
    ],
    "tags": [                                // always update (continuous field)
      {"tag": "Manufacturer", "value": "LENOVO"},
      {"tag": "Tenant", "value": "Company ABC"},
      {"tag": "Contact", "value": "TEAM VIRTUALIZATION"},
      {"tag": "Loki_ID", "value": "12365"},
      // ... all Loki-sourced tags
      // ... + any manual tags (preserved from existing host)
    ],
    "monitored_by": 1,                       // always update (continuous field)
    "proxy_groupid": 1                       // always update (continuous field)
  },
  "auth": "auth_token",
  "id": 2
}
```

**Note:** 
- `groups`, `templates`, and `interface details` (SNMP settings) are **metadata fields** and are **NOT updated** to avoid disrupting existing Zabbix configuration.
- **Manual tags** (tags not sourced from Loki) are **preserved** during updates.

### 6.3 Update Detection Logic

**Comparison Fields:**
1. **Hostname:** `zbx_existing_host.host` vs `zbx_record.HOSTNAME` (NEW)
2. **Display Name:** `zbx_existing_host.name` vs `zbx_record.HOSTNAME` (NEW)
3. **IP Address:** `_existing_interface.ip` vs `zbx_record.HOST_IP`
4. **Monitored By:** `zbx_existing_host.monitored_by` vs `zbx_monitored_by`
5. **Proxy Group:** `zbx_existing_host.proxy_groupid` vs `zbx_proxy_group_id`
6. **Tags:** `zbx_existing_host.tags | to_json` vs `zbx_continuous_tags | to_json`

**Logic:**
```yaml
- name: Check if update is needed
  set_fact:
    _needs_update: >-
      {{
        (
          (_existing_interface.ip | default('') != zbx_record.HOST_IP) or
          (zbx_existing_host.host | default('') != zbx_record.HOSTNAME) or
          (zbx_existing_host.name | default('') != zbx_record.HOSTNAME) or
          (zbx_existing_host.monitored_by | default('') | string != zbx_monitored_by | string) or
          (zbx_existing_host.proxy_groupid | default('') | string != zbx_proxy_group_id | string) or
          (zbx_existing_host.tags | default([]) | to_json != zbx_continuous_tags | to_json)
        ) | bool
      }}
```

**Tag Merge Logic (Preserves Manual Tags):**
```yaml
# Extract all tags from Loki
zbx_continuous_tags: "{{ zbx_tags }}"

# Find manual tags (tags in Zabbix but not from Loki)
zbx_manual_tags: "{{ zbx_existing_host.tags | rejectattr('tag', 'in', zbx_tags | map(attribute='tag') | list) | list }}"

# Merge Loki tags + manual tags
zbx_continuous_tags: "{{ zbx_continuous_tags + zbx_manual_tags }}"
```

**Update Outcomes:**
- `_needs_update = True`: API call made → Status = "güncellendi"
- `_needs_update = False`: No API call → Status = "güncel"

---

## 7. Complete Data Flow Example

### Input: Netbox Device

```json
{
  "id": 12365,
  "name": "c1h2ict11",
  "device_type": {
    "model": "ThinkAgile HX7531",
    "manufacturer": {"name": "LENOVO"}
  },
  "role": {"name": "HOST"},
  "site": {"name": "ALMANYA"},
  "location": {"id": 17, "name": "ICT11", "description": "DATA HALL 1"},
  "tenant": {"name": "Company ABC"},
  "primary_ip4": {"address": "10.70.1.22/24"},
  "cluster": {"name": "vCluster01"},
  "rack": {"name": "R101"},
  "custom_fields": {
    "Sahiplik": "TEAM VIRTUALIZATION",
    "Sorumlu_Ekip": "NOC Team",
    "Kurulum_Tarihi": "2024-01-15"
  },
  "tags": [{"name": "production"}]
}
```

### Step 1: Parse Device

```yaml
hostname: "c1h2ict11"
primary_ip: "10.70.1.22"
device_type: "Lenovo IPMI"
location: "ICT11"
```

### Step 2: Extract Host Groups

```yaml
host_groups: "Lenovo IPMI,ICT11,TEAM VIRTUALIZATION"  # from device_type + location + Sahiplik
```

### Step 3: Extract Tags

```yaml
tags:
  - {tag: "Manufacturer", value: "LENOVO"}
  - {tag: "Device_Type", value: "ThinkAgile HX7531"}
  - {tag: "Location_Detail", value: "ICT11"}
  - {tag: "City", value: "ALMANYA"}
  - {tag: "Tenant", value: "Company ABC"}
  - {tag: "Contact", value: "TEAM VIRTUALIZATION"}
  - {tag: "Sorumlu_Ekip", value: "NOC Team"}
  - {tag: "Loki_ID", value: "12365"}
  - {tag: "Rack_Name", value: "R101"}
  - {tag: "Cluster", value: "vCluster01"}
  - {tag: "Hall", value: "DATA HALL 1"}
  - {tag: "Kurulum_Tarihi", value: "2024-01-15"}
  - {tag: "production", value: "production"}
```

### Step 4: Check Zabbix Existence

```yaml
# Check 1: By Loki_ID
zabbix_hosts_by_loki_id["12365"] → Found: hostid = "10084"
zbx_scenario: "update"

# If not found by Loki_ID:
# Check 2: By hostname
zabbix_hosts_by_hostname["c1h2ict11"] → Found or Not Found
zbx_scenario: "update" or "create"
```

### Step 5: Compare (if update)

```yaml
Current IP: "10.70.1.22"
New IP: "10.70.1.22"
→ No change

Current Tags: [...existing tags...]
New Tags: [...new tags...]
→ Compare JSON: Different? → Update needed

_needs_update: True (if tags differ) or False (if same)
```

### Step 6: Zabbix API Call

**If scenario = "create":**
```json
{
  "method": "host.create",
  "params": {
    "host": "c1h2ict11",
    "name": "c1h2ict11",
    "groups": [{"groupid": "45"}, {"groupid": "17"}, {"groupid": "102"}],
    "templates": [{"templateid": "10682"}],
    "interfaces": [{...}],
    "tags": [
      {"tag": "Tenant", "value": "Company ABC"},
      {"tag": "Contact", "value": "TEAM VIRTUALIZATION"},
      // ... all Loki tags
    ],
    "monitored_by": 1,
    "proxy_groupid": 1
  }
}
```

**If scenario = "update" AND _needs_update = True:**
```json
{
  "method": "host.update",
  "params": {
    "hostid": "10084",
    "host": "c1h2ict11",          // continuous field
    "name": "c1h2ict11",          // continuous field
    "interfaces": [{...}],        // continuous field
    "tags": [
      {"tag": "Tenant", "value": "Company ABC"},
      {"tag": "Contact", "value": "TEAM VIRTUALIZATION"},
      // ... all Loki tags + manual tags preserved
    ],
    "monitored_by": 1,
    "proxy_groupid": 1
  }
}
```

**If scenario = "update" AND _needs_update = False:**
```
No API call
Status: "güncel" (already up-to-date)
```

### Output: Result

```yaml
device_result:
  hostname: "c1h2ict11"
  status: "güncellendi" or "güncel" or "eklendi"
  ip: "10.70.1.22"
  updated_fields: "Tags güncellendi" or ""
```

---

## 8. Field Summary Table

| Zabbix Field | Netbox Source | Parser Function | Update Type |
|-------------|---------------|-----------------|-------------|
| `host` | `device.name` | Direct | **Continuous** ✅ |
| `name` | `device.name` | Direct | **Continuous** ✅ |
| `interfaces[].ip` | `device.primary_ip4.address` | `get_primary_ip()` | **Continuous** ✅ |
| `interfaces[].details` | SNMP settings | From template | **Metadata** (no update) ❌ |
| `groups[]` | device_type + location + contact | `extract_host_groups()` | **Metadata** (no update) ❌ |
| `templates[]` | device_type mapping | `determine_device_type()` | **Metadata** (no update) ❌ |
| `tags[]` (Loki-sourced) | Multiple Netbox fields | `extract_tags()` | **Continuous** ✅ |
| `tags[]` (Manual) | User-added in Zabbix | N/A | **Preserved** (not overwritten) 🔒 |
| `monitored_by` | Always 1 (Proxy) | Hardcoded | **Continuous** ✅ |
| `proxy_groupid` | location → DC_ID | Proxy group matching | **Continuous** ✅ |

**Field Types:**
- **Continuous (✅):** Updated on every run if changed
- **Metadata (❌):** Set once during creation, never updated
- **Preserved (🔒):** Existing values are kept, not overwritten

---

## 9. Important Notes

### 9.1 Loki_ID as Primary Identifier

**Loki_ID = Netbox Device ID**

- ✅ Stored as Zabbix tag: `{"tag": "Loki_ID", "value": "12365"}`
- ✅ Used for host matching (primary method)
- ✅ Immutable and globally unique
- ✅ Survives hostname changes

### 9.2 Hostname Matching as Fallback

- Only used if Loki_ID not found in Zabbix
- Can fail if hostname changes in Netbox
- Less reliable than Loki_ID matching

### 9.3 Contact and Tenant Fields

**Contact (Ownership):**
- **Netbox:** `device.custom_fields.Sahiplik` (Turkish: "ownership")
- **Zabbix:**
  - ✅ Added to **Host Groups** (as "TEAM VIRTUALIZATION")
  - ✅ Added to **Tags** (as `{"tag": "Contact", "value": "TEAM VIRTUALIZATION"}`)

**Tenant (Organization):**
- **Netbox:** `device.tenant.name`
- **Zabbix:**
  - ✅ Added to **Tags ONLY** (as `{"tag": "Tenant", "value": "Company ABC"}`)
  - ❌ NOT added to Host Groups

### 9.4 Location Hierarchy

- If location has parent → Use parent name for DC_ID
- If no parent → Use location name for DC_ID
- Fallback → Use site name for DC_ID

### 9.5 Update Behavior

**What gets updated (Continuous Fields):**
- ✅ **Hostname** (`host` and `name` fields) - **NEW!**
- ✅ IP address (if changed)
- ✅ Tags from Loki (if changed, manual tags preserved)
- ✅ Proxy group (if changed)
- ✅ Monitored by (if changed)

**What does NOT get updated (Metadata Fields):**
- ❌ Host groups
- ❌ Templates
- ❌ Interface details (SNMP settings, port, community string)

**What gets preserved:**
- 🔒 Manual tags (tags added directly in Zabbix, not from Loki)

---

## 10. API Endpoints Summary

| API Endpoint | Purpose | Used For |
|-------------|---------|----------|
| `GET /api/dcim/devices/` | Fetch all devices | Device list |
| `GET /api/dcim/locations/` | Resolve location names | Location filter, hierarchy |
| `GET /api/dcim/locations/{id}/` | Get location details | Parent lookup |
| `GET /api/ipam/ip-addresses/{id}/` | Get IP details | IP resolution (fallback) |
| `POST /api/method host.create` | Create Zabbix host | New hosts |
| `POST /api/method host.update` | Update Zabbix host | Existing hosts |
| `POST /api/method host.get` | Fetch Zabbix hosts | Host matching |
| `POST /api/method proxygroup.get` | Fetch proxy groups | Proxy resolution |
| `POST /api/method template.get` | Fetch templates | Template ID lookup |
| `POST /api/method hostgroup.get` | Fetch host groups | Group ID lookup |
| `POST /api/method hostgroup.create` | Create host group | Missing groups |

---

## Document Version

- **Version:** 1.0
- **Last Updated:** 2026-01-04
- **Author:** Automated Documentation
- **Related Playbooks:**
  - `playbooks/netbox_to_zabbix_migration.yml`
  - `playbooks/roles/netbox_to_zabbix/tasks/`
  - `playbooks/roles/zabbix_migration/tasks/`

