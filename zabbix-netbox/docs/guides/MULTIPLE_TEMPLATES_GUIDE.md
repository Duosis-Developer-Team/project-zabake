# Multiple Templates per Device Type Guide

## Overview

The sync system natively supports assigning **multiple Zabbix templates** to a single device or platform by listing them under the same `device_type` key in `templates.yml`. No code changes are needed — only YAML configuration.

---

## How It Works

`templates.yml` maps each `device_type` to a **YAML list** of template objects. During sync, `zabbix_host_operations.yml` resolves every template name in that list via the Zabbix `template.get` API and passes all resolved IDs to `host.create` or verifies them on `host.update`.

```
templates.yml
  └─ device_type key (e.g. "Huawei Backbone Switch")
       └─ list of template objects
            ├─ template 1: name, type, host_groups, macros (optional)
            └─ template 2: name, type, host_groups, macros (optional)

zabbix_host_operations.yml
  ├─ template.get  ──> resolves all names to IDs
  ├─ zbx_template_id_list = [{ templateid: "..." }, { templateid: "..." }, ...]
  └─ host.create   ──> templates: zbx_template_id_list
```

---

## Single Template vs. Multiple Templates

### Single template (current default pattern)

```yaml
Huawei Backbone Switch:
  - name: BLT - Huawei VRP SNMP
    type: snmpv2
    host_groups:
      - "Network Devices"
```

### Multiple templates

```yaml
Huawei Backbone Switch:
  - name: BLT - Huawei VRP SNMP
    type: snmpv2
    host_groups:
      - "Network Devices"
  - name: BLT - Template SNMP Device Huawei BGP
    type: snmpv2
    host_groups:
      - "Network Devices"
```

Both templates will be attached to the Zabbix host when it is created.

---

## Template Object Fields

Each item in the list supports the following fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Exact Zabbix template name (must exist in Zabbix) |
| `type` | Yes | Interface type key from `template_types.yml` (`snmpv2`, `snmpv3`, `agent`, `API`) |
| `host_groups` | No | Additional host groups to assign to the host; merged across all templates |
| `macros` | No | Zabbix host macros to set; merged across all templates; supports `{HOST.IP}` placeholder |

---

## Behavior When Multiple Templates Are Defined

### Template ID Resolution

All template names are sent to Zabbix in a single `template.get` API call. If **any** template name is not found in Zabbix, host creation is blocked with a validation error listing the missing names:

```
Zabbix'te bulunamayan şablonlar: BLT - Missing Template Name
```

Resolve this by ensuring all template names in `templates.yml` exist in Zabbix before running the sync.

### Interface Type Selection

Zabbix requires **one** interface per host. When multiple templates are listed, the interface type is taken from the **first template's** `type` field:

```yaml
HPE Switch:
  - name: BLT - HPE Main SNMP          # type: snmpv2 → this interface type is used
    type: snmpv2
  - name: BLT - HPE Power Monitoring    # type: agent → triggers a warning, not used for interface
    type: agent
```

If the `type` values differ across templates, a warning is printed during the run:

```
Multiple template types found ['snmpv2', 'agent']; using 'snmpv2'
```

**Best practice:** Use the same `type` for all templates on a device type, or deliberately put the desired interface type on the first template.

### Macro Merging

Macros from all templates in the list are **merged into a single set**. If the same macro key appears in multiple templates, the last occurrence wins (last template in the list takes precedence):

```yaml
Dell IPMI:
  - name: BLT - Dell iDRAC SNMP
    type: snmpv2
    host_groups:
      - "Physical Hosts"
  - name: BLT - Dell iDRAC Redfish
    type: snmpv2
    macros:
      "{$REDFISH.API.URL}": "https://{HOST.IP}/"
      "{$REDFISH.USER}": "zabbix"
      "{$REDFISH.PASSWORD}": "secret"
```

The resulting host receives macros from both templates combined.

The `{HOST.IP}` placeholder in macro values is replaced with the device's actual IP address during processing.

### Host Group Merging

Host groups from all templates are merged and deduplicated:

```yaml
ExampleDevice:
  - name: Template A
    type: snmpv2
    host_groups:
      - "Physical Hosts"
  - name: Template B
    type: snmpv2
    host_groups:
      - "Storage Devices"
      - "Physical Hosts"   # duplicate — removed automatically
```

The host receives: `Physical Hosts`, `Storage Devices` (plus the device_type group and any NetBox-derived groups).

### Duplicate Template IDs

If multiple template names resolve to the same Zabbix `templateid` (e.g. aliases), duplicates are removed automatically before `host.create`:

```yaml
zbx_tpl_unique_templates: "{{ result | unique(attribute='templateid') }}"
```

---

## Practical Examples

### Example 1: Adding BGP monitoring to Huawei switches

Current state — single template:

```yaml
Huawei Backbone Switch:
  - name: BLT - Huawei VRP SNMP
    type: snmpv2
    host_groups:
      - "Network Devices"
```

Updated — add BGP template:

```yaml
Huawei Backbone Switch:
  - name: BLT - Huawei VRP SNMP
    type: snmpv2
    host_groups:
      - "Network Devices"
  - name: BLT - Template SNMP Device Huawei BGP
    type: snmpv2
    host_groups:
      - "Network Devices"
```

> **Note:** If `BLT - Template SNMP Device Huawei BGP` is already linked as a linked template inside `BLT - Huawei VRP SNMP` in Zabbix, attaching it explicitly to the host as well may cause duplicate item key errors on some Zabbix versions. In that case, keep it as a linked template inside Zabbix only and do not add it to `templates.yml`.

---

### Example 2: IPMI server with an additional OS-level agent template

```yaml
Dell IPMI:
  - name: BLT - Dell iDRAC SNMP
    type: snmpv2
    host_groups:
      - "Physical Hosts"
  - name: BLT - Linux by Zabbix Agent Active
    type: agent
    host_groups:
      - "Physical Hosts"
```

Here the interface will be SNMP (from the first template). The agent template will be linked to the host but Zabbix must be configured to collect agent data through a separate interface if needed.

---

### Example 3: Storage device with SNMP and API templates

```yaml
IBM Storage:
  - name: BLT - IBM Storage
    type: API
    host_groups:
      - "Storage Devices"
    macros:
      "{$STORAGE_IP}": "{HOST.IP}"
      "{$IBM_USER}": "zabbix"
      "{$IBM_PASS}": "secretpassword"
  - name: BLT - ICMP Ping
    type: API
    host_groups:
      - "Storage Devices"
```

---

## Step-by-Step: Adding a Second Template to an Existing Device Type

1. Open `mappings/templates.yml`.
2. Find the device type key you want to modify (e.g. `Cisco Switch`).
3. Add a new list item with `name`, `type`, and optionally `host_groups` and `macros`:

   ```yaml
   Cisco Switch:
     - name: BLT - Cisco Catalyst 3750V2-48TS SNMP
       type: snmpv2
       host_groups:
         - "Network Devices"
     - name: BLT - ICMP Ping               # <-- new template
       type: snmpv2
       host_groups:
         - "Network Devices"
   ```

4. Verify the new template name exists in Zabbix (Administration → Templates).
5. Run the playbook. For **new** hosts the templates will be assigned automatically. For existing hosts, you must delete and recreate them, or assign the template manually in Zabbix.

---

## Behavior on Existing Hosts (Update Scenario)

> **Templates are only set during host creation (`host.create`), not during updates (`host.update`).**

When the playbook runs against an already-existing Zabbix host:
- The template list from `templates.yml` is **not** pushed to Zabbix.
- Only IP, hostname, interface, macros, `monitored_by`, and `proxy_groupid` are updated.

To apply a changed template list to an existing host, either:
- Delete the host from Zabbix and re-run the sync (the host will be recreated with the new template list), or
- Manually assign/remove the template in Zabbix.

---

## Validation and Error Handling

| Scenario | Behavior |
|----------|----------|
| All template names found in Zabbix | `host.create` proceeds with full `templateid` list |
| One or more names not found | Validation fails; host is recorded as `eklenemedi` with reason listing missing names |
| `type` values differ across templates | Warning printed; first template's `type` used for interface |
| Template name is `unknown` | Treated as a literal name; `template.get` returns empty; host creation fails |
| Duplicate `templateid`s | Automatically deduplicated before `host.create` |

---

## Reference: `template_types.yml` Interface Types

| type key | Zabbix interface type | Default port | Use when |
|----------|-----------------------|--------------|----------|
| `snmpv2` | SNMP (type 2) | 161 | SNMPv2c monitoring |
| `snmpv3` | SNMP (type 2) | 161 | SNMPv3 monitoring |
| `agent` | Zabbix Agent (type 1) | 10050 | Agent-based monitoring |
| `API` / `api` | No interface | — | HTTP/API templates with no direct interface |

---

## Common Mistakes

### Using `name: unknown` as a placeholder

The value `unknown` is treated as a literal template name. If no Zabbix template is named `unknown`, host creation will fail. Use a comment instead:

```yaml
# TODO: template name not yet determined
# MyDevice:
#   - name: TBD
#     type: snmpv2
```

Or keep the entry disabled by commenting it out until the actual Zabbix template name is known.

### Mismatched template name casing

Template names are matched exactly against Zabbix. `BLT - Huawei VRP SNMP` and `BLT - Huawei VRP snmp` are different names. Always copy the template name directly from the Zabbix UI.

### Adding a linked template that is already embedded in the parent

If Template B is linked inside Template A in Zabbix, and you add both to `templates.yml`, Zabbix may reject the host creation with an "item key already exists" error on some versions. Keep linked templates as links inside Zabbix and list only the parent template in `templates.yml`.
