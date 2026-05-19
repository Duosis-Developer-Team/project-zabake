# NetBox → Zabbix mapping files (index)

This page ties together the YAML files that drive **logical `device_type`** resolution and **Zabbix template assignment** for the `netbox_zabbix_sync` role. Authoritative deep dives live in the linked guides; avoid duplicating long procedures here.

## Data flow

```mermaid
flowchart LR
  subgraph netbox [NetBox]
    Device[DCIM Device]
    Platform[DCIM Platform]
    VFW[Custom virtual_fws]
  end
  subgraph yaml [YAML mappings]
    DTM[netbox_device_type_mapping.yml]
    PM[netbox_platform_mapping.yml]
    VFM[virtual_fw_mapping.yml]
    TPL[templates.yml]
  end
  subgraph zbx [Zabbix]
    Host[Host templates groups]
  end
  Device --> DTM
  DTM -->|"device_type string"| TPL
  Platform --> PM
  PM -->|"device_type string"| TPL
  VFW --> VFM
  VFM -->|"device_type string"| TPL
  TPL --> Host
```

## When to edit which file

| File | Purpose | Typical changes |
|------|---------|-----------------|
| [`mappings/netbox_device_type_mapping.yml`](../../mappings/netbox_device_type_mapping.yml) | Map NetBox **device** records to a logical `device_type` string | New manufacturer / model / role rules; optional `tenant` / `tenants` for customer-specific types; `hostname_prefix` / `hostname_suffix`; `priority` ordering |
| [`mappings/netbox_platform_mapping.yml`](../../mappings/netbox_platform_mapping.yml) | Map NetBox **`platform.manufacturer.name`** to `device_type` and optional **per-DC limits**; optional **name/site** substring rules and **priority** (e.g. Moneygram-specific VMware row) | New virtualization / backup platform rows; `limit_per_dc` (`0` or omitted = no limit); `priority`, `name_contains`, `site_contains`, `match_logic` |
| [`mappings/virtual_fw_mapping.yml`](../../mappings/virtual_fw_mapping.yml) | Map NetBox **custom-objects `virtual_fws`** (`vendor.name` + optional model prefix/suffix) to `device_type` | New firewall vendors/models; enable with role flag `sync_virtual_fws` |
| [`mappings/templates.yml`](../../mappings/templates.yml) | Map `device_type` → list of Zabbix templates, interface `type`, macros, extra host groups | Multiple templates per type; `macros` with `{HOST.IP}` / `{HOST.NAME}`; `host_groups`; `proxy_group_by_dc` |
| [`mappings/platform_tags_config.yml`](../../mappings/platform_tags_config.yml) | Managed tag keys for NetBox **platform** sync on `host.update` (`IP`, `Port`, `Loki_ID`, …) | Add/remove platform tag names; used with `zabbix_merge_tags` (dedupe by tag name) |
| [`mappings/tags_config.yml`](../../mappings/tags_config.yml) | Managed tag keys for **device** sync from datalake/Loki flat fields | Device metadata tags; pairs with `platform_tags_config.yml` for `DEVICE_ROLE: PLATFORM` |

**Invariant:** Every `device_type` produced by **`netbox_device_type_mapping.yml`**, **`netbox_platform_mapping.yml`**, or **`virtual_fw_mapping.yml`** must exist as a **top-level key** in `templates.yml` with **identical spelling** (keys are case-sensitive). The platform section in `templates.yml` is preceded by an in-file comment marking keys required for platform sync.

## Rule summaries

### `netbox_device_type_mapping.yml`

- **Evaluation order:** Entries are sorted by `priority` (**lower number = evaluated first**). After optional tenant filtering, the **first** row whose `conditions` all match wins.
- **Tenant scope:** Optional root-level `tenant` or `tenants`. If `tenants` is present, only that list is used (same-row `tenant` is ignored). Devices without a matching NetBox tenant skip tenant-scoped rows. [`fetch_all_devices.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_devices.yml) applies the same tenant gate as [`process_device.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/process_device.yml).
- **`conditions`:** Combined with **AND**. Supported keys only (anything else never matches — keep in sync with playbook Python and [`tests/test_device_type_mapping.py`](../../tests/test_device_type_mapping.py)):
  - `device_role` — `role.name` / `device_role` (string or list, case-insensitive)
  - `manufacturer` — `device_type.manufacturer.name` (string or list)
  - `model_contains` — substring in model (list: any match)
  - `model_suffix` — model ends with value
  - `name_contains` — substring in device `name`
- **Zabbix visible name:** `hostname_prefix` + normalized NetBox device name + `hostname_suffix` (no automatic separator; include spaces or hyphens in the fields if you want them).

### `netbox_platform_mapping.yml`

- **Manufacturer match:** `manufacturer` is matched against NetBox platform manufacturer with a **case-insensitive full-string** regex (`(?i)^...$`) in [`process_platform.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/process_platform.yml).
- **Evaluation order:** Rows for the same manufacturer are sorted by **`priority`** (**lower number = evaluated first**). The **first** row whose optional name/site rules pass wins (same idea as device mapping `priority`).
- **Optional name/site scope (no NetBox tenant on platforms):** When set, `name_contains` / `site_contains` are **case-insensitive substrings** on platform `name` and on the Site label used for Zabbix (`custom_fields.Site` resolved to `platform_site_code`). Empty/missing filter on a field means “no constraint” for that field. **`match_logic`:** `and` (default) or `or` — how the two substring checks combine when both are non-empty.
- **Fields:** `manufacturer` (required), `device_type` (required; must match a `templates.yml` key), `limit_per_dc` (optional), `priority` (optional; default `999` in playbooks if omitted), `name_contains`, `site_contains`, `match_logic` (optional). DC code extraction for limits follows the comment at the top of the YAML file (first `(DC|AZ|ICT|UZ)[0-9]+` match from the Site/DC label).
- **Moneygram / prod vs DR:** Use a dedicated `device_type` (e.g. `VMware Moneygram`) with matching [`templates.yml`](../../mappings/templates.yml) rows that define **`proxy_group_by_dc`** (`DC13` prod, `DC16` DR). `DC_ID` for platforms is the Site/DC string; [`zabbix_host_operations.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/zabbix_host_operations.yml) extracts the DC code for proxy selection. Tests: [`tests/test_platform_mapping.py`](../../tests/test_platform_mapping.py).

### `virtual_fw_mapping.yml`

- **Source API:** `GET /api/plugins/custom-objects/virtual_fws/?fw_status=active` (see [`fetch_all_virtual_fws.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_virtual_fws.yml)).
- **Match:** First row where `vendor` equals NetBox `vendor.name` (**case-insensitive**), and optional `model_prefix` / `model_suffix` match `manufacturer_model.model` (see filter `virtual_fw_mapping_match` in [`filter_plugins/zabbix_hostname.py`](../../playbooks/roles/netbox_zabbix_sync/filter_plugins/zabbix_hostname.py)).
- **Processing:** [`process_virtual_fw.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/process_virtual_fw.yml); Zabbix role `DEVICE_ROLE=VIRTUAL_FW`; tag merge on update matches platform behavior.

### `templates.yml`

- **Structure:** Top-level key = `device_type`; value = YAML **list** of template objects. Each object needs at least `name` (exact Zabbix template name) and `type` (must exist in [`template_types.yml`](../../mappings/template_types.yml)).
- **Secrets:** Do not commit production passwords or tokens. Prefer AWX credentials, Ansible Vault, or templated extra vars; see [Template macros guide](../guides/TEMPLATE_MACROS_GUIDE.md).

## Ansible path variables

Override these in playbook extra vars if files live outside the default layout ([`defaults/main.yml`](../../playbooks/roles/netbox_zabbix_sync/defaults/main.yml)):

| Variable | Default (relative to playbook dir) |
|----------|----------------------------------|
| `templates_map_path` | `../mappings/templates.yml` |
| `device_type_mapping_path` | `../mappings/netbox_device_type_mapping.yml` |
| `platform_mapping_path` | `../mappings/netbox_platform_mapping.yml` |
| `virtual_fw_mapping_path` | `../mappings/virtual_fw_mapping.yml` |

## Detailed documentation (read next)

| Topic | Document |
|-------|----------|
| Device-type conditions, tenant rules, hostname fields | [README_NETBOX_DEVICE_TYPE_MAPPING.md](README_NETBOX_DEVICE_TYPE_MAPPING.md) |
| Platform sync, `limit_per_dc`, adding a platform type | [PLATFORM_SYNC_GUIDE.md](../guides/PLATFORM_SYNC_GUIDE.md) |
| Host groups / tags derived from mappings | [README_CONFIG.md](../../mappings/README_CONFIG.md) |
| Multiple Zabbix templates per `device_type`, linked-template caveats | [MULTIPLE_TEMPLATES_GUIDE.md](../guides/MULTIPLE_TEMPLATES_GUIDE.md) |
| `macros`, `{HOST.IP}`, API-style templates | [TEMPLATE_MACROS_GUIDE.md](../guides/TEMPLATE_MACROS_GUIDE.md) |

## Related tests

- Device mapping logic: [`tests/test_device_type_mapping.py`](../../tests/test_device_type_mapping.py)
- Platform mapping logic (name/site, priority, DC code for proxy): [`tests/test_platform_mapping.py`](../../tests/test_platform_mapping.py)
- Platform mapping YAML shape: [`tests/test_platforms_feature.py`](../../tests/test_platforms_feature.py)
- Virtual firewall filters: [`tests/test_virtual_fw_filters.py`](../../tests/test_virtual_fw_filters.py)
- `templates.yml` syntax / types: [`tests/test_templates_yaml_syntax.py`](../../tests/test_templates_yaml_syntax.py), [`tests/validate_yaml_syntax.py`](../../tests/validate_yaml_syntax.py)
