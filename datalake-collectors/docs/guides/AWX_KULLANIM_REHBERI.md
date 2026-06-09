# AWX Kullanım Rehberi — Datalake Collector Sync

Playbook: `playbooks/datalake_collector_sync.yaml`  
Rol: `datalake_collector_sync`

## Job Template

| Alan | Değer |
|------|--------|
| **Inventory** | `localhost` içeren inventory |
| **Project SCM** | `project-zabake` → playbook yolu: `datalake-collectors/playbooks/datalake_collector_sync.yaml` |
| **Credentials** | PostgreSQL, NetBox token, Gitea vault token, SSH (proxy NiFi) |
| **Verbosity** | 1 (sorun giderme: 2) |

Proxy reconcile için **Machine Credential** (SSH) gerekir; `proxy_assignment.yml` içindeki `REPLACE_*` hostları gerçek Proxy NiFi adresleriyle değiştirin.

## Zorunlu değişkenler

| Değişken | Açıklama |
|----------|----------|
| `discovery_db_host` | HMDL PostgreSQL host |
| `discovery_db_port` | Port (varsayılan 5432) |
| `discovery_db_name` | Veritabanı adı |
| `discovery_db_user` | Kullanıcı |
| `discovery_db_password` | Şifre |
| `netbox_url` | NetBox base URL (`sync_platforms` veya `sync_devices` true iken) |
| `netbox_token` | NetBox API token |

## Gitea vault

| Değişken | Açıklama |
|----------|----------|
| `gitea_vault_url` | `datalake-collectors-vault` private repo URL |
| `gitea_vault_token` | Gitea read token |
| `gitea_vault_branch` | Varsayılan `main` |

## Senkronizasyon kapsamı

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `sync_platforms` | `true` | Phase 1 — NetBox platforms |
| `sync_devices` | `false` | Phase 2 — NetBox devices |
| `dry_run` | `true` | Diff hesapla, proxy'ye yazma |
| `run_basic_checks` | `true` | ICMP + TCP kontrol |
| `only_fetch` | `false` | Sadece fetch, reconcile yok |
| `location_filter` | `""` | Site/DC substring filtresi |
| `proxy_filter` | `""` | Örn. `DC13` (dc_code; tüm NiFi node'ları) |
| `collector_filter` | `""` | Örn. `VmWare,Nutanix` |
| `removal_guard_enabled` | `true` | NetBox'tan düşen IP silinmeden önce ICMP/TCP kontrol |
| `deploy_scripts` | `false` | Platform collector script'lerini NiFi'ye rsync |

## E-posta (ADR-0003)

| Değişken | Varsayılan |
|----------|------------|
| `mail_recipients` | `[]` |
| `mail_smtp_host` | `10.34.8.191` |
| `mail_smtp_port` | `587` |
| `mail_from` | `infrareport@alert.bulutistan.com` |

## Survey önerisi

1. **Dry Run** (bool, default: true) → `dry_run`
2. **Platform Sync** (bool, default: true) → `sync_platforms`
3. **Device Sync** (bool, default: false) → `sync_devices`
4. **Proxy Filter** (text) → `proxy_filter`
5. **Collector Filter** (text) → `collector_filter`
6. **Run Basic Checks** (bool) → `run_basic_checks`
7. **Email Recipients** (text, virgülle) → `mail_recipients`

## Örnek Extra Variables (pilot DC13)

```yaml
discovery_db_host: "postgresql.example.com"
discovery_db_port: 5432
discovery_db_name: "bulutlake"
discovery_db_user: "hmdl_writer"
discovery_db_password: "{{ vault_db_password }}"

netbox_url: "https://loki.bulutistan.com/"
netbox_token: "{{ vault_netbox_token }}"

gitea_vault_url: "https://gitea.example.local/org/datalake-collectors-vault.git"
gitea_vault_token: "{{ vault_gitea_token }}"

sync_platforms: true
sync_devices: false
dry_run: true
proxy_filter: "DC13"
run_basic_checks: true

mail_recipients:
  - "noc@example.com"
```

## Mapping dosya yolları (override)

| Değişken | Varsayılan |
|----------|------------|
| `collector_types_path` | `mappings/collector_types.yml` |
| `platform_collector_mapping_path` | `mappings/netbox_platform_collector_mapping.yml` |
| `device_collector_mapping_path` | `mappings/netbox_device_collector_mapping.yml` |
| `proxy_assignment_path` | `mappings/proxy_assignment.yml` |
| `target_conf_filename` | `configuration_file.json` |
