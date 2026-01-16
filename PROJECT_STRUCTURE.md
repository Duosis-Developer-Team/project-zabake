# Project Structure

Bu doküman, HMDL (Host Metadata-Driven Lifecycle) projesinin dizin yapısını ve her klasörün amacını açıklar.

## 📁 Root Directory Structure

```
project-zabake/
├── README.md                    # Ana proje dokümantasyonu
├── .gitignore                   # Git ignore kuralları
├── PROJECT_STRUCTURE.md         # Bu dosya
│
├── zabbix-netbox/               # Zabbix-Netbox entegrasyonu modülü
│   ├── README.md                # Zabbix migration dokümantasyonu
│   ├── requirements.yml         # Ansible collection gereksinimleri
│   ├── CHANGES_SUMMARY.md       # Değişiklik özeti
│   ├── COLLECTION_INSTALL.md    # Collection kurulum kılavuzu
│   ├── NETBOX_TO_ZABBIX_DATA_MAPPING.md
│   ├── PERFORMANCE_ANALYSIS.md
│   │
│   ├── docs/                    # Dokümantasyon
│   │   ├── guides/              # Kullanım kılavuzları
│   │   ├── analysis/            # Analiz dokümanları
│   │   ├── design/              # Tasarım dokümanları
│   │   ├── development/         # Geliştirme özetleri
│   │   ├── scripts/             # Script dokümanları
│   │   └── mappings/            # Mapping dokümanları
│   │
│   ├── playbooks/               # Ansible playbook'ları
│   │   ├── ansible.cfg          # Ansible konfigürasyonu
│   │   ├── netbox_to_zabbix.yaml
│   │   ├── zabbix_migration.yaml
│   │   └── roles/               # Ansible rolleri
│   │       ├── netbox_to_zabbix/
│   │       └── zabbix_migration/
│   │
│   ├── scripts/                 # Python scriptleri
│   │   ├── requirements.txt     # Python gereksinimleri
│   │   ├── netbox_discovery.py
│   │   ├── analyze_netbox_api.py
│   │   ├── debug_netbox_api.py
│   │   ├── test_netbox_token.py
│   │   └── test_token_variations.py
│   │
│   ├── mappings/                # Mapping YAML dosyaları
│   │   ├── templates.yml
│   │   ├── template_types.yml
│   │   ├── datacenters.yml
│   │   └── netbox_device_type_mapping.yml
│   │
│   └── examples/                # Örnek dosyalar
│       ├── hosts.csv
│       └── templates.csv
│
├── legacy/                      # Eski workflow
│   ├── README.md                # Legacy dokümantasyonu
│   ├── scripts/                 # Legacy Python scriptleri
│   │   ├── check_new_platform.py
│   │   ├── engine.py
│   │   ├── datalake_integration.py
│   │   └── zabbix_integration.py
│   └── playbooks/               # Legacy Ansible playbook'ları
│       ├── check_new_platform.yaml
│       ├── engine.yaml
│       ├── datalake_integration.yaml
│       ├── zabbix_integration.yaml
│       ├── zabbix_csv_import.yaml  # CSV import (Legacy)
│       └── roles/                # Legacy Ansible rolleri
│           └── zabbix_csv_import/
│
└── _old/                        # Arşivlenmiş eski versiyonlar
    ├── init/
    └── vmware integration/
```

## 📂 Klasör Açıklamaları

### Root Level

- **README.md**: Proje genel bakışı ve hızlı başlangıç kılavuzu
- **.gitignore**: Git ignore kuralları (Python, Ansible, IDE, credentials)
- **PROJECT_STRUCTURE.md**: Bu doküman

### zabbix-netbox/ (Zabbix-Netbox Entegrasyonu)

Zabbix ve Netbox (Loki) sistemleri arasında otomatik senkronizasyon ve envanter yönetimi modülü.

- **docs/**: Kapsamlı dokümantasyon
  - `guides/`: Kullanım kılavuzları (AWX, Email, Netbox to Zabbix)
  - `analysis/`: API endpoint kararları, update analizleri
  - `design/`: Sistem tasarımı, şema, host groups ve tags
  - `development/`: Geliştirme özetleri
  - `scripts/`: Script dokümanları
  - `mappings/`: Mapping dokümanları

- **playbooks/**: Ansible playbook'ları ve rolleri
  - `netbox_zabbix_sync.yaml`: Netbox entegrasyonu ana playbook'u
  - `roles/`: Ansible rolleri (netbox_zabbix_sync)
  - **Not:** CSV import özelliği legacy klasörüne taşınmıştır

- **scripts/**: Python scriptleri
  - Netbox discovery ve analiz scriptleri
  - Debug ve test scriptleri

- **mappings/**: YAML mapping dosyaları
  - Template, template type, datacenter ve device type mapping'leri

- **examples/**: Örnek CSV dosyaları

### legacy/

Eski platform synchronization ve datalake integration workflow'u.

- **scripts/**: Legacy Python scriptleri
  - Platform synchronization (Netbox API → PostgreSQL)
  - Datalake integration
  - Zabbix host creation

- **playbooks/**: Legacy Ansible playbook'ları
  - Platform synchronization playbook'ları
  - CSV-based Zabbix host import (Legacy)
  - AWX/Ansible Tower üzerinden çalıştırılmak üzere tasarlanmış

### _old/

Arşivlenmiş eski versiyonlar. Referans amaçlı saklanmaktadır.

## 🔄 Proje Geliştirme Akışı

1. **Development Branch**: Ana geliştirme branch'i
2. **Feature Branches**: Her feature için ayrı branch
3. **Main Branch**: Production-ready kod

## 📝 Notlar

- Yeni geliştirmeler için `zabbix-netbox/` kullanılmalıdır
- `legacy/` klasörü artık aktif olarak geliştirilmemektedir
- `_old/` klasörü sadece referans amaçlıdır
- Proje HMDL (Host Metadata-Driven Lifecycle) kapsamında geliştirilmektedir

