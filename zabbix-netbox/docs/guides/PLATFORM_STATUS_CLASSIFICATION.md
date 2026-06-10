# Platform Status Classification

Reference for how NetBox **platforms** are included or excluded in HMDL automation, and how the same rules drive **NiFi collector config** (`datalake-collectors`) with status annotations in audit logs.

See also: [PLATFORM_SYNC_GUIDE.md](PLATFORM_SYNC_GUIDE.md) (Zabbix host sync), [datalake-collectors DC rollout](../../../datalake-collectors/docs/guides/DC_ROLLOUT_GUIDE.md).

---

## Two consumers, one rule set

| Consumer | Purpose | `izlenmeli=Hayır` behavior |
|----------|---------|------------------------------|
| **zabbix-netbox** | Create/update Zabbix hosts | Excluded from sync (`atlandı`) |
| **datalake-collectors** | Reconcile `configuration_file.json` on NiFi | **Included in config**; logged with `[platform_status: not_monitored]` |

Zabbix sync behavior is unchanged. Collector sync uses classification from this document for logging only.

---

## Inclusion pipeline (Zabbix)

```
NetBox /api/dcim/platforms/
  → fetch (cf_izlenmeli Evet + null → monitor; Hayır → skip list)
  → optional location_filter on Site
  → parallel_compare_engine.compare_one_platform
      → izlenmeli Hayır → skip (atlandı)
      → invalid site regex / missing IP / no mapping → skip (eklenemedi)
      → OK → Zabbix host.create/update
```

Sources:

- [fetch_all_platforms_loki.yml](../../playbooks/roles/netbox_zabbix_sync/tasks/fetch_all_platforms_loki.yml)
- [parallel_compare_engine.py](../../playbooks/roles/netbox_zabbix_sync/files/parallel_compare_engine.py) (`compare_one_platform`)

---

## Status categories (collector logging)

| Code | Detection | NiFi config |
|------|-----------|-------------|
| `monitored` | Default when not below | Yes (if mapped + valid IP/site) |
| `not_monitored` | `custom_fields.izlenmeli` or `monitor_edilmeli_mi` = Hayır / no / false / 0 | Yes + status note |
| `customer_environment` | Row in [netbox_platform_mapping.yml](../../mappings/netbox_platform_mapping.yml) with `customer_environment: true` and name/site match | Yes + status note |
| `unmapped` | No row in [netbox_platform_collector_mapping.yml](../../../datalake-collectors/mappings/netbox_platform_collector_mapping.yml) | No |
| `invalid` | Missing IP or site code outside `(DC\|AZ\|ICT\|UZ)[0-9]+` | No |

Combined statuses use `; ` (e.g. `customer_environment; not_monitored`).

---

## NetBox fields

| Field | Used for |
|-------|----------|
| `custom_fields.izlenmeli` | Primary monitor flag |
| `custom_fields.monitor_edilmeli_mi` | Legacy alias |
| `custom_fields.Site` / `DC` | DC code, location_filter, customer site rules |
| `custom_fields.ip_addresses` | Collector IP / Zabbix host IP |
| `manufacturer.name` | Mapping to collector type / Zabbix device_type |
| `custom_fields.Zabbix` | **Not** used for inclusion |

---

## Customer environment (Moneygram example)

Platforms have **no NetBox tenant**. Customer-specific VMware hosts are detected via mapping rules in [netbox_platform_mapping.yml](../../mappings/netbox_platform_mapping.yml):

```yaml
- manufacturer: "VMware"
  device_type: "VMware Moneygram"
  name_contains: "moneygram"
  site_contains: "moneygram"
  match_logic: "or"
  customer_environment: true
  priority: 1
```

Collector mapping mirrors the same name/site rules in [netbox_platform_collector_mapping.yml](../../../datalake-collectors/mappings/netbox_platform_collector_mapping.yml) (`collector_type: VmWare`).

### Adding a new customer rule

1. Add a row to `netbox_platform_mapping.yml` with `name_contains` / `site_contains`, `match_logic`, and `customer_environment: true`.
2. Add a matching row to `netbox_platform_collector_mapping.yml` with the same match fields and target `collector_type`.
3. Run collector dry_run and verify `hmdl.collector_target.extra` and `collector_diff_log.reason`.

---

## Audit locations (collector)

| Store | Field |
|-------|-------|
| `hmdl.collector_target.extra` | JSON: `platform_status`, `platform_status_note` |
| `hmdl.collector_diff_log.reason` | Suffix: `[platform_status: …]` on added/preserved rows |
| Email report | CSV column `platform_status` |

---

## Known gaps (Zabbix-only)

- Platform skip list (`izlenmeli=Hayır`) is emailed but not written to `hmdl.zabbix_sync_log` (devices are logged).
- `limit_per_dc` is enforced in legacy `process_platform.yml`, not in `parallel_compare_engine` Phase A.
