# Zabbix Migration Project

Bu proje, Netbox ve CSV kaynaklarından Zabbix'e host migration ve senkronizasyon işlemlerini otomatikleştirir.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Proje Yapısı](#proje-yapısı)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Dokümantasyon](#dokümantasyon)
- [Bileşenler](#bileşenler)

## Genel Bakış

Bu modül, iki ana senaryo için Zabbix host yönetimini otomatikleştirir:

1. **CSV'den Migration**: CSV dosyasından host'ları Zabbix'e aktarır
2. **Netbox Entegrasyonu**: Netbox'tan gelen cihaz bilgilerini Zabbix ile senkronize eder

### CSV Migration Özellikleri
- Host oluşturma ve güncelleme
- `DEVICE_TYPE` ve `TEMPLATE_TYPE`'a göre template uygulama
- `DC_ID`'ye göre proxy/proxy group atama
- Host-level macro yönetimi

### Netbox Entegrasyonu Özellikleri
- Netbox cihazlarını Zabbix'e otomatik senkronizasyon
- Lokasyon, IP ve hostname'in sürekli güncellenmesi
- Metadata tag'lerinin (rack, cluster, hall, vb.) yönetimi
- Email bildirimleri (başarısız işlemler için)
- Lokasyon bazlı filtreleme

## Proje Yapısı

```
zabbix-migration/
├── docs/                    # Tüm dokümantasyon
│   ├── guides/             # Kullanım kılavuzları
│   ├── analysis/           # Analiz dokümanları
│   ├── design/             # Tasarım dokümanları
│   ├── development/        # Geliştirme özetleri
│   ├── scripts/            # Script dokümanları
│   └── mappings/           # Mapping dokümanları
├── playbooks/              # Ansible playbook'ları
│   ├── netbox_to_zabbix.yaml
│   ├── zabbix_migration.yaml
│   └── roles/              # Ansible rolleri
├── scripts/                # Python scriptleri
├── mappings/               # Mapping YAML dosyaları
├── examples/               # Örnek CSV dosyaları
└── collections/            # Ansible collection gereksinimleri
```

## Hızlı Başlangıç

### Netbox'tan Zabbix'e Migration

```bash
ansible-playbook playbooks/netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['user@example.com']" \
  -e "netbox_location_filter=LocationName"
```

### CSV'den Migration

```bash
ansible-playbook playbooks/zabbix_migration.yaml \
  -e "csv_file=examples/hosts.csv" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

## Dokümantasyon

### Kılavuzlar (`docs/guides/`)
- **[Netbox to Zabbix Kılavuzu](docs/guides/NETBOX_TO_ZABBIX_README.md)**: Netbox entegrasyonu detaylı kullanım kılavuzu
- **[Email Bildirimleri](docs/guides/EMAIL_NOTIFICATION_GUIDE.md)**: Email bildirim sistemi konfigürasyonu
- **[AWX Kılavuzu](docs/guides/AWX_GUIDE.md)**: AWX/AAP ile kullanım

### Tasarım (`docs/design/`)
- **[Tasarım Dokümanı](docs/design/DESIGN.md)**: Sistem tasarımı ve idempotency kuralları
- **[Şema](docs/design/SCHEMA.md)**: Veri şeması ve yapıları
- **[Host Groups ve Tags](docs/design/HOST_GROUPS_AND_TAGS_IMPLEMENTATION.md)**: Tag ve grup yönetimi

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
- `playbooks/netbox_to_zabbix.yaml`: Netbox entegrasyonu ana playbook'u
- `playbooks/zabbix_migration.yaml`: CSV migration playbook'u

### Ansible Roles
- `playbooks/roles/netbox_to_zabbix/`: Netbox entegrasyonu rolü
- `playbooks/roles/zabbix_migration/`: Zabbix migration rolü

### Mapping Files
- `mappings/templates.yml`: Template mapping'leri
- `mappings/template_types.yml`: Template type tanımları
- `mappings/datacenters.yml`: Datacenter/proxy mapping'leri
- `mappings/netbox_device_type_mapping.yml`: Netbox device type filtreleme

### Scripts
- `scripts/netbox_discovery.py`: Netbox API keşif scripti
- `scripts/analyze_netbox_api.py`: Netbox API analiz scripti

### Examples
- `examples/hosts.csv`: Örnek CSV dosyası
- `examples/templates.csv`: Örnek template CSV dosyası


