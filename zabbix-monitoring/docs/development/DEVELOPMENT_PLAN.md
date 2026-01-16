# Zabbix Monitoring Integration - Development Plan

## 📋 Proje Genel Bakış

Bu alt-proje, Zabbix'te bulunan hostların template'lerine göre belirlenen connectivity item'larının veri durumunu analiz ederek, host'lardan veri çekilip çekilemediğini tespit eder.

### Amaç
- Zabbix host'larındaki template'lere göre connectivity item'larını belirleme
- Bu item'ların veri durumunu analiz etme
- Host'lardan veri çekilip çekilemediğini tespit etme
- Zabbix API veya passive database'den veri alma
- Python ile karşılaştırma ve analiz yapma

### Teknik Gereksinimler
- **Orkestrasyon**: Kubernetes üzerinde Ansible AWX
- **Veri Kaynağı**: 
  - Başlangıç: Zabbix API
  - Production: Zabbix passive database (cluster'dan)
- **İşleme**: Python ile veri analizi ve karşılaştırma
- **Performans**: Zabbix'te ekstra yük oluşturmamak için veri bir kez alınıp işlenecek

## 🏗️ Mimari Tasarım

### Veri Akışı
```
Zabbix API/DB → Data Collection → Python Analysis → Results/Reports
```

### Bileşenler
1. **Data Collector**: Zabbix API veya DB'den veri çekme
2. **Template Analyzer**: Template'lerden connectivity item'larını belirleme
3. **Data Analyzer**: Item verilerini analiz etme ve karşılaştırma
4. **Report Generator**: Sonuçları raporlama
5. **Orchestrator**: AWX playbook'ları ile orkestrasyon

## 📁 Dosya Yapısı

```
zabbix-monitoring/
├── README.md                          # Ana dokümantasyon
├── requirements.yml                   # Ansible collection gereksinimleri
├── CHANGES_SUMMARY.md                 # Değişiklik özeti
│
├── docs/                              # Dokümantasyon
│   ├── guides/                        # Kullanım kılavuzları
│   │   ├── AWX_SETUP.md              # AWX kurulum ve konfigürasyon
│   │   ├── DATABASE_CONNECTION.md    # Passive DB bağlantı kılavuzu
│   │   └── USAGE.md                  # Kullanım kılavuzu
│   ├── analysis/                      # Analiz dokümanları
│   │   ├── CONNECTIVITY_ITEMS.md     # Connectivity item analizi
│   │   └── TEMPLATE_ANALYSIS.md      # Template analiz dokümanı
│   ├── design/                        # Tasarım dokümanları
│   │   ├── ARCHITECTURE.md           # Mimari tasarım
│   │   ├── DATA_FLOW.md              # Veri akış diyagramları
│   │   └── SCHEMA.md                 # Veri şeması
│   ├── development/                   # Geliştirme dokümanları
│   │   ├── DEVELOPMENT_PLAN.md       # Bu dosya
│   │   └── TASK_BREAKDOWN.md        # Görev dağılımı
│   └── scripts/                       # Script dokümanları
│       └── API_REFERENCE.md          # Zabbix API referansı
│
├── playbooks/                         # Ansible playbook'ları
│   ├── ansible.cfg                    # Ansible konfigürasyonu
│   ├── zabbix_monitoring_check.yaml  # Ana monitoring playbook'u
│   └── roles/                         # Ansible rolleri
│       └── zabbix_monitoring/
│           ├── defaults/
│           │   └── main.yml          # Varsayılan değişkenler
│           ├── tasks/
│           │   ├── main.yml          # Ana task dosyası
│           │   ├── collect_data.yml  # Veri toplama task'ları
│           │   ├── analyze_data.yml # Veri analiz task'ları
│           │   └── generate_report.yml # Rapor oluşturma task'ları
│           ├── library/
│           │   └── zabbix_helpers.py # Zabbix helper fonksiyonları
│           └── templates/
│               └── report.j2        # Rapor template'i
│
├── scripts/                           # Python scriptleri
│   ├── requirements.txt               # Python gereksinimleri
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # Konfigürasyon ayarları
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── api_collector.py          # Zabbix API veri toplayıcı
│   │   └── db_collector.py           # Zabbix DB veri toplayıcı
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── template_analyzer.py      # Template analiz modülü
│   │   ├── connectivity_analyzer.py  # Connectivity item analiz modülü
│   │   └── data_analyzer.py          # Veri analiz modülü
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                 # Logging utility
│   │   └── validators.py             # Veri doğrulama utility
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── report_generator.py       # Rapor oluşturucu
│   │   └── formatters.py            # Rapor formatlayıcılar
│   └── main.py                       # Ana entry point
│
├── config/                            # Konfigürasyon dosyaları
│   ├── zabbix_api_config.yml         # Zabbix API konfigürasyonu
│   ├── db_config.yml                 # Database konfigürasyonu
│   └── monitoring_config.yml         # Monitoring konfigürasyonu
│
├── tests/                             # Unit testler
│   ├── __init__.py
│   ├── test_collectors/
│   │   ├── __init__.py
│   │   ├── test_api_collector.py
│   │   └── test_db_collector.py
│   ├── test_analyzers/
│   │   ├── __init__.py
│   │   ├── test_template_analyzer.py
│   │   ├── test_connectivity_analyzer.py
│   │   └── test_data_analyzer.py
│   ├── test_utils/
│   │   ├── __init__.py
│   │   └── test_validators.py
│   └── fixtures/                      # Test fixture'ları
│       └── sample_data.json
│
└── examples/                          # Örnek dosyalar
    ├── sample_config.yml              # Örnek konfigürasyon
    └── sample_report.json             # Örnek rapor çıktısı
```

## 🎯 Geliştirme Aşamaları

### Faz 1: Temel Altyapı ve Planlama (1-2 gün)
- [x] Proje yapısı oluşturma
- [ ] Geliştirme planı dokümantasyonu
- [ ] Mimari tasarım dokümantasyonu
- [ ] Veri şeması tasarımı
- [ ] Konfigürasyon yapısı tasarımı

### Faz 2: Zabbix API Entegrasyonu (2-3 gün)
- [ ] Zabbix API client modülü
- [ ] Host ve template verilerini çekme
- [ ] Item verilerini çekme
- [ ] API authentication ve error handling
- [ ] Unit testler

### Faz 3: Template ve Connectivity Item Analizi (2-3 gün)
- [ ] Template'lerden connectivity item'larını belirleme
- [ ] Item tipi ve key pattern analizi
- [ ] Template hiyerarşisi analizi
- [ ] Connectivity item filtreleme mantığı
- [ ] Unit testler

### Faz 4: Veri Analiz Modülü (2-3 gün)
- [ ] Item veri durumu analizi
- [ ] Veri çekilme durumu tespiti
- [ ] Karşılaştırma algoritması
- [ ] Sonuç hesaplama ve skorlama
- [ ] Unit testler

### Faz 5: Raporlama Modülü (1-2 gün)
- [ ] Rapor formatları (JSON, HTML, CSV)
- [ ] Rapor oluşturucu
- [ ] Rapor template'leri
- [ ] Unit testler

### Faz 6: Ansible AWX Entegrasyonu (2-3 gün)
- [ ] Ansible playbook'ları
- [ ] Ansible rolleri
- [ ] AWX job template konfigürasyonu
- [ ] Error handling ve notification
- [ ] Integration testler

### Faz 7: Database Entegrasyonu (2-3 gün)
- [ ] Passive database bağlantı modülü
- [ ] SQL sorguları optimizasyonu
- [ ] Database connection pooling
- [ ] API'den DB'ye geçiş mekanizması
- [ ] Unit testler

### Faz 8: Optimizasyon ve İyileştirmeler (1-2 gün)
- [ ] Performans optimizasyonu
- [ ] Hata yönetimi iyileştirmeleri
- [ ] Logging ve monitoring
- [ ] Dokümantasyon tamamlama

### Faz 9: Test ve Deployment (2-3 gün)
- [ ] End-to-end testler
- [ ] AWX üzerinde test
- [ ] Production hazırlık
- [ ] Deployment dokümantasyonu

## 📝 Görev Detayları

### Faz 1: Temel Altyapı
**Süre**: 1-2 gün

**Görevler**:
1. Proje klasör yapısını oluştur
2. README.md dosyasını hazırla
3. Mimari tasarım dokümanını oluştur
4. Veri şeması tasarımını yap
5. Konfigürasyon yapısını tasarla

**Çıktılar**:
- Proje klasör yapısı
- Mimari dokümantasyon
- Veri şeması
- Konfigürasyon şablonları

### Faz 2: Zabbix API Entegrasyonu
**Süre**: 2-3 gün

**Görevler**:
1. Zabbix API client sınıfı oluştur
2. Authentication mekanizması
3. Host listesi çekme
4. Template listesi çekme
5. Item listesi çekme
6. Item history/trend verilerini çekme
7. Error handling ve retry mekanizması
8. Unit testler yaz

**Çıktılar**:
- `api_collector.py` modülü
- API helper fonksiyonları
- Unit testler
- API dokümantasyonu

### Faz 3: Template ve Connectivity Item Analizi
**Süre**: 2-3 gün

**Görevler**:
1. Template yapısını analiz et
2. Connectivity item pattern'lerini belirle
3. Item key pattern matching
4. Template inheritance analizi
5. Connectivity item filtreleme mantığı
6. Unit testler yaz

**Çıktılar**:
- `template_analyzer.py` modülü
- `connectivity_analyzer.py` modülü
- Connectivity item pattern tanımları
- Unit testler

### Faz 4: Veri Analiz Modülü
**Süre**: 2-3 gün

**Görevler**:
1. Item veri durumu analizi
2. Son veri zamanı kontrolü
3. Veri çekilme durumu tespiti
4. Karşılaştırma algoritması
5. Host bazlı skorlama
6. Unit testler yaz

**Çıktılar**:
- `data_analyzer.py` modülü
- Analiz algoritmaları
- Unit testler

### Faz 5: Raporlama Modülü
**Süre**: 1-2 gün

**Görevler**:
1. JSON format rapor
2. HTML format rapor
3. CSV format rapor
4. Rapor template'leri
5. Unit testler yaz

**Çıktılar**:
- `report_generator.py` modülü
- `formatters.py` modülü
- Rapor template'leri
- Unit testler

### Faz 6: Ansible AWX Entegrasyonu
**Süre**: 2-3 gün

**Görevler**:
1. Ana playbook oluştur
2. Ansible rolleri tasarla
3. Task'ları organize et
4. AWX job template hazırla
5. Error handling
6. Notification mekanizması
7. Integration testler

**Çıktılar**:
- `zabbix_monitoring_check.yaml` playbook
- Ansible rolleri
- AWX konfigürasyon dokümantasyonu
- Integration testler

### Faz 7: Database Entegrasyonu
**Süre**: 2-3 gün

**Görevler**:
1. Database connection modülü
2. SQL sorguları yaz
3. Query optimizasyonu
4. Connection pooling
5. API/DB geçiş mekanizması
6. Unit testler yaz

**Çıktılar**:
- `db_collector.py` modülü
- SQL sorguları
- Database dokümantasyonu
- Unit testler

### Faz 8: Optimizasyon ve İyileştirmeler
**Süre**: 1-2 gün

**Görevler**:
1. Performans analizi
2. Kod optimizasyonu
3. Hata yönetimi iyileştirmeleri
4. Logging mekanizması
5. Monitoring entegrasyonu
6. Dokümantasyon güncellemeleri

**Çıktılar**:
- Optimize edilmiş kod
- İyileştirilmiş error handling
- Logging sistemi
- Güncellenmiş dokümantasyon

### Faz 9: Test ve Deployment
**Süre**: 2-3 gün

**Görevler**:
1. End-to-end testler
2. AWX üzerinde test
3. Production environment hazırlık
4. Deployment kılavuzu
5. Operasyonel dokümantasyon

**Çıktılar**:
- Test sonuçları
- Deployment dokümantasyonu
- Operasyonel kılavuz
- Production-ready kod

## 🔧 Teknik Detaylar

### Connectivity Item Tanımları
Connectivity item'ları şu kriterlere göre belirlenir:
- Item key pattern'leri (örn: `icmpping`, `icmppingsec`, `net.tcp.service`)
- Item tipi (Zabbix agent, SNMP, etc.)
- Template içindeki konum
- Item isim pattern'leri

### Veri Analiz Kriterleri
- Son veri zamanı kontrolü
- Veri boşlukları tespiti
- Veri kalitesi analizi
- Host bazlı connectivity durumu

### Performans Gereksinimleri
- Zabbix API'ye minimum yük
- Büyük veri setleri için optimize edilmiş sorgular
- Paralel işleme desteği
- Caching mekanizması

## 📊 Başarı Kriterleri

1. ✅ Tüm connectivity item'ları doğru şekilde tespit edilmeli
2. ✅ Veri durumu analizi doğru sonuçlar vermeli
3. ✅ Zabbix'te ekstra yük oluşturmamalı
4. ✅ AWX üzerinden sorunsuz çalışmalı
5. ✅ Production database'den veri çekebilmeli
6. ✅ Raporlar anlaşılır ve kullanışlı olmalı
7. ✅ Tüm unit testler geçmeli
8. ✅ Dokümantasyon tam ve güncel olmalı

## 🚀 Sonraki Adımlar

1. Proje yapısını oluştur
2. Faz 1 görevlerini tamamla
3. Geliştirme branch'i oluştur
4. İlk feature branch'i oluştur ve Faz 2'ye başla

