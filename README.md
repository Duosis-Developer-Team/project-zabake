# HMDL - Host Metadata-Driven Lifecycle

Host Metadata-Driven Lifecycle (HMDL) projesi, Zabbix, Netbox (Loki) ve Datalake projelerinin konfigürasyon senkronizasyonu, envanter yönetimi ve izleme tanımlarının otomasyonunu sağlar.

## 📋 Proje Yapısı

Detaylı proje yapısı için: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

```
project-zabake/
├── zabbix-netbox/             # Zabbix-Netbox entegrasyonu modülü
│   ├── docs/                  # Dokümantasyon
│   ├── playbooks/             # Ansible playbook'ları
│   ├── scripts/               # Python scriptleri
│   ├── mappings/              # Mapping YAML dosyaları
│   └── examples/              # Örnek CSV dosyaları
├── legacy/                    # Eski workflow scriptleri (platform sync, datalake integration)
│   ├── scripts/               # Legacy Python scriptleri
│   └── playbooks/             # Legacy Ansible playbook'ları
└── _old/                      # Arşivlenmiş eski versiyonlar
```

## 🎯 Proje Amacı

HMDL projesi, aşağıdaki sistemler arasında otomatik senkronizasyon ve yönetim sağlar:

- **Zabbix**: İzleme ve alerting sistemi
- **Netbox (Loki)**: Envanter ve DCIM (Data Center Infrastructure Management) sistemi
- **Datalake**: Veri depolama ve analiz platformu

### Ana Özellikler

- ✅ **Konfigürasyon Senkronizasyonu**: Sistemler arası konfigürasyon senkronizasyonu
- ✅ **Envanter Yönetimi**: Otomatik envanter güncellemeleri ve senkronizasyonu
- ✅ **İzleme Tanımları**: İzleme kurallarının otomatik oluşturulması ve güncellenmesi
- ✅ **Metadata-Driven**: Host metadata'sına dayalı otomatik yaşam döngüsü yönetimi

## 🏗️ Mimari

### Orkestrasyon
- **Ansible AWX**: Ana orkestrasyon platformu
- **Playbooks**: İş akışlarını tanımlayan Ansible playbook'ları

### Arka Plan İşlemleri
- **Python**: Otomasyon scriptleri ve API entegrasyonları
- **Git**: CI/CD ve versiyon kontrolü
- **CI/CD Pipeline**: Otomatik test ve deployment

## 🚀 Hızlı Başlangıç

### Zabbix-Netbox Entegrasyonu

Ana entegrasyon modülü için detaylı dokümantasyon: [zabbix-netbox/README.md](zabbix-netbox/README.md)

**Netbox'tan Zabbix'e Senkronizasyon:**
```bash
cd zabbix-netbox
ansible-playbook playbooks/netbox_zabbix_sync.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

**CSV Import (Legacy):**
```bash
cd legacy
ansible-playbook playbooks/zabbix_csv_import.yaml \
  -e "csv_path=/path/to/hosts.csv" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Legacy Workflow

Eski platform synchronization ve datalake integration workflow'u için `legacy/` klasörüne bakın.

## 📚 Dokümantasyon

### Ana Modüller
- **[Zabbix-Netbox Entegrasyonu](zabbix-netbox/README.md)**: Zabbix ve Netbox arası senkronizasyon
- **[Zabbix-Netbox Docs](zabbix-netbox/docs/)**: Detaylı dokümantasyon klasörü
  - Guides: Kullanım kılavuzları
  - Design: Tasarım dokümanları
  - Analysis: Analiz dokümanları
  - Development: Geliştirme özetleri

### Legacy
- **[Legacy Workflow](legacy/README.md)**: Eski workflow dokümantasyonu

## 🔧 Gereksinimler

### Zabbix-Netbox Entegrasyonu
- Python 3.8+
- Ansible 2.9+
- Ansible Collections:
  - `community.general` (>=8.0.0)
  - `community.zabbix` (>=2.0.0)

Kurulum:
```bash
cd zabbix-netbox
ansible-galaxy collection install -r requirements.yml
pip install -r scripts/requirements.txt
```

### Legacy Workflow
- Python 3.8+
- Ansible 2.9+
- PostgreSQL (psycopg2)
- requests

## 📝 Modüller

### 1. Zabbix-Netbox Entegrasyonu
Zabbix ve Netbox (Loki) sistemleri arasında otomatik senkronizasyon ve envanter yönetimi.

**Konum:** `zabbix-netbox/`

**Özellikler:**
- Netbox cihazlarını Zabbix'e otomatik senkronizasyon
- Lokasyon, IP ve hostname'in sürekli güncellenmesi
- Metadata tag'lerinin (rack, cluster, hall, vb.) yönetimi
- Email bildirimleri (başarısız işlemler için)

### 2. Legacy Workflow
Eski platform synchronization, datalake integration ve CSV-based Zabbix host creation workflow'ları.

**Konum:** `legacy/`

**Özellikler:**
- Platform synchronization (Netbox API → PostgreSQL)
- Datalake integration
- CSV'den Zabbix'e host import (Legacy)

## 🔄 Geliştirme

1. Development branch'inde çalışın
2. Her feature için ayrı branch oluşturun
3. Feature tamamlandığında development'a merge edin
4. Development onaylandıktan sonra main'e merge edin
5. Her feature için unit test yazın
6. Testleri çalıştırın ve başarılıysa GitHub'a push edin

## 🏭 CI/CD

Proje, Python ve Git kullanılarak CI/CD pipeline'ı ile yönetilir:
- Otomatik testler
- Versiyon kontrolü
- Deployment otomasyonu

## 📞 Destek

Sorularınız için:
- Zabbix-Netbox Entegrasyonu: `zabbix-netbox/docs/` klasörüne bakın
- Legacy Workflow: `legacy/` klasörüne bakın

## 📄 Lisans

[Lisans bilgisi buraya eklenecek]
