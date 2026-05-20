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
  ─ deduplicates the monitor list by NetBox platform `id` (first occurrence wins)
          │
          ▼
  process_platform.yml
  ─ reads netbox_platform_mapping.yml  → resolves device_type + limit_per_dc (+ optional name/site + priority)
  ─ reads templates.yml                → resolves Zabbix template list
  ─ validates IP, site code, DC limit
          │
          ▼
  zabbix_host_operations.yml
  ─ resolves template IDs via template.get
  ─ resolves proxy group by DC code
  ─ sets Zabbix **technical** `host` (ASCII via `zabbix_platform_technical_hostname` — name slug plus `_P_<netbox_platform_id>` within 128 chars) and **visible** `name` (UTF-8 from NetBox)
  ─ calls host.create (or host.update when host already exists — prefetch maps, duplicate-error recovery, or live host.get)
          │
          ▼
  Zabbix Host
  tag: Loki_ID = P_<netbox_platform_id>
```

---

## Files Involved

| File | Role |
|------|------|
| `mappings/netbox_platform_mapping.yml` | Maps NetBox platform manufacturer (+ optional name/site rules) → Zabbix device_type and per-DC limit |
| `mappings/templates.yml` | Maps device_type → list of Zabbix templates to assign |
| `mappings/template_types.yml` | Maps template type string (e.g. `snmpv2`) → Zabbix interface definition |
| `playbooks/roles/netbox_zabbix_sync/defaults/main.yml` | Contains `sync_devices: true`, `sync_platforms: false` defaults |
| `playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_platforms.yml` | Fetches platforms from NetBox API with pagination; **deduplicates by NetBox platform `id`** before returning the monitor list |
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

## Creating hosts as disabled

Newly created Zabbix hosts can be added as disabled by type. These options are disabled by default and only affect `host.create`; existing hosts processed through `host.update` keep their current Zabbix status.

```yaml
create_devices_disabled: true
create_platforms_disabled: true
```

Use `create_devices_disabled` for NetBox device hosts and `create_platforms_disabled` for NetBox platform hosts. Enable only the type that should be created disabled in the current AWX job.

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
# - priority: Lower number = evaluated first (recommended explicit value per row)
# - name_contains / site_contains / match_logic: optional substring rules (platforms have no tenant field)

mappings:
  - manufacturer: "Nutanix"
    device_type: "Nutanix"
    priority: 999
    limit_per_dc: 1
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturer` | string | Yes | Must match `platform.manufacturer.name` in NetBox (case-insensitive) |
| `device_type` | string | Yes | Must exactly match a top-level key in `templates.yml` |
| `limit_per_dc` | integer | No | Maximum platforms of this type per **normalized** DC code (first `(DC|AZ|ICT|UZ)[0-9]+` from Site/DC). `0` or omitted = no limit |
| `priority` | integer | No | Lower = evaluated first. Default in Ansible logic is `999` if omitted |
| `name_contains` | string | No | Case-insensitive substring on NetBox platform **name**; omit or empty = no constraint |
| `site_contains` | string | No | Case-insensitive substring on **Site** label (`custom_fields.Site` → `platform_site_code`); omit or empty = no constraint |
| `match_logic` | string | No | `and` (default) or `or` — combines `name_contains` and `site_contains` when both are set |

> **Important:** The `device_type` value must have a corresponding top-level key in `templates.yml`, otherwise the platform will fail with: `No templates found for device_type <value>`.

### Customer-specific platforms (e.g. Moneygram) without a NetBox tenant

NetBox **Platform** objects do not expose a tenant field like devices. For customer-specific Zabbix templates and **`proxy_group_by_dc`** (prod `DC13` vs DR `DC16`), add **two rows** for the same manufacturer: a **narrow** row with `name_contains` / `site_contains` / `match_logic: or` and **`priority: 1`**, plus a **fallback** row with only `manufacturer` + `device_type` and **`priority: 999`**. Example: `VMware` → `VMware Moneygram` vs `VMware` in [`mappings/netbox_platform_mapping.yml`](../../mappings/netbox_platform_mapping.yml) and `VMware Moneygram` in [`mappings/templates.yml`](../../mappings/templates.yml). Keep mapping selection in sync with [`tests/test_platform_mapping.py`](../../tests/test_platform_mapping.py).

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

1. Before `host.create`, the playbook resolves the Zabbix host by tag `Loki_ID` (`P_<netbox_platform_id>`) using `zabbix_hosts_by_loki_id`, then falls back to **`zabbix_hosts_by_hostname`** using the **technical** host key, then to **`zabbix_hosts_by_visible_name`** using the **visible** name (the original NetBox UTF-8 name). If a host is found, `zbx_scenario` is `update`; otherwise `create`.
2. Zabbix `host.create` / `host.update` use **`host`** = technical ASCII (platforms: transliterated name plus `_P_<id>` suffix) and **`name`** = visible UTF-8 label (`HOST_VISIBLE_NAME`), so Turkish characters remain in the UI name while the API host key stays valid and unique per NetBox platform id.
3. If `host.create` still runs and fails with a duplicate-host error, the playbook falls back to `zbx_scenario: update` by resolving the existing host in order: **Loki_ID from intended tags**, then **technical hostname map**, then **visible name map**, then **live `host.get` by technical `host`**, then **live `host.get` by visible `name`**. This covers a **stale prefetch** (a host created earlier in the same playbook run is not in the in-memory maps) and legacy hosts missing `Loki_ID`. Zabbix often returns `error.message: Invalid params.` with the real text in `error.data` (e.g. `Host with the same name "..." already exists.`); both `message` and `data` are checked for `already exists`.
4. The update modifies: IP address, technical host, visible name, interface, macros, `monitored_by`, and `proxy_groupid`. For **`DEVICE_ROLE: PLATFORM`**, when managed tags differ from Zabbix, **`host.update` sends a deduplicated tag list** built by the `zabbix_merge_tags` module (`module_utils/zabbix_merge_helpers.merge_tags`): manual tags are preserved, keys in `mappings/platform_tags_config.yml` plus `tags_config.yml` are replaced from NetBox. If no managed tag changed, the `tags` parameter is **omitted** (Zabbix keeps existing tags).
5. For non-platform hosts, tag updates on `host.update` use only `tags_config.yml` managed keys (same merge helper); tags are omitted when unchanged.
6. **Host groups on update:** `zabbix_merge_host_groups` uses the full collected required set (`HOST_GROUPS` + `templates.yml` `host_groups` + `DEVICE_TYPE`) — template groups are **not** subtracted from managed names. For **all host types** (including `DEVICE_ROLE: PLATFORM`), `preserve_manual` is **true**: managed groups from Loki/mapping are applied; Zabbix groups added manually outside the managed set are **never removed**. If group membership is unchanged, the `groups` parameter is **omitted** on `host.update` (Zabbix API replaces all groups when `groups` is sent).
6. Templates are **not** updated on existing hosts — only set during creation.

> To force a full template reassignment on an existing platform host, delete it from Zabbix and re-run the sync.

> **Visible name collisions:** `zabbix_hosts_by_visible_name` is keyed by Zabbix `host.name`. If two hosts share the same visible name, the map keeps one entry; rely on `Loki_ID`, unique technical `host` keys (`_P_<id>` suffix on platforms), or the live `host.get` duplicate recovery for disambiguation.

---

## Troubleshooting

### `Invalid params` / `tags/N` — `(tag, value)=(IP, ...) already exists` on `host.update`

**Cause (fixed in 2026-05):** Platform tags such as `IP` were not listed in device-only `tags_config.yml` managed keys. The old Jinja merge kept the existing `IP` tag as “manual” and appended the same `IP` from NetBox again. Zabbix 7.0 rejects duplicate `(tag, value)` pairs in a single `host.update` request (`-32602`); `error.message` is often only `Invalid params.` — see **`error.data`** in AWX logs or the CSV `reason` column.

**Fix (built-in):** `mappings/platform_tags_config.yml` defines platform managed keys; `zabbix_merge_tags` deduplicates by tag name before `host.update`. Re-run the sync after upgrading the role.

---

### `Invalid params` / `tags/N` — `(tag, value)=(Vendor, ...) already exists` on virtual firewall `host.update`

**Symptom:** All VFW rows `EKLENEMEDI`; CSV shows e.g. `Invalid parameter "/1/tags/8": value (tag, value)=(Vendor, Fortinet) already exists.` (Job 109430).

**Cause (fixed in 2026-05):** VFW tags (`Vendor`, `Model`, `Port`, `fw_status`, `proje`, …) were not in `_effective_managed_tag_keys`. `merge_tags` treated them as manual (from Zabbix) and also appended them from NetBox MACROS, producing duplicate tag names in one `host.update` payload.

**Fix (built-in):** `mappings/virtual_fw_tags_config.yml` defines VFW managed keys for `DEVICE_ROLE: VIRTUAL_FW`; `merge_tags` only adds managed keys to the replacement set. Re-run with `sync_virtual_fws: true` after upgrading the role.

**Verify:** `pytest tests/test_tag_merge_strategy.py -v` (includes `test_vfw_tag_merge_no_duplicate`).

---

### "Host with the same name ... already exists" (platform rows, same run)

**Cause:** Zabbix host maps from the start of the play do not include hosts created **earlier in the same run**, or the existing host was created without a `Loki_ID` tag / under a different technical name.

**Fix (built-in):** Duplicate `host.create` errors trigger live `host.get` by technical host and by visible name, then `host.update`. Platforms use a `_P_<id>` technical suffix and tag merge on update so the next run resolves by `Loki_ID` from prefetch.

---

### "Host with the same name ... already exists" on virtual firewall `host.update` (stale Loki_ID host)

**Symptom:** VFW rows `EKLENEMEDI`; CSV reason `Güncelleme hatası: Host with the same name "DIJITAL_KURYE_DC14_VFW_804" already exists.` (e.g. AWX job 109443). Same hostname may appear twice in the report if leftover `/tmp/zabbix_vfw_operation_result_*.json` files were not cleaned up before a previous interrupted run.

**Cause (fixed in 2026-05):** Prefetch resolves the host by `Loki_ID=VFW_<id>` on a **legacy** Zabbix host (old technical `host` / visible name). A **newer** host already owns the canonical technical name (`<slug>_VFW_<id>`). The play attempted `host.update` on the stale host while renaming `host` to the canonical name, which collides with the existing host.

**Fix (built-in):** In [`process_virtual_fw.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/process_virtual_fw.yml), after Loki_ID lookup, if the matched host’s technical name differs from the expected `HOSTNAME` **and** `zabbix_hosts_by_hostname` already has that canonical name, the playbook selects the canonical host for update instead of renaming the stale one. VFW processing also removes leftover `/tmp/zabbix_vfw_operation_result_*.json` before each run ([`main.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/main.yml)).

**Stale hosts:** Orphan Zabbix hosts that still hold the wrong `Loki_ID` tag are not deleted automatically; disable or remove them manually after confirming the canonical host is correct.

**Verify:** `pytest tests/test_zabbix_host_resolution.py::TestVfwHostResolution -v`

---

### Platform host ends up in wrong groups (e.g. `Backup & Replication` + `Veeam` on Nutanix/VMware/NetBackup)

**Symptom:** CSV or Zabbix shows a platform moved from the correct groups (e.g. `Virtual Infrastructure`, `Acropolis`) to unrelated backup groups after sync.

**Cause (fixed in 2026-05):** The old update merge subtracted `templates.yml` `host_groups` from the required set, treated unrelated existing Zabbix groups as “manual”, and sent only group IDs present in `zbx_group_map` — often leaving two IDs from an earlier platform in the same AWX run. Zabbix `host.update` **replaces** all group memberships when `groups` is included.

**Fix (built-in):** `zabbix_merge_host_groups` with full managed set (no template subtraction); per-record reset of `zbx_required_groups_for_record`, `zbx_groups_formatted`, and `_template_host_groups`; merged names must resolve in `zbx_group_map` (create/fail path); omit `groups` when unchanged. Manual Zabbix groups are preserved on all host types.

**Verify:** AWX log `Resolve merged group IDs` should list platform-specific names (`Acropolis`, `VMware`, `NetBackup`, …). Run `pytest tests/test_host_group_merge_strategy.py -v`.

---

### Manual host group removed on platform update (e.g. `test_Bulutistan` dropped)

**Symptom:** A manually added Zabbix host group disappears after platform sync; CSV shows `Groups: …, ManualGroup → …` without the manual group.

**Cause (fixed in 2026-05):** An interim fix used `preserve_manual: false` for `DEVICE_ROLE: PLATFORM`, which stripped all groups outside the mapping-derived set.

**Fix (built-in):** `preserve_manual: true` for all host types. Re-run sync; manual groups are kept unless you remove them in Zabbix.

---

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
