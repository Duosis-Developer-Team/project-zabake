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

### Netbox'tan Zabbix'e Senkronizasyon

```bash
ansible-playbook playbooks/netbox_zabbix_sync.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['user@example.com']" \
  -e "location_filter=LocationName"
```


## Dokümantasyon

### Kılavuzlar (`docs/guides/`)
- **[Netbox to Zabbix Kılavuzu](docs/guides/NETBOX_TO_ZABBIX_README.md)**: Netbox entegrasyonu detaylı kullanım kılavuzu
- **[Template Macros Kılavuzu](docs/guides/TEMPLATE_MACROS_GUIDE.md)**: API-tabanlı template'ler için makro konfigürasyonu (yeni!)
- **[Email Bildirimleri](docs/guides/EMAIL_NOTIFICATION_GUIDE.md)**: Email bildirim sistemi konfigürasyonu
- **[AWX Kılavuzu](docs/guides/AWX_GUIDE.md)**: AWX/AAP ile kullanım

### Tasarım (`docs/design/`)
- **[Tasarım Dokümanı](docs/design/DESIGN.md)**: Sistem tasarımı ve idempotency kuralları
- **[Şema](docs/design/SCHEMA.md)**: Veri şeması ve yapıları
- **[Host Groups ve Tags](docs/design/HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md)**: Tag ve grup yönetimi
- **[Location hierarchy resolution](docs/design/LOCATION_HIERARCHY_RESOLUTION.md)**: NetBox `dcim/locations` kök çözümlemesi ve lokasyon filtresi (BFS); referans kod: [`scripts/netbox_location_hierarchy.py`](scripts/netbox_location_hierarchy.py)

### Analiz (`docs/analysis/`)
- **[Netbox API Endpoints](docs/analysis/NETBOX_API_ENDPOINTS_DECISION.md)**: API endpoint kararları
- **[Netbox-Zabbix Update Analizi](docs/analysis/NETBOX_ZABBIX_UPDATE_ANALYSIS.md)**: Update stratejisi analizi
- **[Playbook Analizi](docs/analysis/PLAYBOOK_ANALYSIS_AND_DEVELOPMENT_PLAN.md)**: Playbook geliştirme planı

### Geliştirme (`docs/development/`)
- **[Geliştirme Özeti](docs/development/DEVELOPMENT_SUMMARY.md)**: Proje geliştirme özeti

### Script Dokümanları (`docs/scripts/`)
- Netbox discovery ve analiz scriptleri için dokümantasyon

### Mapping Dokümanları (`docs/mappings/`)
- Mapping dosyaları için açıklamalar

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
- `mappings/netbox_device_type_mapping.yml`: Netbox device type filtreleme

### Scripts
- `scripts/netbox_discovery.py`: Netbox API keşif scripti
- `scripts/analyze_netbox_api.py`: Netbox API analiz scripti
- `scripts/debug_netbox_api.py`: Netbox API debug scripti

### Examples
- `examples/hosts.csv`: Örnek CSV dosyası (referans amaçlı)
- `examples/templates.csv`: Örnek template CSV dosyası (referans amaçlı)

**Not:** CSV import özelliği legacy klasöründe bulunmaktadır.
