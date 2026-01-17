# Manuel Test Kılavuzu

Bu kılavuz, Zabbix Monitoring Integration modülünün manuel olarak nasıl test edileceğini açıklar.

## 📋 İçindekiler

- [Gereksinimler](#gereksinimler)
- [Test Senaryoları](#test-senaryoları)
- [Adım Adım Test](#adım-adım-test)
- [Sorun Giderme](#sorun-giderme)

## 🔧 Gereksinimler

### Sistem Gereksinimleri

- Python 3.8+
- Ansible 2.9+
- Zabbix API erişimi
- Test host'ları (template'li)

### Kurulum

```bash
cd zabbix-monitoring

# Ansible collections
ansible-galaxy collection install -r requirements.yml

# Python paketleri
pip install -r scripts/requirements.txt
```

## 🧪 Test Senaryoları

### Senaryo 1: API Bağlantı Testi

Zabbix API'ye bağlantıyı test eder.

```bash
cd scripts
python test_manual.py \
  --test api-connection \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password
```

**Beklenen Çıktı:**
```
✅ API connection successful! Found X hosts
Sample host:
  - Name: hostname
  - Host: hostname.example.com
  - Status: 0
```

### Senaryo 2: Template Loader Testi

Template yapılandırmasını yüklemeyi test eder.

```bash
python test_manual.py \
  --test template-loader \
  --template-mapping ../mappings/templates.yml
```

**Beklenen Çıktı:**
```
✅ Template loader successful! Loaded 6 templates
  - BLT - Lenovo ICT XCC Monitoring (Lenovo)
    Connection items: 2
    Master items: 0
```

### Senaryo 3: Veri Toplama Testi

Zabbix'ten veri toplamayı test eder.

```bash
python test_manual.py \
  --test data-collection \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password \
  --output-dir ./test_output
```

**Beklenen Çıktı:**
```
✅ Data collection successful!
  - Hosts: 10
  - Templates: 50
  - Items: 200
✅ Data saved to ./test_output
```

**Oluşturulan Dosyalar:**
- `test_output/hosts.json`
- `test_output/templates.json`
- `test_output/items.json`
- `test_output/history.json`

### Senaryo 4: Connectivity Tespit Testi

Connectivity item'ları tespit etmeyi test eder.

```bash
python test_manual.py \
  --test connectivity-detection \
  --template-mapping ../mappings/templates.yml \
  --input-dir ./test_output \
  --output-dir ./test_output
```

**Beklenen Çıktı:**
```
✅ Connectivity detection successful!
  - Connectivity items: 20
  - Master items: 2
Sample connectivity items:
  - snmp.availability (hostname.example.com)
```

**Oluşturulan Dosyalar:**
- `test_output/connectivity_items.json`
- `test_output/master_items.json`

### Senaryo 5: Veri Analiz Testi

Veri analizini test eder.

```bash
python test_manual.py \
  --test data-analysis \
  --template-mapping ../mappings/templates.yml \
  --input-dir ./test_output \
  --output-dir ./test_output
```

**Beklenen Çıktı:**
```
✅ Data analysis successful!
  - Total hosts: 10
  - Hosts with connectivity: 8
  - Hosts without connectivity: 2
  - Average score: 0.85
✅ Analysis results saved to ./test_output
```

**Oluşturulan Dosyalar:**
- `test_output/analysis_results.json`

### Senaryo 6: Tam Workflow Testi

Tüm workflow'u end-to-end test eder.

```bash
python test_manual.py \
  --test full-workflow \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password \
  --template-mapping ../mappings/templates.yml \
  --output-dir ./test_output
```

**Beklenen Çıktı:**
```
Step 1: Collecting data...
✅ Data collection successful!
Step 2: Detecting connectivity items...
✅ Connectivity detection successful!
Step 3: Analyzing data...
✅ Data analysis successful!
✅ Full workflow test successful!
```

## 📝 Ansible Playbook ile Test

### Temel Test (Email Olmadan)

```bash
cd playbooks
ansible-playbook zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Email ile Test

```bash
ansible-playbook zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['test@example.com']"
```

### Adım Adım Test (AWX Debug)

Her adımı ayrı test etmek için:

```bash
# Sadece veri toplama
ansible-playbook zabbix_monitoring_check.yaml \
  -e "zabbix_url=..." \
  -e "zabbix_user=..." \
  -e "zabbix_password=..." \
  -e "step_analyze_templates=false" \
  -e "step_detect_connectivity=false" \
  -e "step_analyze_data=false" \
  -e "step_check_master_items=false" \
  -e "step_generate_report=false" \
  -e "step_send_notifications=false"
```

## 🔍 Test Sonuçlarını Kontrol Etme

### Debug Output Klasörü

Tüm intermediate dosyalar `debug_output_dir` klasöründe:

```bash
ls -la ./debug_output/
```

**Dosyalar:**
- `hosts.json` - Toplanan host'lar
- `templates.json` - Toplanan template'ler
- `items.json` - Toplanan item'lar
- `history.json` - Item history verileri
- `template_analysis.json` - Template analiz sonuçları
- `connectivity_items.json` - Tespit edilen connectivity item'lar
- `master_items.json` - Tespit edilen master item'lar
- `analysis_results.json` - Analiz sonuçları
- `master_items_check.json` - Master item kontrol sonuçları

### Log Dosyaları

```bash
tail -f ./logs/zabbix_monitoring.log
```

## 🐛 Sorun Giderme

### API Bağlantı Hatası

**Hata:**
```
❌ API connection failed: Authentication failed
```

**Çözüm:**
- Zabbix kullanıcı adı ve şifresini kontrol edin
- Zabbix URL'ini doğrulayın
- Network bağlantısını kontrol edin

### Template Bulunamadı

**Hata:**
```
❌ Template loader failed: Template mapping file not found
```

**Çözüm:**
- `mappings/templates.yml` dosyasının varlığını kontrol edin
- Dosya yolunu doğrulayın

### Veri Dosyası Bulunamadı

**Hata:**
```
❌ Connectivity detection failed: hosts.json not found
```

**Çözüm:**
- Önce `data-collection` testini çalıştırın
- Input directory'yi kontrol edin

## 📊 Test Checklist

Manuel test için kontrol listesi:

- [ ] API bağlantısı çalışıyor mu?
- [ ] Template loader doğru çalışıyor mu?
- [ ] Veri toplama başarılı mı?
- [ ] Connectivity item'lar tespit ediliyor mu?
- [ ] Master item'lar tespit ediliyor mu?
- [ ] Veri analizi doğru sonuçlar veriyor mu?
- [ ] Email gönderimi çalışıyor mu?
- [ ] Debug output dosyaları oluşturuluyor mu?

## 🔗 İlgili Dokümanlar

- [Usage Guide](USAGE.md)
- [Email Notification Guide](EMAIL_NOTIFICATION_GUIDE.md)
- [Template Configuration Guide](TEMPLATE_CONFIGURATION.md)
- [Current Status](../development/CURRENT_STATUS.md)
