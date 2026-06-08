# Ansible AWX / AAP — Inventory → Zabbix sync

Guide for running [`playbooks/netbox_zabbix_sync.yaml`](../../playbooks/netbox_zabbix_sync.yaml) and role `netbox_zabbix_sync` on AWX.

**Turkish detailed reference (Survey, scenarios, SQL):** [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md)

**Data flow diagrams:** [SYNC_DATA_FLOW.md](../design/SYNC_DATA_FLOW.md)

---

## Prerequisites

- EE can reach PostgreSQL discovery DB, Zabbix JSON-RPC, and (if any `*_source: loki`) NetBox API.
- SCM checks out `project-zabake` / `zabbix-netbox`.
- Playbook uses `hosts: localhost`.

## Job template

| Field | Value |
|-------|--------|
| Inventory | Contains `localhost` |
| Playbook | `playbooks/netbox_zabbix_sync.yaml` |
| Extra vars | See sections below |

---

## Required variables (playbook validation)

Always validated in playbook `pre_tasks`:

| Variable | Description |
|----------|-------------|
| `discovery_db_host`, `discovery_db_name`, `discovery_db_user`, `discovery_db_password` | PostgreSQL discovery DB |
| `discovery_db_port` | Default `5000` in role; often `5432` in AWX |
| `zabbix_url`, `zabbix_user`, `zabbix_password` | Zabbix API (required even when `only_fetch: true`) |
| `zabbix_validate_certs` | Default `false` |
| `zabbix_api_timeout` | Default `300` (seconds); timeout for all Zabbix JSON-RPC `uri` calls |

## Conditional: NetBox (Loki) API

Required when **any** of `device_source`, `platform_source`, `virtual_fw_source` is `loki`:

| Variable | Description |
|----------|-------------|
| `netbox_url` | NetBox base URL |
| `netbox_token` | API token |
| `netbox_verify_ssl` | Default `false` |

---

## Inventory source routing (per host type)

| Variable | Allowed | Default | `loki` | `datalake` |
|----------|---------|---------|--------|------------|
| `device_source` | `loki`, `datalake` | `datalake` | NetBox devices API | SQL `discovery_netbox_inventory_device` |
| `platform_source` | `loki`, `datalake` | `loki` | NetBox platforms API | SQL `discovery_netbox_platform` |
| `virtual_fw_source` | `loki`, `datalake` | `loki` | custom-objects virtual_fws | SQL `discovery_netbox_inventory_virtual_fw` |

Logged as `inventory_source` on device operations.

---

## Sync scope and modes

| Variable | Default | Description |
|----------|---------|-------------|
| `sync_devices` | `true` | Device sync |
| `sync_platforms` | `false` | Platform sync |
| `sync_virtual_fws` | `false` | Virtual firewall sync |
| `only_fetch` | `false` | Fetch only; no Zabbix processing |
| `dry_run` | `false` | Full logic; no `host.create` / `host.update` |
| `report_izlenmeyecek` | `true` | Include non-monitored items in report |
| `device_limit` | `0` | `0` = no limit |
| `location_filter` | `""` | Location name filter |
| `create_devices_disabled` | `false` | New device hosts disabled in Zabbix |
| `create_platforms_disabled` | `false` | New platform hosts disabled |
| `create_virtual_fws_disabled` | `false` | New VFW hosts disabled |

---

## HMDL audit (recommended for production)

| Variable | Default |
|----------|---------|
| `hmdl_log_enabled` | `false` |
| `hmdl_log_schema` | `hmdl` |
| `hmdl_log_table` | `zabbix_sync_log` |
| `hmdl_playbook_name` | `db_to_zabbix_sync` |
| `hmdl_db_*` | Defaults to discovery DB connection |

Schema: [`SQL/zabbix-netbox/`](../../../SQL/zabbix-netbox/README.md).

Smart-merge columns: `proxy_manual_change_detected`, `field_merge_actions`, `last_managed_groups`.

---

## Email

| Variable | Default |
|----------|---------|
| `mail_recipients` | `[]` (no mail if empty) |
| `mail_smtp_*`, `mail_from` | See `defaults/main.yml` |

---

## Example: production devices from datalake

```yaml
discovery_db_host: "postgresql.example.com"
discovery_db_port: 5432
discovery_db_name: "bulutlake"
discovery_db_user: "zabbix_sync"
discovery_db_password: "{{ vault_discovery_password }}"

zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "api_sync"
zabbix_password: "{{ vault_zabbix_password }}"

device_source: datalake
platform_source: loki
virtual_fw_source: loki
netbox_url: "https://loki.example.com"
netbox_token: "{{ vault_netbox_token }}"

sync_devices: true
sync_platforms: false
sync_virtual_fws: false
dry_run: false
hmdl_log_enabled: true
mail_recipients: ["noc@example.com"]
```

---

## Smart merge (update path)

- **Tags / groups / macros:** Managed fields from config + inventory; manual Zabbix values preserved.
- **Visible name:** Preserved when manual change detected vs last HMDL row.
- **Proxy group:** Updated on location change; if location unchanged and Zabbix proxy differs from expected without matching last log → **not updated**, `proxy_manual_change_detected: true`.

See [SYNC_DATA_FLOW.md](../design/SYNC_DATA_FLOW.md).

---

## Related docs

- [AWX_KULLANIM_REHBERI.md](AWX_KULLANIM_REHBERI.md) — full TR guide + Survey table
- [SYNC_DATA_FLOW.md](../design/SYNC_DATA_FLOW.md)
- [HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md](../design/HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md)
