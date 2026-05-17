# Schema comparison: before vs smart-merge target

Reference: production screenshot (3 tables in `hmdl`) vs canonical DDL in this folder.

## `zabbix_sync_log`

| Column | Before (SQL export) | After (required) |
|--------|---------------------|------------------|
| Core run/device | run_id, source_device_id, zabbix_hostname, status, … | unchanged |
| source_table | default `discovery_netbox_inventory_device` | unchanged |
| **host_entity_type** | — | `device` \| `platform` \| `virtual_fw` |
| **inventory_source** | — | `loki` \| `datalake` |
| **last_visible_name** | — | visible name at sync |
| **last_location** | — | DC root (proxy baseline) |
| **expected_proxy_group_id** | — | calculated from DC_ID |
| **last_proxy_group_id** | — | automation-assigned proxy |
| **zabbix_proxy_group_id** | — | proxy on Zabbix before update |
| **proxy_location_change** | — | location changed → proxy updated |
| **proxy_manual_change_detected** | — | manual proxy override |
| **field_merge_actions** | — | JSON per-field merge outcome |
| **last_managed_groups** | — | JSON array of managed groups |
| **dry_run** | — | playbook dry_run flag |

## `zabbix_host_update_log`

| Column | Before | After |
|--------|--------|-------|
| field-level audit | field_name, old/new, action, status | unchanged |
| **host_entity_type** | — | entity type |
| **inventory_source** | — | loki/datalake |
| **merge_result** | — | `updated` \| `preserved_manual` \| `skipped` |
| **dry_run** | — | boolean |
| Indexes | none in export | run_id, device_id, field_name, processed_at |

## `zabbix_tag_update_log`

| Column | Before | After |
|--------|--------|-------|
| tag/macro audit | object_type, key_name, action | unchanged |
| **host_entity_type** | — | entity type |
| **inventory_source** | — | loki/datalake |
| **merge_result** | — | merge outcome |
| **dry_run** | — | boolean |
| Indexes | none in export | run_id, device_id, object_type |

## Apply on existing DB

Run once:

```bash
psql -h <host> -U <user> -d <db> -f migrations/001_smart_merge_audit_columns.sql
```

Playbooks also apply `ADD COLUMN IF NOT EXISTS` when `hmdl_log_enabled: true`.
