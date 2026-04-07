# Platform Synchronization Guide

## Overview

The platform synchronization feature allows NetBox **Platforms** (virtual/logical groupings of devices such as Nutanix clusters) to be automatically registered as hosts in Zabbix. This is separate from the standard device sync flow and is **disabled by default**.

---

## Architecture

```
NetBox /api/dcim/platforms/
          │
          ▼  (sync_platforms: true)
  fetch_all_platforms.yml
  ─ filters by cf_izlenmeli at API (monitor: Evet+null; skip: Hayır)
  ─ excludes platforms only when izlenmeli means do-not-monitor (Hayır / false); Zabbix CF is not used for inclusion
  ─ optional: location_filter substring match on custom_fields.Site (same playbook var as devices)
          │
          ▼
  process_platform.yml
  ─ reads netbox_platform_mapping.yml  → resolves device_type + limit_per_dc
  ─ reads templates.yml                → resolves Zabbix template list
  ─ validates IP, site code, DC limit
          │
          ▼
  zabbix_host_operations.yml
  ─ resolves template IDs via template.get
  ─ resolves proxy group by DC code
  ─ calls host.create (or falls back to host.update if already exists)
          │
          ▼
  Zabbix Host
  tag: Loki_ID = P_<netbox_platform_id>
```

---

## Files Involved

| File | Role |
|------|------|
| `mappings/netbox_platform_mapping.yml` | Maps NetBox platform manufacturer → Zabbix device_type and per-DC limit |
| `mappings/templates.yml` | Maps device_type → list of Zabbix templates to assign |
| `mappings/template_types.yml` | Maps template type string (e.g. `snmpv2`) → Zabbix interface definition |
| `playbooks/roles/netbox_zabbix_sync/defaults/main.yml` | Contains `sync_devices: true`, `sync_platforms: false` defaults |
| `playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_platforms.yml` | Fetches platforms from NetBox API with pagination |
| `playbooks/roles/netbox_zabbix_sync/tasks/process_platform.yml` | Processes each platform: validates, maps, builds Zabbix record |
| `playbooks/roles/netbox_zabbix_sync/tasks/zabbix_host_operations.yml` | Shared task: creates or updates Zabbix host |

---

## Enabling Platform Sync

Platform sync is disabled by default. To enable it, pass `sync_platforms=true` as an extra variable when running the playbook:

```bash
ansible-playbook playbooks/netbox_zabbix_sync.yaml \
  -e netbox_url=https://netbox.example.com \
  -e netbox_token=YOUR_TOKEN \
  -e zabbix_url=https://zabbix.example.com/api_jsonrpc.php \
  -e zabbix_user=Admin \
  -e zabbix_password=YOUR_PASSWORD \
  -e sync_platforms=true
```

When running in AWX/Tower, set `sync_platforms: true` in the **Extra Variables** field of the Job Template.

---

## Location filter for platforms

The playbook variable `location_filter` (e.g. `DC13`) applies to **platform sync** as well as device sync. When set and non-empty, only platforms whose NetBox custom field **`Site`** contains the filter string (case-insensitive substring) are kept after the izlenmeli-based list is built. Examples: `DC13` matches `DC13-G12` and `DC13-G1-AHV-CLS`; it does not match `AZ11-CLS` or `DC14`.

---

## Platforms only (skip device sync)

By default the role syncs **devices** (`sync_devices: true`) and optionally **platforms** (`sync_platforms: false`). To run **only** platform synchronization (no NetBox device API fetch, no `process_device`, no device CSV/email rows from devices):

```yaml
sync_devices: false
sync_platforms: true
```

Requirements:

- Zabbix API is still used (`fetch_all_zabbix_hosts`) so platform host create/update can resolve templates, groups, and the “host already exists” fallback.
- `only_fetch: true` still pulls NetBox devices for inspection even if `sync_devices: false` (see `defaults/main.yml`).
- If all of `sync_devices`, `sync_platforms`, and `only_fetch` are off, the role **fails** with a clear message.

---

## NetBox Platform Requirements

For a platform to be successfully synced, the following must be set on the NetBox platform object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Used as the Zabbix hostname |
| `manufacturer` | FK | Yes | Must match a `manufacturer` entry in `netbox_platform_mapping.yml` (case-insensitive) |
| `custom_fields.ip_addresses` | string | Yes | Primary IP address; used as Zabbix host IP |
| `custom_fields.Site` or `custom_fields.DC` | string | Yes | Site/DC code matching pattern `(DC\|AZ\|ICT\|UZ)[0-9]+` (e.g. `DC11`, `AZ02`) |
| `custom_fields.izlenmeli` | choice / bool | No | `Hayır` or `false` skips the platform; `null`, `Evet`, or `true` includes it |
| `custom_fields.Zabbix` | boolean | No | Not used for fetch inclusion (optional metadata only) |
| `custom_fields.Port` | string | No | Stored as Zabbix tag |
| `custom_fields.URL` | string | No | Stored as Zabbix tag |

---

## Configuration: `netbox_platform_mapping.yml`

Located at `mappings/netbox_platform_mapping.yml`.

### Structure

```yaml
---
# Mapping NetBox platforms to Zabbix DEVICE_TYPE and per-DC limits
#
# - manufacturer: NetBox platform.manufacturer.name (case-insensitive match)
# - device_type:  Key in templates.yml that defines Zabbix templates
# - limit_per_dc: Maximum number of platforms per DC for this device_type (0 or missing = no limit)

mappings:
  - manufacturer: "Nutanix"
    device_type: "Nutanix"
    limit_per_dc: 1
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturer` | string | Yes | Must match `platform.manufacturer.name` in NetBox (case-insensitive) |
| `device_type` | string | Yes | Must exactly match a top-level key in `templates.yml` |
| `limit_per_dc` | integer | No | Maximum platforms of this type per **normalized** DC code (first `(DC|AZ|ICT|UZ)[0-9]+` from Site/DC). `0` or omitted = no limit |

> **Important:** The `device_type` value must have a corresponding top-level key in `templates.yml`, otherwise the platform will fail with: `No templates found for device_type <value>`.

---

## Configuration: `templates.yml` (Platform Section)

Every `device_type` referenced in `netbox_platform_mapping.yml` must have a matching key in `mappings/templates.yml`.

### Example: Nutanix platform template definition

```yaml
Nutanix:
  - name: BLT - Nutanix
    type: snmpv2
    host_groups:
      - "Storage Devices"
```

See [MULTIPLE_TEMPLATES_GUIDE.md](MULTIPLE_TEMPLATES_GUIDE.md) to learn how to assign multiple templates to a single platform device type.

---

## Adding a New Platform Type — Step by Step

### Step 1: Identify the manufacturer name in NetBox

Go to NetBox → DCIM → Platforms → open the platform → note the **Manufacturer** field value exactly (e.g. `VMware`).

### Step 2: Add a Zabbix template entry in `templates.yml`

Open `mappings/templates.yml` and add a new top-level key. The key will become your `device_type`:

```yaml
VMware vSphere:
  - name: BLT - VMware vSphere by HTTP
    type: API
    host_groups:
      - "Virtual Infrastructure"
    macros:
      "{$VMWARE.URL}": "https://{HOST.IP}/sdk"
      "{$VMWARE.USERNAME}": "zabbix"
      "{$VMWARE.PASSWORD}": "yourpassword"
```

Available `type` values and their resulting Zabbix interface definitions are in `mappings/template_types.yml`:
- `snmpv2` — SNMPv2 interface on port 161
- `snmpv3` — SNMPv3 interface on port 161
- `agent` — Zabbix Agent interface on port 10050
- `API` / `api` — No interface (API-only templates)

### Step 3: Add a mapping entry in `netbox_platform_mapping.yml`

```yaml
mappings:
  - manufacturer: "VMware"
    device_type: "VMware vSphere"
    limit_per_dc: 0          # 0 = no limit

  - manufacturer: "Nutanix"
    device_type: "Nutanix"
    limit_per_dc: 1
```

The `manufacturer` value must match the NetBox platform's manufacturer name **exactly** (matching is case-insensitive).  
The `device_type` value must match the key you added in `templates.yml` **exactly** (case-sensitive).

### Step 4: Verify the NetBox platform has required custom fields

Confirm the following custom fields are populated on the platform in NetBox:
- `ip_addresses`: the IP address for Zabbix monitoring
- `Site` or `DC`: a valid site code (e.g. `DC11`)
- `izlenmeli`: must not be `Hayır` / `false` if the platform should sync

### Step 5: Run the playbook with `sync_platforms=true`

```bash
ansible-playbook playbooks/netbox_zabbix_sync.yaml \
  -e netbox_url=https://netbox.example.com \
  -e netbox_token=YOUR_TOKEN \
  -e zabbix_url=https://zabbix.example.com/api_jsonrpc.php \
  -e zabbix_user=Admin \
  -e zabbix_password=YOUR_PASSWORD \
  -e sync_platforms=true
```

---

## Per-DC Limit (`limit_per_dc`)

The `limit_per_dc` field controls how many platforms of a given `device_type` are allowed per **logical DC code** within a single playbook run.

| Value | Behavior |
|-------|----------|
| `0` | No limit — all platforms are synced |
| `1` | Only the first platform of this type per logical DC is synced |
| `N` | At most N platforms per logical DC per run |

**DC bucket (what “per DC” means):** The playbook takes `custom_fields.Site` or `custom_fields.DC` (same as `platform_site_code` / Zabbix `DC_ID`) and derives a **normalized** key by matching the first `(DC|AZ|ICT|UZ)[0-9]+` substring (case-insensitive), then uppercasing it. Examples: `DC13-G12`, `DC13-G13`, and `dc13-FC1-CLS` all map to **`DC13`** for counting. `DC_ID` and tags still use the full Site/DC string from NetBox.

**How it works:** Platforms are processed in the order returned by the NetBox API. The usage counter is keyed by `(device_type, normalized DC)`. When `limit_per_dc` is already reached for that pair, the platform is not sent to Zabbix and receives status `eklenemedi` with reason `DC limit exceeded for <device_type> in <normalized DC> (site: <full site>)`.

**Example use case:** For Nutanix clusters, you typically want one Zabbix host per DC (representing the cluster endpoint), so `limit_per_dc: 1` keeps a single sync per `DC13`-style code even if NetBox lists many rows with different `Site` suffixes under the same DC.

---

## Zabbix Tags Created for Platforms

Each platform synced to Zabbix receives the following tags:

| Tag Key | Source |
|---------|--------|
| `IP` | `custom_fields.ip_addresses` |
| `Port` | `custom_fields.Port` |
| `URL` | `custom_fields.URL` |
| `Site` | Site code from `custom_fields.Site` or `custom_fields.DC` |
| `DC` | `custom_fields.DC` |
| `Manufacturer` | `platform.manufacturer.name` |
| `Created` | `platform.created` |
| `Last_Updated` | `platform.last_updated` |
| `Loki_Platform_ID` | NetBox platform numeric ID |
| `Loki_ID` | `P_<platform_id>` — unique platform identifier used for idempotent updates |

---

## How Existing Platforms are Handled

When a platform is synced again after already existing in Zabbix:

1. The playbook always uses `zbx_scenario: create` for platforms.
2. If the `host.create` API call returns an "already exists" error, the playbook falls back to `zbx_scenario: update`.
3. The update modifies: IP address, hostname, interface, macros, `monitored_by`, and `proxy_groupid`.
4. Tags are **not** updated on existing hosts — they are only written during creation.
5. Templates are **not** updated on existing hosts — only set during creation.

> To force a template/tag update on an existing platform host, delete it from Zabbix and re-run the sync.

---

## Troubleshooting

### "No platform mapping found for manufacturer X"

**Cause:** The platform's manufacturer in NetBox has no entry in `netbox_platform_mapping.yml`.

**Fix:** Add a mapping entry as described in Step 3 above.

---

### "No templates found for device_type X"

**Cause:** The `device_type` value in `netbox_platform_mapping.yml` does not match any top-level key in `templates.yml`.

**Fix:** Add the corresponding key to `templates.yml` as described in Step 2. Keys are **case-sensitive**.

---

### "Standart dışı site kodu"

**Cause:** The `Site` or `DC` custom field value on the NetBox platform does not match the expected pattern `(DC|AZ|ICT|UZ)[0-9]+`.

**Fix:** Update the custom field value in NetBox to use a valid site code (e.g. `DC11`, `AZ02`, `ICT01`).

---

### "IP address is missing on platform"

**Cause:** The `ip_addresses` custom field is empty or not set on the NetBox platform.

**Fix:** Set the `ip_addresses` custom field on the platform in NetBox.

---

### Platform not picked up during fetch

**Causes:**
- `custom_fields.izlenmeli` is set to `Hayır` or boolean/string `false`
- NetBox API monitor filter excludes rows that are not `Evet` or `null` for `izlenmeli` (if your NetBox stores another “yes” value, confirm it matches the API filter)
- `location_filter` is set and `custom_fields.Site` does not contain that substring

**Fix:** Set `izlenmeli` to `null`, `Evet`, or `true` for platforms that should sync; adjust `Site` or `location_filter` as needed.

---

### "DC limit exceeded for X in DC11"

**Cause:** More platforms of a given `device_type` exist in NetBox for the same **normalized** DC code than `limit_per_dc` allows (see [Per-DC Limit](#per-dc-limit-limit_per_dc)).

**Fix:** Either increase `limit_per_dc` in `netbox_platform_mapping.yml`, or set `limit_per_dc: 0` to remove the limit.

---

## Current Active Mappings

| Manufacturer | device_type | limit_per_dc | Zabbix Template |
|-------------|-------------|--------------|-----------------|
| Nutanix | Nutanix | 1 | BLT - Nutanix |
