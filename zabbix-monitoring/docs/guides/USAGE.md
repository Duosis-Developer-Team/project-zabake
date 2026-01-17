# Usage Guide - Zabbix Monitoring Integration

Bu kılavuz, Zabbix Monitoring Integration modülünün nasıl kullanılacağını açıklar.

## 📋 İçindekiler

- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Konfigürasyon](#konfigürasyon)
- [Kullanım Senaryoları](#kullanım-senaryoları)
- [Çıktı Formatları](#çıktı-formatları)
- [Sorun Giderme](#sorun-giderme)

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.8+
- Ansible 2.9+
- Zabbix API erişimi veya Zabbix database erişimi

### Kurulum

```bash
# Ansible collections kurulumu
cd zabbix-monitoring
ansible-galaxy collection install -r requirements.yml

# Python paketleri kurulumu
pip install -r scripts/requirements.txt
```

### Temel Kullanım

#### Ansible AWX ile

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "output_format=json"
```

#### Python Script ile

```bash
python scripts/main.py \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password \
  --output-format json
```

## ⚙️ Konfigürasyon

### Konfigürasyon Dosyaları

Konfigürasyon dosyaları `config/` klasöründe bulunur:

- `zabbix_api_config.yml`: Zabbix API ayarları
- `db_config.yml`: Database ayarları
- `monitoring_config.yml`: Monitoring ayarları

### Environment Variables

Konfigürasyon dosyaları yerine environment variable'lar da kullanılabilir:

```bash
export ZABBIX_URL="https://zabbix.example.com/api_jsonrpc.php"
export ZABBIX_USER="admin"
export ZABBIX_PASSWORD="password"
export MONITORING_DATA_SOURCE="api"
export LOG_LEVEL="INFO"
```

### Örnek Konfigürasyon

```yaml
# config/zabbix_api_config.yml
zabbix:
  api:
    url: "https://zabbix.example.com/api_jsonrpc.php"
    user: "admin"
    password: "password"
    timeout: 30
    verify_ssl: true

# config/monitoring_config.yml
monitoring:
  data_source: "api"
  connectivity_patterns:
    - "icmpping"
    - "icmppingsec"
    - "net.tcp.service"
  analysis:
    max_data_age: 3600
    min_connectivity_score: 0.8
    inactive_threshold: 7200
```

## 📊 Kullanım Senaryoları

### Senaryo 1: Tüm Host'ları Analiz Et

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Senaryo 2: Belirli Host Group'larını Analiz Et

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "host_groups=Linux Servers,Windows Servers"
```

### Senaryo 3: Database'den Veri Çek

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "data_source=database" \
  -e "db_host=zabbix-db.example.com" \
  -e "db_name=zabbix" \
  -e "db_user=zabbix" \
  -e "db_password=password"
```

### Senaryo 4: HTML Rapor Oluştur

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "output_format=html"
```

## 📄 Çıktı Formatları

### JSON Format

```json
{
  "report_metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "total_hosts": 100
  },
  "summary": {
    "total_hosts": 100,
    "hosts_with_connectivity": 95,
    "average_connectivity_score": 0.92
  },
  "hosts": [...]
}
```

### HTML Format

HTML formatında görsel bir rapor oluşturulur. Tarayıcıda açılabilir.

### CSV Format

CSV formatında Excel'de açılabilir tablo formatında rapor oluşturulur.

## 🔧 Gelişmiş Kullanım

### Custom Connectivity Patterns

```yaml
# config/monitoring_config.yml
monitoring:
  connectivity_patterns:
    - "icmpping"
    - "custom.ping.check"
    - "net.tcp.service[ssh]"
```

### Filtreleme

```bash
# Sadece aktif host'ları analiz et
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "filter_status=enabled"

# Belirli template'lere sahip host'ları analiz et
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "filter_templates=Template OS Linux"
```

## 🐛 Sorun Giderme

### Yaygın Hatalar

#### 1. Authentication Hatası

```
Error: Authentication failed
```

**Çözüm**: Zabbix kullanıcı adı ve şifresini kontrol edin.

#### 2. Connection Timeout

```
Error: Connection timeout
```

**Çözüm**: Zabbix URL'ini ve network bağlantısını kontrol edin.

#### 3. No Data Found

```
Warning: No connectivity items found
```

**Çözüm**: Connectivity pattern'lerini kontrol edin ve host'larda bu pattern'lere uygun item'ların olduğundan emin olun.

### Log Dosyaları

Log dosyaları varsayılan olarak `logs/zabbix_monitoring.log` konumunda bulunur.

Log seviyesini değiştirmek için:

```bash
export LOG_LEVEL="DEBUG"
```

### Debug Modu

Detaylı log için:

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "log_level=DEBUG" \
  -e "zabbix_url=..." \
  -e "zabbix_user=..." \
  -e "zabbix_password=..."
```

## 📝 Notlar

- İlk çalıştırmada veri toplama işlemi biraz zaman alabilir
- Büyük Zabbix kurulumlarında işlem süresi artabilir
- Database kullanımı API'ye göre daha hızlı olabilir
- Rapor dosyaları `reports/` klasöründe saklanır

## 🔗 İlgili Dokümanlar

- [AWX Setup Guide](AWX_SETUP.md)
- [Database Connection Guide](DATABASE_CONNECTION.md)
- [Development Plan](../development/DEVELOPMENT_PLAN.md)
