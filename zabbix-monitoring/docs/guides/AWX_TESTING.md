# Ansible AWX Test Kılavuzu

Bu kılavuz, Zabbix Monitoring Integration'ı Ansible AWX üzerinden nasıl test edeceğinizi açıklar.

## 📋 İçindekiler

- [Gereksinimler](#gereksinimler)
- [AWX Variables Yapılandırması](#awx-variables-yapılandırması)
- [Test Senaryoları](#test-senaryoları)
- [Adım Adım Test](#adım-adım-test)
- [Sorun Giderme](#sorun-giderme)

## 🔧 Gereksinimler

### AWX Yapılandırması

1. **Project Oluşturma**
   - AWX'te yeni bir Project oluşturun
   - SCM Type: Git
   - SCM URL: Repository URL'nizi girin
   - SCM Branch: `development` (veya test için branch)

2. **Inventory Oluşturma**
   - Localhost için bir inventory oluşturun
   - Host: `localhost`
   - Variables: Boş bırakılabilir (playbook variables kullanılacak)

3. **Job Template Oluşturma**
   - Name: `Zabbix Monitoring Check`
   - Job Type: `Run`
   - Inventory: Oluşturduğunuz inventory
   - Project: Oluşturduğunuz project
   - Playbook: `playbooks/zabbix_tag_based_monitoring.yaml`
   - Credentials: Gerekli credentials (varsa)

## 📝 AWX Variables Yapılandırması

### Zorunlu Variables (Required)

AWX Job Template'in **Variables** alanına aşağıdaki değişkenleri ekleyin:

```yaml
---
# Zabbix API Connection (ZORUNLU)
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password_here"
```

### Opsiyonel Variables

#### Email Bildirimi

```yaml
# Email Notification (OPSIYONEL - Test için önerilir)
mail_recipients:
  - "test@example.com"
  - "admin@example.com"

# Email SMTP Ayarları (Varsayılanlar genelde yeterli)
mail_smtp_host: "10.34.8.191"
mail_smtp_port: 587
mail_from: "infrareport@alert.bulutistan.com"
```

#### Debug ve Logging

```yaml
# Debug Mode (Test için önerilir)
debug_enabled: true
debug_save_intermediate_files: true
debug_output_dir: "./debug_output"

# Logging
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
log_file: "./logs/zabbix_monitoring.log"
```

#### Filtreleme (Test için sınırlı veri)

```yaml
# Sadece belirli host group'larını test etmek için
filter_host_groups:
  - "Linux Servers"
  - "Windows Servers"

# Sadece belirli template'leri test etmek için
filter_templates:
  - "BLT - Lenovo ICT XCC Monitoring"
```

#### Step-by-Step Execution (Debug için)

```yaml
# Her adımı ayrı test etmek için
step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: true
step_generate_report: true
step_send_notifications: true
```

### Tam Örnek Variables (Test için)

```yaml
---
# Zabbix API Connection (ZORUNLU)
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password_here"

# Email Notification (Test için)
mail_recipients:
  - "test@example.com"

# Debug Mode
debug_enabled: true
debug_save_intermediate_files: true
log_level: "INFO"

# Step-by-step execution (Tüm adımları çalıştır)
step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: true
step_generate_report: true
step_send_notifications: true
```

## 🧪 Test Senaryoları

### Senaryo 1: Minimal Test (Sadece Veri Toplama)

**Amaç:** Sadece Zabbix'ten veri toplamayı test eder.

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

# Sadece veri toplama adımını çalıştır
step_collect_data: true
step_analyze_templates: false
step_detect_connectivity: false
step_analyze_data: false
step_check_master_items: false
step_generate_report: false
step_send_notifications: false

# Debug
debug_enabled: true
log_level: "INFO"
```

**Beklenen Sonuç:**
- Job başarıyla tamamlanır
- `debug_output/hosts.json` dosyası oluşur
- `debug_output/templates.json` dosyası oluşur
- `debug_output/items.json` dosyası oluşur

### Senaryo 2: Tam Workflow Test (Email Olmadan)

**Amaç:** Tüm workflow'u email göndermeden test eder.

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

# Tüm adımları çalıştır (email hariç)
step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: true
step_generate_report: true
step_send_notifications: false  # Email gönderme

# Debug
debug_enabled: true
log_level: "INFO"
```

**Beklenen Sonuç:**
- Tüm adımlar başarıyla tamamlanır
- `debug_output/` klasöründe tüm intermediate dosyalar oluşur
- `debug_output/analysis_results.json` dosyası oluşur

### Senaryo 3: Tam Test (Email ile)

**Amaç:** Tüm workflow'u email göndererek test eder.

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

# Email Notification
mail_recipients:
  - "test@example.com"

# SMTP (varsayılanlar genelde yeterli)
mail_smtp_host: "10.34.8.191"
mail_smtp_port: 587
mail_from: "infrareport@alert.bulutistan.com"

# Debug
debug_enabled: true
log_level: "INFO"
```

**Beklenen Sonuç:**
- Tag-based connectivity analizi tamamlanır
- Email gönderilir
- Email'de HTML rapor ve `zabbix_connectivity_raporu.csv` eki bulunur

### Senaryo 4: Sınırlı Veri Testi

**Amaç:** Sadece belirli host group'larını test eder.

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

# Filtreleme
filter_host_groups:
  - "Linux Servers"

# Debug
debug_enabled: true
log_level: "INFO"
```

**Beklenen Sonuç:**
- Sadece belirtilen host group'larından veri toplanır
- Daha hızlı test süresi

## 📊 Adım Adım Test

### 1. İlk Test: Konfigürasyon Doğrulama

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: false
step_detect_connectivity: false
step_analyze_data: false
step_check_master_items: false
step_generate_report: false
step_send_notifications: false

debug_enabled: true
log_level: "DEBUG"
```

**Kontrol:**
- Job başarıyla çalışıyor mu?
- `debug_output/` klasörü oluştu mu?
- Log dosyasında hata var mı?

### 2. İkinci Test: Veri Toplama

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: false
step_analyze_data: false
step_check_master_items: false
step_generate_report: false
step_send_notifications: false

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- `debug_output/hosts.json` dosyası var mı?
- `debug_output/templates.json` dosyası var mı?
- `debug_output/items.json` dosyası var mı?
- `debug_output/template_analysis.json` dosyası var mı?

### 3. Üçüncü Test: Connectivity Tespiti

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: false
step_check_master_items: false
step_generate_report: false
step_send_notifications: false

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- `debug_output/connectivity_items.json` dosyası var mı?
- `debug_output/master_items.json` dosyası var mı?
- Connectivity item'lar doğru tespit edildi mi?

### 4. Dördüncü Test: Veri Analizi

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: false
step_generate_report: false
step_send_notifications: false

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- `debug_output/analysis_results.json` dosyası var mı?
- Analysis summary'de veri var mı?
- Connectivity score'lar hesaplandı mı?

### 5. Beşinci Test: Master Items Kontrolü

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: true
step_generate_report: false
step_send_notifications: false

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- `debug_output/master_items_check.json` dosyası var mı?
- Master item'lar kontrol edildi mi?

### 6. Altıncı Test: Rapor Oluşturma

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

step_collect_data: true
step_analyze_templates: true
step_detect_connectivity: true
step_analyze_data: true
step_check_master_items: true
step_generate_report: true
step_send_notifications: false

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- Rapor verisi hazırlandı mı?
- Email içeriği oluşturuldu mu?

### 7. Yedinci Test: Email Gönderimi

**Variables:**
```yaml
---
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "your_password"

mail_recipients:
  - "test@example.com"

mail_smtp_host: "10.34.8.191"
mail_smtp_port: 587
mail_from: "infrareport@alert.bulutistan.com"

debug_enabled: true
log_level: "INFO"
```

**Kontrol:**
- Email gönderildi mi?
- Email konusu doğru mu? (`Zabbix Connectivity Raporu - ...`)
- HTML rapor email'de var mı?
- `zabbix_connectivity_raporu.csv` eki email'de var mı?

## 🔍 Debug Output Dosyaları

AWX Job çalıştıktan sonra, `debug_output_dir` klasöründe şu dosyalar oluşur:

```
debug_output/
├── hosts.json                    # Toplanan host'lar
├── templates.json                # Toplanan template'ler
├── items.json                    # Toplanan item'lar
├── history.json                  # Item history verileri
├── template_analysis.json        # Template analiz sonuçları
├── connectivity_items.json       # Tespit edilen connectivity item'lar
├── master_items.json            # Tespit edilen master item'lar
├── analysis_results.json         # Analiz sonuçları
├── master_items_check.json       # Master item kontrol sonuçları
└── *.txt                         # Debug summary dosyaları
```

## 🐛 Sorun Giderme

### Hata: "zabbix_url is required"

**Çözüm:**
- AWX Variables'da `zabbix_url` değişkenini ekleyin
- Değerin doğru olduğundan emin olun

### Hata: "Template mapping file not found"

**Çözüm:**
- Project'in doğru branch'ten çekildiğinden emin olun
- `mappings/templates.yml` dosyasının mevcut olduğunu kontrol edin

### Hata: "Authentication failed"

**Çözüm:**
- Zabbix kullanıcı adı ve şifresini kontrol edin
- Zabbix URL'inin doğru olduğundan emin olun
- Network bağlantısını kontrol edin

### Hata: "Email sending failed"

**Çözüm:**
- SMTP ayarlarını kontrol edin
- `mail_recipients` listesinin doğru formatta olduğundan emin olun
- SMTP sunucusuna erişim olduğundan emin olun

### Job Çok Yavaş Çalışıyor

**Çözüm:**
- `filter_host_groups` kullanarak sınırlı veri test edin
- `api_batch_size` değerini artırın
- `max_workers` değerini ayarlayın

## 📋 Test Checklist

AWX'te test yaparken kontrol edin:

- [ ] Zorunlu variables eklendi mi?
- [ ] Zabbix API bağlantısı çalışıyor mu?
- [ ] Template mapping dosyası mevcut mu?
- [ ] Her adım başarıyla tamamlanıyor mu?
- [ ] Debug output dosyaları oluşuyor mu?
- [ ] Email gönderimi çalışıyor mu?
- [ ] Log dosyalarında hata var mı?

## 🔗 İlgili Dokümanlar

- [Manual Testing Guide](MANUAL_TESTING.md)
- [Email Notification Guide](EMAIL_NOTIFICATION_GUIDE.md)
- [Usage Guide](USAGE.md)
