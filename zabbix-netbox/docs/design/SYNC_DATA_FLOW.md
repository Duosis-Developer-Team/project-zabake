# NetBox / Datalake → Zabbix sync — data flow

End-to-end description of how inventory is fetched, mapped, merged with Zabbix, and audited. Playbook: [`playbooks/netbox_zabbix_sync.yaml`](../../playbooks/netbox_zabbix_sync.yaml), role: `netbox_zabbix_sync`.

## High-level architecture

```mermaid
flowchart TB
    subgraph awx [AWX Job Template]
        EV[Extra Variables]
    end

    subgraph fetch [1 Fetch layer]
        RD[device_source router]
        RP[platform_source router]
        RV[virtual_fw_source router]
    end

    subgraph sources [Inventory sources]
        Loki[NetBox REST API Loki]
        DB[(PostgreSQL Discovery DB)]
    end

    subgraph zabbix_read [2 Zabbix read]
        ZH[host.get all hosts]
        Maps[Loki_ID / hostname / visible name maps]
    end

    subgraph process [3 Process per record]
        MapYAML[mapping YAML files]
        Proc[process_device / platform / vfw]
        ZOps[zabbix_host_operations]
    end

    subgraph audit [4 Audit optional]
        SyncLog[hmdl.zabbix_sync_log]
        HostLog[hmdl.zabbix_host_update_log]
        TagLog[hmdl.zabbix_tag_update_log]
    end

    subgraph out [5 Output]
        Email[SMTP failure report]
    end

    EV --> RD & RP & RV
    RD -->|loki| Loki
    RD -->|datalake| DB
    RP -->|loki| Loki
    RP -->|datalake| DB
    RV -->|loki| Loki
    RV -->|datalake| DB
    Loki --> Proc
    DB --> Proc
    EV --> ZH --> Maps --> Proc
    MapYAML --> Proc
    Proc --> ZOps
    ZOps --> SyncLog & HostLog & TagLog
    ZOps --> Email
```

## Execution phases (role `tasks/main.yml`)

| Phase | Task file | When | Output facts |
|-------|-----------|------|----------------|
| 1 | Load mappings | Always | `templates_map`, `device_type_mapping`, … |
| 2 | `fetch_all_devices.yml` | `sync_devices` or `only_fetch` | `netbox_devices_*` |
| 3 | `fetch_all_virtual_fws.yml` | `sync_virtual_fws` | `netbox_virtual_fws_raw` |
| 4 | `fetch_all_zabbix_hosts.yml` | Not `only_fetch` | `zabbix_hosts_by_loki_id`, `zabbix_hosts_by_hostname`, `zabbix_hosts_by_visible_name` |
| 5 | Filter/limit devices | After fetch | `netbox_devices_final` |
| 6 | `process_device.yml` loop | `sync_devices` | Per-device JSON in `/tmp/zabbix_host_operation_result_*.json` |
| 7 | `process_platform.yml` loop | `sync_platforms` | Platform results |
| 8 | `process_virtual_fw.yml` loop | `sync_virtual_fws` | VFW results |
| 9 | Aggregate + email | End | `processing_results` → SMTP |

Early exit: `only_fetch: true` ends play after fetch summaries (no Zabbix login).

## Inventory source routing

Each host category has its own AWX variable: `device_source`, `platform_source`, `virtual_fw_source` (`loki` | `datalake`).

```mermaid
flowchart LR
    subgraph devices [fetch_all_devices.yml]
        D{device_source}
        D -->|loki| DL[fetch_all_devices_loki.yml]
        D -->|datalake| DD[fetch_all_devices_datalake.yml]
    end

    DL --> API[NetBox API paginated BFS locations]
    DD --> SQL1[discovery_netbox_inventory_device CTE SQL]

    subgraph platforms [fetch_all_platforms.yml]
        P{platform_source}
        P -->|loki| PL[fetch_all_platforms_loki.yml]
        P -->|datalake| PD[fetch_all_platforms_datalake.yml]
    end

    PL --> API2[NetBox dcim/platforms API]
    PD --> SQL2[discovery_netbox_platform]

    subgraph vfw [fetch_all_virtual_fws.yml]
        V{virtual_fw_source}
        V -->|loki| VL[fetch_all_virtual_fws_loki.yml]
        V -->|datalake| VD[fetch_all_virtual_fws_datalake.yml]
    end

    VL --> API3["/api/plugins/custom-objects/virtual_fws/"]
    VD --> SQL3[discovery_netbox_inventory_virtual_fw]
```

### Datalake device fetch (SQL)

[`fetch_all_devices_datalake.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_devices_datalake.yml):

1. `WITH RECURSIVE location_tree` — root location per device (`root_location_name` → `DC_ID`).
2. Join `discovery_loki_location`, `discovery_netbox_platform`, VM cluster maps.
3. Filter `status_value = active` and `izlenmeli` (monitor vs skip queries).
4. Python filter script applies `netbox_device_type_mapping.yml` conditions.

Flat columns used in processing: `device_role_name`, `manufacturer_name`, `device_model`, `sahiplik`, `tags1_name`…`tags5_name`, `root_location_name`, etc.

### Loki device fetch (API)

[`fetch_all_devices_loki.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_devices_loki.yml):

1. Python script paginates NetBox `dcim/devices/`.
2. BFS collects child locations when `location_filter` is set.
3. Same mapping filter script as datalake path.

Requires: `netbox_url`, `netbox_token`, `netbox_verify_ssl`.

## Per-device processing pipeline

```mermaid
sequenceDiagram
    participant NB as Inventory row
    participant PD as process_device.yml
    participant PY as Python processor
    participant ZH as Zabbix maps
    participant ZO as zabbix_host_operations
    participant ZBX as Zabbix API
    participant HMDL as PostgreSQL hmdl.*

    NB->>PD: netbox_device dict
    PD->>PD: izlenmeli check skip
    PD->>PY: device + YAML configs
    PY-->>PD: device_type host_groups tags IP DC_ID
    PD->>ZH: match Loki_ID then hostname then visible name
    PD->>PD: zbx_scenario create or update
    PD->>HMDL: hmdl_read_last_sync baseline
    PD->>ZO: zbx_record + zbx_existing_host
    ZO->>ZO: templates proxy groups tags merge
    alt dry_run false
        ZO->>ZBX: host.create or host.update
    else dry_run true
        ZO->>ZO: preview only
    end
    ZO-->>PD: device_result
    PD->>HMDL: hmdl_sync_log + hmdl_update_log
```

### Mapping YAML (configuration, not inventory)

| File | Role in pipeline |
|------|------------------|
| [`netbox_device_type_mapping.yml`](../../mappings/netbox_device_type_mapping.yml) | Conditions → logical `device_type` |
| [`templates.yml`](../../mappings/templates.yml) | `device_type` → Zabbix templates, macros, `proxy_group_by_dc` |
| [`template_types.yml`](../../mappings/template_types.yml) | Interface type (SNMP/API/…) |
| [`host_groups_config.yml`](../../mappings/host_groups_config.yml) | Sources for host group names |
| [`tags_config.yml`](../../mappings/tags_config.yml) | Managed tag definitions |
| [`datacenters.yml`](../../mappings/datacenters.yml) | Legacy DC helpers (if referenced) |

Processing is **config-driven**: inventory supplies flat fields; YAML defines what becomes Zabbix tags/groups.

## Smart merge on update

When `zbx_scenario == update`, automation does **not** replace the entire Zabbix host blindly.

```mermaid
flowchart TD
    Start[Update path] --> LoadZbx[Read existing host tags groups macros from Zabbix]
    LoadZbx --> LoadHMDL[hmdl_read_last_sync last location proxy visible name]
    LoadHMDL --> Calc[Compute new managed tags groups macros from inventory]
    Calc --> Split{Field type}

    Split -->|Tags| TM[Managed = tags_config names + Loki_Tag_*]
    TM --> TM2[Final = new managed + manual tags]

    Split -->|Host groups| GM[Managed = full required: HOST_GROUPS + template host_groups + DEVICE_TYPE]
    GM --> GM2[Final = managed + manual groups outside managed set]
    GM2 --> GM5[Omit groups on host.update if unchanged]

    Split -->|Macros| MM[Managed = template macro keys]
    MM --> MM2[Final = managed + manual macros]

    Split -->|Visible name| VN{Zabbix differs from last HMDL?}
    VN -->|Manual edit| VNP[Preserve + report]
    VN -->|No| VNU[Apply automation name]

    Split -->|Proxy group| PG{Location changed?}
    PG -->|Yes| PGU[Update proxy to expected]
    PG -->|No| PGM{Zabbix proxy != expected AND != last HMDL log?}
    PGM -->|Yes| PGK[Preserve proxy report manual]
    PGM -->|No| PGU2[Sync if drift]

    TM2 & GM5 & MM2 & VNP & VNU & PGU & PGK --> API[host.update unless dry_run]
```

Reference implementation: [`module_utils/zabbix_merge_helpers.py`](../../playbooks/roles/netbox_zabbix_sync/module_utils/zabbix_merge_helpers.py).

## Host matching (idempotency)

Order used to find existing Zabbix host before create:

1. **Loki_ID** tag → `zabbix_hosts_by_loki_id`
2. **Technical hostname** → `zabbix_hosts_by_hostname`
3. **Visible name** → `zabbix_hosts_by_visible_name`
4. On create duplicate error → same chain in `zabbix_host_operations.yml`

Create path uses technical hostname filter `zabbix_technical_hostname` for ASCII-safe Zabbix `host` field.

## HMDL audit trail

```mermaid
flowchart LR
    subgraph per_host [Per host operation]
        SL[zabbix_sync_log 1 row summary]
        HL[zabbix_host_update_log N rows per field]
        TL[zabbix_tag_update_log N rows per tag/macro]
    end

    SL -->|run_id source_device_id| HL
    SL -->|run_id source_device_id| TL
```

| Table | Written when | Key columns |
|-------|--------------|-------------|
| `hmdl.zabbix_sync_log` | Every processed/skipped host | `status`, `inventory_source`, `proxy_manual_change_detected`, `field_merge_actions` |
| `hmdl.zabbix_host_update_log` | Update with field changes | `field_name`, `merge_result` |
| `hmdl.zabbix_tag_update_log` | Update with tag/macro changes | `object_type`, `key_name`, `action` |

DDL: [`SQL/zabbix-netbox/`](../../../SQL/zabbix-netbox/).

Baseline read for next run: [`hmdl_read_last_sync.yml`](../../playbooks/roles/netbox_zabbix_sync/tasks/hmdl_read_last_sync.yml) — last successful row per `source_device_id`.

## Related documents

- [AWX Kullanım Rehberi](../guides/AWX_KULLANIM_REHBERI.md) — all Extra Variables
- [Host groups and tags](HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md)
- [Location hierarchy](LOCATION_HIERARCHY_RESOLUTION.md)
- [SQL used in datalake fetch](../KULLANILAN_SQLLER.md)
