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
├── zabbix-monitoring/           # Zabbix Monitoring Integration modülü
│   ├── README.md                # Ana dokümantasyon
│   ├── requirements.yml         # Ansible collection gereksinimleri
│   ├── CHANGES_SUMMARY.md       # Değişiklik özeti
│   │
│   ├── docs/                    # Dokümantasyon
│   │   ├── guides/              # Kullanım kılavuzları
│   │   │   ├── AWX_SETUP.md
│   │   │   ├── DATABASE_CONNECTION.md
│   │   │   └── USAGE.md
│   │   ├── analysis/            # Analiz dokümanları
│   │   │   ├── CONNECTIVITY_ITEMS.md
│   │   │   └── TEMPLATE_ANALYSIS.md
│   │   ├── design/              # Tasarım dokümanları
│   │   │   ├── ARCHITECTURE.md
│   │   │   ├── DATA_FLOW.md
│   │   │   └── SCHEMA.md
│   │   ├── development/         # Geliştirme dokümanları
│   │   │   ├── DEVELOPMENT_PLAN.md
│   │   │   └── TASK_BREAKDOWN.md
│   │   └── scripts/             # Script dokümanları
│   │       └── API_REFERENCE.md
│   │
│   ├── playbooks/               # Ansible playbook'ları
│   │   ├── ansible.cfg          # Ansible konfigürasyonu
│   │   ├── zabbix_monitoring_check.yaml
│   │   └── roles/               # Ansible rolleri
│   │       └── zabbix_monitoring/
│   │           ├── defaults/
│   │           ├── tasks/
│   │           ├── library/
│   │           └── templates/
│   │
│   ├── scripts/                 # Python scriptleri
│   │   ├── requirements.txt     # Python gereksinimleri
│   │   ├── config/              # Konfigürasyon modülleri
│   │   ├── collectors/          # Veri toplayıcılar
│   │   │   ├── api_collector.py
│   │   │   └── db_collector.py
│   │   ├── analyzers/          # Analiz modülleri
│   │   │   ├── template_analyzer.py
│   │   │   ├── connectivity_analyzer.py
│   │   │   └── data_analyzer.py
│   │   ├── utils/              # Yardımcı modüller
│   │   │   ├── logger.py
│   │   │   └── validators.py
│   │   ├── reports/            # Rapor modülleri
│   │   │   ├── report_generator.py
│   │   │   └── formatters.py
│   │   └── main.py             # Ana entry point
│   │
│   ├── config/                 # Konfigürasyon dosyaları
│   │   ├── zabbix_api_config.yml
│   │   ├── db_config.yml
│   │   └── monitoring_config.yml
│   │
│   ├── tests/                  # Unit testler
│   │   ├── test_collectors/
│   │   ├── test_analyzers/
│   │   ├── test_utils/
│   │   └── fixtures/
│   │
│   └── examples/                # Örnek dosyalar
│       ├── sample_config.yml
│       └── sample_report.json
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

### zabbix-monitoring/ (Zabbix Monitoring Integration)

Zabbix host'larındaki connectivity item'larının veri durumunu analiz ederek, host'lardan veri çekilip çekilemediğini tespit eden modül.

- **docs/**: Kapsamlı dokümantasyon
  - `guides/`: Kullanım kılavuzları (AWX, Database, Usage)
  - `analysis/`: Connectivity item ve template analizleri
  - `design/`: Mimari tasarım, veri akışı, şema
  - `development/`: Geliştirme planı ve görev dağılımı
  - `scripts/`: Script dokümanları

- **playbooks/**: Ansible playbook'ları ve rolleri
  - `zabbix_monitoring_check.yaml`: Ana monitoring playbook'u
  - `roles/`: Ansible rolleri (zabbix_monitoring)
  - Kubernetes üzerinde AWX ile çalıştırılmak üzere tasarlanmış

- **scripts/**: Python scriptleri
  - `collectors/`: Zabbix API ve DB veri toplayıcılar
  - `analyzers/`: Template, connectivity ve veri analiz modülleri
  - `reports/`: Rapor oluşturucu ve formatlayıcılar
  - `utils/`: Logging ve validation yardımcı modülleri

- **config/**: Konfigürasyon dosyaları
  - Zabbix API, database ve monitoring ayarları

- **tests/**: Unit testler
  - Collector, analyzer ve utility testleri

- **examples/**: Örnek konfigürasyon ve rapor dosyaları

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

- Yeni geliştirmeler için `zabbix-netbox/` ve `zabbix-monitoring/` kullanılmalıdır
- `zabbix-monitoring/` modülü Zabbix connectivity monitoring için kullanılır
- `legacy/` klasörü artık aktif olarak geliştirilmemektedir
- `_old/` klasörü sadece referans amaçlıdır
- Proje HMDL (Host Metadata-Driven Lifecycle) kapsamında geliştirilmektedir

