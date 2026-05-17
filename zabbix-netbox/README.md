# Zabbix-Netbox Entegrasyonu

Bu modül, HMDL (Host Metadata-Driven Lifecycle) projesinin bir parçasıdır ve Netbox (Loki) ile Zabbix arasında otomatik senkronizasyon ve envanter yönetimi sağlar.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Proje Yapısı](#proje-yapısı)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Dokümantasyon](#dokümantasyon)
- [Bileşenler](#bileşenler)

## Genel Bakış

Bu modül, Netbox (Loki) ile Zabbix arasında otomatik senkronizasyon sağlar:

### Netbox Sync Özellikleri
- Netbox cihazlarını Zabbix'e otomatik senkronizasyon
- Lokasyon, IP ve hostname'in sürekli güncellenmesi
- Metadata tag'lerinin (rack, cluster, hall, vb.) yönetimi
- **API-tabanlı template'ler için otomatik makro yönetimi** (yeni!)
  - Otomatik IP enjeksiyonu (`{HOST.IP}` değişkeni)
  - Birden fazla interface tipini destekleme (SNMP + API)
  - Template bazlı makro tanımlaması
- Email bildirimleri (başarısız işlemler için)
- Lokasyon bazlı filtreleme

## Proje Yapısı

```
zabbix-netbox/
├── docs/                    # Tüm dokümantasyon
│   ├── guides/             # Kullanım kılavuzları
│   ├── analysis/           # Analiz dokümanları
│   ├── design/             # Tasarım dokümanları
│   ├── development/        # Geliştirme özetleri
│   ├── scripts/            # Script dokümanları
│   └── mappings/           # Mapping dokümanları
├── playbooks/              # Ansible playbook'ları
│   ├── netbox_zabbix_sync.yaml
│   └── roles/              # Ansible rolleri
├── scripts/                # Python scriptleri
├── mappings/               # Mapping YAML dosyaları
├── examples/               # Örnek CSV dosyaları
└── requirements.yml        # Ansible collection gereksinimleri
```

## Hızlı Başlangıç

### AWX (önerilen)

Tüm job input’ları, Survey önerisi ve senaryolar: **[AWX Kullanım Rehberi](docs/guides/AWX_KULLANIM_REHBERI.md)**.

Veri akışı ve smart merge diyagramları: **[SYNC_DATA_FLOW](docs/design/SYNC_DATA_FLOW.md)**.

Minimum örnek (cihazlar discovery DB, platform Loki):

```yaml
discovery_db_host: "postgresql.example.com"
discovery_db_port: 5432
discovery_db_name: "bulutlake"
discovery_db_user: "zabbix_sync"
discovery_db_password: "<secret>"

zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "api_sync"
zabbix_password: "<secret>"

device_source: datalake
platform_source: loki
netbox_url: "https://loki.example.com"
netbox_token: "<token>"

sync_devices: true
hmdl_log_enabled: true
dry_run: true          # ilk çalıştırmada
device_limit: 10
```

### CLI (ansible-playbook)

```bash
ansible-playbook playbooks/netbox_zabbix_sync.yaml \
  -e "discovery_db_host=postgresql.example.com" \
  -e "discovery_db_name=bulutlake" \
  -e "discovery_db_user=zabbix_sync" \
  -e "discovery_db_password=SECRET" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=api_sync" \
  -e "zabbix_password=SECRET" \
  -e "device_source=datalake" \
  -e "dry_run=true" \
  -e "device_limit=10"
```

Loki-only (NetBox API) için ekleyin: `netbox_url`, `netbox_token`. Kaynak seçimi: `device_source`, `platform_source`, `virtual_fw_source` (`loki` | `datalake`).

## Dokümantasyon

Tam indeks: **[docs/guides/00-DOCUMENTATION_INDEX.md](docs/guides/00-DOCUMENTATION_INDEX.md)**

### Kılavuzlar (`docs/guides/`)
- **[AWX Kullanım Rehberi](docs/guides/AWX_KULLANIM_REHBERI.md)**: AWX Extra Variables, Survey, senaryolar, HMDL sorguları (TR)
- **[AWX Guide](docs/guides/AWX_GUIDE.md)**: AWX summary (EN)
- **[Netbox to Zabbix Kılavuzu](docs/guides/NETBOX_TO_ZABBIX_README.md)**: Netbox entegrasyonu detaylı kullanım kılavuzu
- **[Template Macros Kılavuzu](docs/guides/TEMPLATE_MACROS_GUIDE.md)**: API-tabanlı template'ler için makro konfigürasyonu
- **[Email Bildirimleri](docs/guides/EMAIL_NOTIFICATION_GUIDE.md)**: Email bildirim sistemi konfigürasyonu

### Tasarım (`docs/design/`)
- **[Sync data flow](docs/design/SYNC_DATA_FLOW.md)**: Envanter fetch, smart merge, proxy, HMDL (diyagramlar)
- **[Tasarım Dokümanı](docs/design/DESIGN.md)**: Legacy CSV migration tasarımı (tarihsel)
- **[Şema](docs/design/SCHEMA.md)**: Veri şeması ve yapıları
- **[Host Groups ve Tags](docs/design/HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md)**: Tag ve grup yönetimi
- **[Location hierarchy resolution](docs/design/LOCATION_HIERARCHY_RESOLUTION.md)**: NetBox `dcim/locations` kök çözümlemesi ve lokasyon filtresi (BFS)

### SQL (`SQL/zabbix-netbox/`)
- **[HMDL audit tables](../SQL/zabbix-netbox/README.md)**: DDL, migration, smart-merge kolonları

### Analiz (`docs/analysis/`)
- **[Netbox API Endpoints](docs/analysis/NETBOX_API_ENDPOINTS_DECISION.md)**: API endpoint kararları
- **[Netbox-Zabbix Update Analizi](docs/analysis/NETBOX_ZABBIX_UPDATE_ANALYSIS.md)**: Update stratejisi analizi
- **[Playbook Analizi](docs/analysis/PLAYBOOK_ANALYSIS_AND_DEVELOPMENT_PLAN.md)**: Playbook geliştirme planı

### Geliştirme (`docs/development/`)
- **[Geliştirme Özeti](docs/development/DEVELOPMENT_SUMMARY.md)**: Proje geliştirme özeti

### Script Dokümanları (`docs/scripts/`)
- Netbox discovery ve analiz scriptleri için dokümantasyon

### Mapping Dokümanları (`docs/mappings/`)
- **[Mapping dosyaları indeksi (İngilizce)](docs/mappings/README.md)**: `netbox_device_type_mapping.yml`, `netbox_platform_mapping.yml`, `templates.yml` akışı ve kurallar
- [NetBox device type mapping (Türkçe)](docs/mappings/README_NETBOX_DEVICE_TYPE_MAPPING.md)

## Bileşenler

### Ansible Playbooks
- `playbooks/netbox_zabbix_sync.yaml`: Netbox entegrasyonu ana playbook'u

### Ansible Roles
- `playbooks/roles/netbox_zabbix_sync/`: Netbox entegrasyonu rolü

**Not:** CSV import özelliği legacy olarak `legacy/playbooks/zabbix_csv_import.yaml` dosyasında bulunmaktadır.

### Mapping Files
- `mappings/templates.yml`: Template mapping'leri (makro desteği ile!)
- `mappings/template_types.yml`: Template type tanımları
- `mappings/datacenters.yml`: Datacenter/proxy mapping'leri
- `mappings/netbox_device_type_mapping.yml`: NetBox cihaz kaydından mantıksal `device_type` eşlemesi
- `mappings/netbox_platform_mapping.yml`: NetBox platform üreticisi → `device_type` ve DC başına limit
- `mappings/virtual_fw_mapping.yml`: NetBox custom-objects `virtual_fws` → `device_type` (AWX’te `sync_virtual_fws: true` ile)
- Özet ve çapraz linkler: [docs/mappings/README.md](docs/mappings/README.md)

### Scripts
- `scripts/netbox_discovery.py`: Netbox API keşif scripti
- `scripts/analyze_netbox_api.py`: Netbox API analiz scripti
- `scripts/debug_netbox_api.py`: Netbox API debug scripti

### Examples
- `examples/hosts.csv`: Örnek CSV dosyası (referans amaçlı)
- `examples/templates.csv`: Örnek template CSV dosyası (referans amaçlı)

**Not:** CSV import özelliği legacy klasöründe bulunmaktadır.
