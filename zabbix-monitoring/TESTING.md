# Testing Guide - Zabbix Monitoring Integration

Bu doküman, Zabbix Monitoring Integration modülünün test edilmesi için kılavuz sağlar.

## 🧪 Test Türleri

### 1. Manuel Testler

Manuel testler, sistemin gerçek Zabbix ortamında çalışıp çalışmadığını kontrol eder.

**Test Scriptleri:**
- `scripts/test_manual.py` - Manuel test scripti
- `scripts/test_with_mock_data.py` - Mock data ile test

**Detaylı Kılavuz:** [Manual Testing Guide](docs/guides/MANUAL_TESTING.md)

### 2. Unit Testler (Gelecek)

Her modül için unit testler yazılacak.

**Test Klasörü:** `tests/`

### 3. Integration Testler (Gelecek)

End-to-end testler yazılacak.

## 🚀 Hızlı Test

### Mock Data ile Test (Zabbix API Gerektirmez)

```bash
cd scripts
python test_with_mock_data.py
```

Bu test, gerçek Zabbix API'ye ihtiyaç duymadan sistemin çalışıp çalışmadığını kontrol eder.

### API Bağlantı Testi

```bash
python test_manual.py \
  --test api-connection \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password
```

### Tam Workflow Testi

```bash
python test_manual.py \
  --test full-workflow \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password \
  --output-dir ./test_output
```

## 📋 Test Checklist

### Ön Test Kontrolleri

- [ ] Python 3.8+ kurulu
- [ ] Ansible 2.9+ kurulu
- [ ] Gerekli Python paketleri kurulu (`pip install -r scripts/requirements.txt`)
- [ ] Ansible collections kurulu (`ansible-galaxy collection install -r requirements.yml`)
- [ ] Zabbix API erişimi var
- [ ] Template mapping dosyası mevcut (`mappings/templates.yml`)

### Fonksiyonel Testler

- [ ] API bağlantısı çalışıyor
- [ ] Template loader doğru çalışıyor
- [ ] Veri toplama başarılı
- [ ] Connectivity item tespiti çalışıyor
- [ ] Master item tespiti çalışıyor
- [ ] Veri analizi doğru sonuçlar veriyor
- [ ] Email gönderimi çalışıyor

### Ansible Playbook Testleri

- [ ] Playbook başarıyla çalışıyor
- [ ] Her adım debug edilebiliyor
- [ ] Intermediate dosyalar oluşturuluyor
- [ ] Email gönderimi çalışıyor

## 🔍 Test Sonuçlarını İnceleme

### Debug Output

Tüm test sonuçları `debug_output_dir` klasöründe saklanır:

```bash
ls -la ./debug_output/
cat ./debug_output/analysis_results.json | jq
```

### Log Dosyaları

```bash
tail -f ./logs/zabbix_monitoring.log
```

## 📝 Test Senaryoları

Detaylı test senaryoları için: [Manual Testing Guide](docs/guides/MANUAL_TESTING.md)

## 🔗 İlgili Dokümanlar

- [Manual Testing Guide](docs/guides/MANUAL_TESTING.md)
- [Current Status](docs/development/CURRENT_STATUS.md)
- [Usage Guide](docs/guides/USAGE.md)
