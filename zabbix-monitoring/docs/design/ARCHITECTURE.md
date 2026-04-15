# Architecture Design - Zabbix Monitoring Integration

## 📋 Genel Bakış

Bu doküman, Zabbix Monitoring Integration modülünün mimari tasarımını açıklar.

## 🏗️ Sistem Mimarisi

### Yüksek Seviye Mimari

```
┌─────────────────┐
│   Ansible AWX   │
│  (Orchestrator) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ansible        │
│  Playbooks      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Python Scripts │◄─────│  Zabbix API/DB   │
│  (Main Logic)   │      │  (Data Source)   │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│   Reports       │
│  (JSON/HTML/CSV)│
└─────────────────┘
```

## 🔄 Veri Akışı

### 1. Veri Toplama Aşaması

```
AWX Playbook
    │
    ├─► Collect Hosts (API/DB)
    │       │
    │       └─► Host List
    │
    ├─► Collect Templates (API/DB)
    │       │
    │       └─► Template List
    │
    └─► Collect Items (API/DB)
            │
            └─► Item List + History
```

### 2. Analiz Aşaması

```
Collected Data
    │
    ├─► Template Analyzer
    │       │
    │       └─► Template Structure
    │
    ├─► Connectivity Analyzer
    │       │
    │       └─► Connectivity Items
    │
    └─► Data Analyzer
            │
            └─► Analysis Results
```

### 3. Raporlama Aşaması

```
Analysis Results
    │
    ├─► Report Generator
    │       │
    │       ├─► JSON Formatter
    │       ├─► HTML Formatter
    │       └─► CSV Formatter
    │
    └─► Output Files
```

## 📦 Bileşenler

### 1. Data Collectors

**Amaç**: Zabbix'ten veri çekme

**Modüller**:
- `api_collector.py`: Zabbix API üzerinden veri çekme
- `db_collector.py`: Zabbix database'den veri çekme

**Sorumluluklar**:
- Authentication
- Data fetching
- Error handling
- Rate limiting
- Data caching

### 2. Analyzers

**Amaç**: Veri analizi ve işleme

**Modüller**:
- `template_analyzer.py`: Template yapısını analiz etme
- `connectivity_analyzer.py`: Connectivity item'larını tespit etme
- `data_analyzer.py`: Veri durumunu analiz etme

**Sorumluluklar**:
- Template parsing
- Pattern matching
- Data analysis
- Status calculation

### 3. Report Generators

**Amaç**: Analiz sonuçlarını raporlama

**Modüller**:
- `report_generator.py`: Ana rapor oluşturucu
- `formatters.py`: Format dönüştürücüler

**Sorumluluklar**:
- Report generation
- Format conversion
- Output management

### 4. Email Notification

**Amaç**: Connectivity analiz sonuçlarını e-posta ile raporlama

**Dosya**: `roles/zabbix_monitoring/files/send_notification_email_smtp.py`

**Akış**:
```
Ansible set_fact (HTML / plain text / subject)
        │
        ▼
/tmp/zabbix_monitoring/
  ├── analysis_results.json   ← connectivity_analysis verisi
  ├── email_body.html         ← HTML rapor
  └── email_body.txt          ← düz metin yedek
        │
        ▼
python3 send_notification_email_smtp.py
  --html-file ... --text-file ... --results-file ...
        │
        ▼
SMTP → MIMEMultipart(mixed)
  ├── alternative: HTML + plain text
  └── attachment: zabbix_connectivity_raporu.csv
```

**Neden dosya tabanlı yaklaşım?**
E-posta içeriği `shell` heredoc içine doğrudan gömüldüğünde yüzlerce host olduğunda `ARG_MAX` sınırı aşılır ve özel karakterler heredoc interpolasyonunu bozar. İçeriği önce geçici dosyalara yazarak (`copy` modülü) sonra Python scriptine dosya yolu argümanı olarak göndermek bu sorunları ortadan kaldırır.

**Değişken isimleri** (`defaults/main.yml` ve AWX extra vars):
- `mail_smtp_host`, `mail_smtp_port`, `mail_smtp_username`, `mail_smtp_password`
- `mail_from`, `mail_recipients` (liste)
- `zabbix_monitoring_tmp_dir` (default: `/tmp/zabbix_monitoring`)

### 5. Utilities

**Amaç**: Ortak yardımcı fonksiyonlar

**Modüller**:
- `logger.py`: Logging utility
- `validators.py`: Veri doğrulama

**Sorumluluklar**:
- Logging
- Validation
- Error handling
- Configuration management

## 🔌 API Entegrasyonları

### Zabbix API

**Endpoint**: `https://zabbix.example.com/api_jsonrpc.php`

**Kullanılan Metodlar**:
- `user.login`: Authentication
- `host.get`: Host listesi
- `template.get`: Template listesi
- `item.get`: Item listesi
- `history.get`: Item history
- `trend.get`: Item trends

**Rate Limiting**: API'ye minimum yük için batch processing

### Zabbix Database

**Connection**: PostgreSQL (passive database)

**Tablolar**:
- `hosts`: Host bilgileri
- `items`: Item bilgileri
- `history_*`: History tabloları
- `trends_*`: Trend tabloları

**Query Optimization**: Index kullanımı ve batch queries

## 📊 Veri Yapıları

### Host Data Structure

```python
{
    "hostid": "12345",
    "host": "hostname.example.com",
    "name": "Host Display Name",
    "status": "0",  # 0=enabled, 1=disabled
    "templates": [
        {
            "templateid": "10001",
            "name": "Template OS Linux"
        }
    ],
    "items": [...]
}
```

### Template Data Structure

```python
{
    "templateid": "10001",
    "name": "Template OS Linux",
    "items": [
        {
            "itemid": "20001",
            "key_": "icmpping",
            "name": "ICMP ping",
            "type": "0",  # Zabbix agent
            "value_type": "3"  # Numeric (unsigned)
        }
    ],
    "parent_templates": [...]
}
```

### Connectivity Item Structure

```python
{
    "itemid": "20001",
    "hostid": "12345",
    "key_": "icmpping",
    "name": "ICMP ping",
    "template": "Template OS Linux",
    "lastvalue": "1",
    "lastclock": "1672531200",
    "status": "active"
}
```

### Analysis Result Structure

```python
{
    "hostid": "12345",
    "hostname": "hostname.example.com",
    "connectivity_items": [
        {
            "itemid": "20001",
            "key_": "icmpping",
            "status": "active",
            "last_data_time": "1672531200",
            "data_available": true
        }
    ],
    "connectivity_score": 0.95,
    "total_items": 10,
    "active_items": 9,
    "inactive_items": 1
}
```

## 🔐 Güvenlik

### Authentication

- **API**: Token-based authentication
- **Database**: Credential-based authentication
- **Credentials**: AWX credential store'da saklanır

### Data Security

- Sensitive data encryption
- Secure credential storage
- Audit logging

## ⚡ Performans

### Optimizasyon Stratejileri

1. **Batch Processing**: Toplu veri çekme
2. **Caching**: Sık kullanılan verileri cache'leme
3. **Parallel Processing**: Paralel işleme desteği
4. **Query Optimization**: Optimize edilmiş SQL sorguları
5. **Rate Limiting**: API rate limit yönetimi

### Performans Metrikleri

- Veri toplama süresi: < 5 dakika (1000 host için)
- Analiz süresi: < 2 dakika
- Rapor oluşturma süresi: < 30 saniye

## 🔄 Hata Yönetimi

### Hata Senaryoları

1. **API Connection Errors**: Retry mekanizması
2. **Database Connection Errors**: Connection pooling
3. **Data Validation Errors**: Validation ve logging
4. **Processing Errors**: Error handling ve recovery

### Logging

- Structured logging
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Log rotation
- Centralized logging (opsiyonel)

## 🧪 Test Stratejisi

### Unit Tests

- Her modül için unit testler
- Mock data kullanımı
- Edge case testleri

### Integration Tests

- End-to-end testler
- AWX playbook testleri
- Database connection testleri

### Performance Tests

- Load testing
- Stress testing
- Performance benchmarking

## 📈 Ölçeklenebilirlik

### Ölçekleme Stratejileri

1. **Horizontal Scaling**: Paralel işleme
2. **Vertical Scaling**: Resource artırımı
3. **Caching**: Veri cache'leme
4. **Database Optimization**: Query optimizasyonu

### Limitler

- Maksimum host sayısı: 10,000+
- Maksimum item sayısı: 100,000+
- İşlem süresi: < 30 dakika (10,000 host için)

## 🔧 Konfigürasyon

### Konfigürasyon Dosyaları

- `zabbix_api_config.yml`: API ayarları
- `db_config.yml`: Database ayarları
- `monitoring_config.yml`: Monitoring ayarları

### Environment Variables

- `ZABBIX_URL`: Zabbix API URL
- `ZABBIX_USER`: Zabbix kullanıcı adı
- `ZABBIX_PASSWORD`: Zabbix şifresi
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database adı

## 📝 Notlar

- Mimari, modüler ve genişletilebilir olacak şekilde tasarlanmıştır
- Her bileşen bağımsız olarak test edilebilir
- Performans optimizasyonları sürekli gözden geçirilmelidir

