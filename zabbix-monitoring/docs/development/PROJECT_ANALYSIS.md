# Zabbix Monitoring Integration - Proje Analizi

**Analiz Tarihi:** 2025  
**Genel İlerleme:** ~%75

---

## 1. Proje Özeti

### 1.1 Amaç
Bu modül, **HMDL (Host Metadata-Driven Lifecycle)** projesinin bir parçasıdır. Zabbix host'larındaki **connectivity item**'larının veri durumunu analiz ederek, host'lardan veri çekilip çekilemediğini tespit eder.

### 1.2 Teknik Yığın
| Bileşen | Teknoloji |
|---------|-----------|
| Orkestrasyon | Ansible AWX (Kubernetes) |
| Veri kaynağı (dev) | Zabbix API |
| Veri kaynağı (prod, planlanan) | Zabbix passive DB (PostgreSQL) |
| İşleme | Python 3.8+ |
| Konfigürasyon | YAML (mappings, defaults) |

### 1.3 Desteklenen Template'ler (mappings/templates.yml)
- **BLT - Lenovo ICT XCC Monitoring** (snmp.availability, icmpping)
- **BLT - Inspur M6 Template** (snmp.availability, icmpping)
- **BLT - Server Inspur BMC All Items 4 Zabbix SNMP** (snmp.availability)
- **BLT - HPE ProLiant DL380 SNMP** (snmp.availability)
- **BLT - Dell iDRAC SNMP** (snmp.availability, icmpping, data.check, discovery)
- **BLT- Supermicro ILO by Redfish API** (master: redfish.get.metrics)

---

## 2. Proje Yapısı (Güncel)

```
zabbix-monitoring/
├── docs/
│   ├── design/          # ARCHITECTURE, DATA_FLOW, SCHEMA
│   ├── development/     # CURRENT_STATUS, DEVELOPMENT_PLAN, TASK_BREAKDOWN
│   └── guides/          # AWX_TESTING, EMAIL_NOTIFICATION_GUIDE, MANUAL_TESTING,
│                        # TEMPLATE_CONFIGURATION, USAGE
├── playbooks/
│   ├── ansible.cfg
│   ├── zabbix_monitoring_check.yaml   # Ana playbook
│   └── roles/zabbix_monitoring/
│       ├── defaults/main.yml
│       └── tasks/
│           ├── main.yml
│           ├── validate_config.yml
│           ├── collect_data.yml
│           ├── analyze_templates.yml
│           ├── detect_connectivity.yml
│           ├── analyze_data.yml
│           ├── check_master_items.yml
│           ├── generate_report.yml
│           └── send_notification_email.yml
├── scripts/
│   ├── main.py
│   ├── test_manual.py
│   ├── test_with_mock_data.py
│   ├── config/          # settings.py, template_loader.py
│   ├── collectors/      # api_collector.py
│   ├── analyzers/       # template_analyzer, connectivity_analyzer, data_analyzer
│   └── utils/           # logger.py
├── mappings/
│   └── templates.yml
├── tests/               # Sadece __init__.py; pytest testleri YOK
├── examples/
└── requirements.yml, scripts/requirements.txt
```

**Not:** README'de geçen `config/` (zabbix_api_config.yml, db_config.yml, monitoring_config.yml) proje ağacında **yok**. Konfigürasyon `defaults/main.yml`, `mappings/templates.yml` ve playbook/ortam değişkenleri ile yönetiliyor.

---

## 3. Veri Akışı

```
Playbook (AWX)
    │
    ├─► validate_config
    ├─► collect_data (main.py --mode collect)     → hosts.json, templates.json, items.json, history.json
    ├─► analyze_templates (main.py --mode analyze-templates)
    ├─► detect_connectivity (main.py --mode detect-connectivity) → connectivity_items.json, master_items.json
    ├─► analyze_data (main.py --mode analyze-data)              → analysis_results.json
    ├─► check_master_items (main.py --mode check-master-items)   → master_items_check.json
    ├─► generate_report (sadece analysis_results varlık kontrolü + özet; rapor dosyası üretilmiyor)
    └─► send_notification_email (analysis_results.json → HTML/plain + SMTP)
```

Raporlama **sadece e-posta** ile yapılıyor; JSON/HTML/CSV dosya çıktısı üretilmiyor.

---

## 4. Faz Bazlı Durum

| Faz | Açıklama | Durum | Not |
|-----|-----------|-------|-----|
| **1** | Temel altyapı | ✅ %100 | Proje yapısı, docs, config (settings, template_loader), logger |
| **2** | Zabbix API entegrasyonu | ✅ %100 | api_collector: hosts, templates, items, history; batch, retry |
| **3** | Template & connectivity analizi | ✅ %100 | template_analyzer, connectivity_analyzer, YAML template loader |
| **4** | Veri analizi | ✅ %100 | data_analyzer: connectivity score, master item, issue tespiti |
| **5** | Raporlama | ⚠️ ~%30 | Email (HTML+text) ✅; report_generator, JSON/HTML/CSV formatter ❌ |
| **6** | Ansible AWX entegrasyonu | ✅ %100 | Playbook, role, 9 task (step-by-step, rescue, debug) |
| **7** | Database entegrasyonu | ❌ %0 | db_collector yok; main.py'de database için TODO |
| **8–9** | Test & optimizasyon | ❌ %0 | Unit/integration test yok; manuel test scriptleri **mevcut** (aşağıda) |

---

## 5. Detaylı Bileşen Durumu

### 5.1 Python Modülleri

| Modül | Durum | Açıklama |
|-------|-------|----------|
| `config.settings` | ✅ | get_settings, Zabbix/DB ayarları |
| `config.template_loader` | ✅ | TemplateConfigLoader, YAML template okuma |
| `collectors.api_collector` | ✅ | Zabbix API: auth, hosts, templates, items, history, save_collected_data |
| `collectors.db_collector` | ❌ | Yok |
| `analyzers.template_analyzer` | ✅ | analyze_templates, save_analysis |
| `analyzers.connectivity_analyzer` | ✅ | detect_connectivity_items, detect_master_items, save |
| `analyzers.data_analyzer` | ✅ | analyze_connectivity, analyze_master_items, save |
| `utils.logger` | ✅ | setup_logging, get_logger |
| `main.py` | ⚠️ | collect, analyze-templates, detect-connectivity, analyze-data, check-master-items ✅; **generate-report** sadece TODO, 0 döndürüyor |

### 5.2 Ansible Görevleri

| Task | İşlev | Durum |
|------|--------|-------|
| `validate_config` | Zabbix URL/user/pass vb. kontrol | ✅ |
| `collect_data` | main.py --mode collect (api/database) | ⚠️ database seçilirse main.py TODO yüzünden fail |
| `analyze_templates` | main.py --mode analyze-templates | ✅ |
| `detect_connectivity` | main.py --mode detect-connectivity | ✅ |
| `analyze_data` | main.py --mode analyze-data | ✅ |
| `check_master_items` | main.py --mode check-master-items | ✅ |
| `generate_report` | analysis_results.json varlığı + özet; dosya raporu yok | ✅ (tasarım: sadece email) |
| `send_notification_email` | analysis_results → HTML/text + SMTP | ✅ |

### 5.3 Raporlama ve Email
- **generate_report.yml:** `analysis_results.json` ve `master_items_check.json` varlığını kontrol eder; "Reports are sent via email only" notu var. Ek dosya (JSON/HTML/CSV) yazılmıyor.
- **send_notification_email.yml:** `analysis_results.json` → özet istatistikler, sorunlu host tablosu, HTML + plain text, Python SMTP ile gönderim. `mail_recipients` tanımlı ve dolu ise çalışır.

---

## 6. Test Durumu

### 6.1 CURRENT_STATUS ile Fark
- **CURRENT_STATUS.md:** "Manuel test scriptleri yok" yazıyor → **Güncel değil.**
- **scripts/test_manual.py** mevcut ve kullanılabilir.

### 6.2 test_manual.py
- **Testler:** `api-connection`, `template-loader`, `data-collection`, `connectivity-detection`, `data-analysis`, `full-workflow`
- **Kullanım:**  
  `python3 scripts/test_manual.py --test <test-adı> [--zabbix-url ... --zabbix-user ... --zabbix-password ...]`

### 6.3 tests/ (pytest)
- `tests/test_analyzers/`, `tests/test_collectors/`, `tests/test_utils/` sadece `__init__.py` içeriyor.
- **Gerçek unit/integration test dosyası yok.**  
- `scripts/requirements.txt` içinde pytest, pytest-cov, pytest-mock tanımlı; test kodu yazılmamış.

### 6.4 test_with_mock_data.py
- Mock veri ile test için ayrı script; varlığı test altyapısının kısmen hazır olduğunu gösterir.

---

## 7. Eksik ve Tutarsızlıklar

### 7.1 Eksikler
1. **Database collector:** `db_collector.py` yok; `main.py` ve `collect_data.yml` database modunu desteklemiyor (TODO/fail).
2. **Report generator (Python):** `main.py` içinde `generate_report` sadece TODO. Ayrıca `reports/report_generator.py` ve `formatters.py` (JSON/HTML/CSV) yok. Tasarım "sadece email" ise `generate_report`'un anlamı sınırlı; yine de dokümantasyonla uyum için sadeleştirilebilir veya ileride dosya çıktısı eklenebilir.
3. **Unit/entegrasyon testleri:** `tests/` altında sadece `__init__.py`; pytest senaryoları yok.
4. **config/ klasörü:** README'de `config/` ve `zabbix_api_config.yml`, `db_config.yml`, `monitoring_config.yml` anlatılıyor; projede bu dosyalar/klasör yok.

### 7.2 Dokümantasyon Tutarsızlıkları
- README'de referans verilen ancak projede **olmayan** dokümanlar:
  - `docs/guides/AWX_SETUP.md`
  - `docs/guides/DATABASE_CONNECTION.md`
  - `docs/analysis/CONNECTIVITY_ITEMS.md`
  - `docs/analysis/TEMPLATE_ANALYSIS.md`
- `docs/guides/AWX_TESTING.md` mevcut; AWX_SETUP ayrı bir kılavuz olarak yok.

### 7.3 Küçük Noktalar
- **main.py:** `generate_report` şu an anlamsız (hemen 0 dönüyor). Ya kaldırılmalı ya da "sadece email" tasarımına uygun minimal bir işlev (ör. özet log) verilmeli.
- **collect_data.yml:** `monitoring_data_source == "database"` iken main.py database'i desteklemediği için playbook hata verir. Database implemente edilene kadar bu blok devre dışı bırakılabilir veya fail mesajı netleştirilebilir.

---

## 8. Bağımlılıklar

### 8.1 Ansible (requirements.yml)
- `community.general` (>=8.0.0)
- `community.zabbix` (>=2.0.0)

### 8.2 Python (scripts/requirements.txt)
- `requests`, `urllib3`, `pyyaml`, `python-dotenv`
- `psycopg2-binary` (DB için; db_collector olmadığı için henüz kullanılmıyor)
- `pandas`, `numpy`
- `loguru`
- `pytest`, `pytest-cov`, `pytest-mock`
- `black`, `flake8`, `mypy`

---

## 9. Önerilen Sonraki Adımlar

### Öncelik 1
1. **CURRENT_STATUS.md güncellemesi:** "Manuel test scriptleri yok" → "test_manual.py mevcut" olarak düzeltmek.
2. **Unit testler:** `tests/` altında en azından `api_collector`, `template_analyzer`, `connectivity_analyzer`, `data_analyzer` için temel pytest testleri yazmak.
3. **main.py generate_report:** Tasarım "sadece email" ise TODO kaldırıp, `generate_report`'u "analysis_results varlığını doğrulama" veya "özet log" gibi minimal bir işleve indirgemek veya `generate_report.yml` ile uyumlu açık bir not bırakmak.

### Öncelik 2
4. **README ve dokümanlar:**  
   - `config/` ve `zabbix_api_config.yml` vb. ifadeleri kaldırmak veya `defaults/main.yml` / `mappings/templates.yml` / env değişkenleri ile eşleştirmek.  
   - AWX_SETUP, DATABASE_CONNECTION, CONNECTIVITY_ITEMS, TEMPLATE_ANALYSIS için ya dosya eklemek ya da README’deki linkleri kaldırmak.
5. **Database collector:** Production planı sürüyorsa `db_collector.py` ve `main.py`/`collect_data.yml` entegrasyonu.

### Öncelik 3
6. **Report generator / formatter’lar:** İleride JSON/HTML/CSV dosya çıktısı istenirse `report_generator` ve formatter modülleri eklenebilir.
7. **Performans ve kalite:** Büyük host/item setleri için ölçüm, gerekirse optimizasyon; flake8/mypy/black ile sürekli kontrol.

---

## 10. Özet Tablo

| Kategori | Tamamlanan | Eksik / Dikkat |
|----------|------------|-----------------|
| Altyapı & config | Proje yapısı, settings, template_loader, logger, mappings | README’deki config/ ve bazı doc linkleri |
| Veri toplama | API collector | DB collector |
| Analiz | Template, connectivity, data analyzer | - |
| Raporlama | Email (HTML+text) | Report generator, JSON/HTML/CSV (opsiyonel) |
| Orkestrasyon | Playbook, role, tüm task’lar, step flags, rescue | - |
| Test | test_manual.py, test_with_mock_data.py | Unit/integration (pytest) |
| Dokümantasyon | Architecture, data flow, schema, plan, task breakdown, kılavuzlar | CURRENT_STATUS (manuel test), README (config, bazı doc linkleri) |

---

*Bu analiz, `zabbix-monitoring` klasöründe yer alan kaynak kod, playbook’lar, dokümantasyon ve mevcut CURRENT_STATUS bilgisine dayanmaktadır.*
