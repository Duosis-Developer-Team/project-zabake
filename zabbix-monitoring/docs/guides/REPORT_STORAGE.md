# Report Storage Guide

Bu kılavuz, Zabbix Monitoring Integration raporlarının nerede depolanacağını ve nasıl gönderileceğini açıklar.

## 📋 Rapor Depolama Seçenekleri

### 1. Lokal Dosya Sistemi (Varsayılan)

Raporlar varsayılan olarak lokal dosya sistemine kaydedilir.

**Konfigürasyon:**
```yaml
report_storage:
  local:
    enabled: true
    path: "./reports"
    keep_last_n: 10  # Son 10 raporu sakla, 0 = hepsini sakla
```

**Özellikler:**
- Raporlar `output_dir` klasörüne kaydedilir
- Eski raporları otomatik temizleme (keep_last_n)
- AWX'te artifact olarak saklanır

### 2. AWX Artifact Storage

AWX üzerinde çalıştırıldığında, raporlar otomatik olarak AWX artifact olarak saklanır.

**Konfigürasyon:**
```yaml
report_storage:
  awx_artifacts:
    enabled: true  # AWX'te otomatik aktif
    path: "{{ output_dir }}"
```

**Özellikler:**
- AWX job sonuçlarında indirilebilir
- AWX web arayüzünden erişilebilir
- Job geçmişinde saklanır

### 3. Email Gönderme

Raporlar email ile gönderilebilir.

**Konfigürasyon:**
```yaml
report_storage:
  email:
    enabled: true
    smtp_host: "smtp.example.com"
    smtp_port: 25
    smtp_username: "user@example.com"
    smtp_password: "password"
    from_address: "zabbix-monitoring@example.com"
    recipients:
      - "admin@example.com"
      - "team@example.com"
    send_on_success: true
    send_on_failure: true
    attach_reports: true
    formats_to_attach: ["html", "json"]
```

**Özellikler:**
- HTML ve plain text formatında email
- Rapor dosyaları ek olarak gönderilir
- Başarılı/başarısız durumlara göre gönderim kontrolü
- Özet istatistikler email içinde

### 4. Remote Storage (S3, NFS, SFTP)

Raporlar uzak depolama sistemlerine yüklenebilir.

#### S3 Storage

```yaml
report_storage:
  remote:
    enabled: true
    type: "s3"
    s3_bucket: "my-reports-bucket"
    s3_prefix: "zabbix-monitoring/"
    s3_access_key: "ACCESS_KEY"
    s3_secret_key: "SECRET_KEY"
    s3_region: "us-east-1"
```

#### SFTP Storage

```yaml
report_storage:
  remote:
    enabled: true
    type: "sftp"
    remote_host: "sftp.example.com"
    remote_path: "/reports/zabbix-monitoring"
    remote_user: "sftp_user"
    remote_key: "/path/to/private_key"
```

#### NFS Storage

```yaml
report_storage:
  remote:
    enabled: true
    type: "nfs"
    remote_host: "nfs.example.com"
    remote_path: "/exports/reports"
```

## 🔧 Kullanım Örnekleri

### Örnek 1: Sadece Lokal Depolama

```yaml
report_storage:
  local:
    enabled: true
    path: "./reports"
    keep_last_n: 10
  email:
    enabled: false
  remote:
    enabled: false
```

### Örnek 2: Email + Lokal Depolama

```yaml
report_storage:
  local:
    enabled: true
    path: "./reports"
  email:
    enabled: true
    smtp_host: "smtp.example.com"
    smtp_port: 25
    from_address: "monitoring@example.com"
    recipients:
      - "admin@example.com"
    attach_reports: true
    formats_to_attach: ["html"]
```

### Örnek 3: S3 + Email

```yaml
report_storage:
  local:
    enabled: true
  email:
    enabled: true
    recipients: ["admin@example.com"]
  remote:
    enabled: true
    type: "s3"
    s3_bucket: "reports-bucket"
    s3_prefix: "zabbix-monitoring/"
```

## 📧 Email İçeriği

Email şu bilgileri içerir:

- **Özet İstatistikler:**
  - Toplam host sayısı
  - Connectivity'ye sahip host sayısı
  - Connectivity sorunu olan host sayısı
  - Ortalama connectivity skoru
  - Toplam/aktif/inaktif item sayıları

- **Durum Bilgisi:**
  - Tüm host'lar sağlıklı mı?
  - Sorun tespit edildi mi?

- **Ekler:**
  - HTML rapor dosyası
  - JSON rapor dosyası (opsiyonel)
  - CSV rapor dosyası (opsiyonel)

## 🔐 Güvenlik Notları

### Email Güvenliği

- SMTP şifreleri AWX credential store'da saklanmalı
- TLS/SSL kullanımı önerilir (smtp_port: 587 veya 465)

### S3 Güvenliği

- Access key ve secret key AWX credential store'da saklanmalı
- IAM role kullanımı önerilir (AWX'te)

### SFTP Güvenliği

- Private key dosyaları güvenli şekilde saklanmalı
- Key-based authentication kullanılmalı

## 📊 Rapor Dosya Adları

Rapor dosyaları şu formatta adlandırılır:

```
zabbix_monitoring_{timestamp}.{format}
```

Örnek:
- `zabbix_monitoring_2024-01-15T10-30-00.json`
- `zabbix_monitoring_2024-01-15T10-30-00.html`
- `zabbix_monitoring_2024-01-15T10-30-00.csv`

## 🔄 AWX'te Kullanım

AWX'te raporlar otomatik olarak:

1. **Lokal olarak kaydedilir** (`output_dir`)
2. **AWX artifact olarak saklanır** (indirilebilir)
3. **Email gönderilir** (yapılandırılmışsa)
4. **Remote storage'a yüklenir** (yapılandırılmışsa)

AWX job sonuçlarında:
- Rapor dosyaları "Artifacts" sekmesinde görünür
- İndirilebilir
- Job geçmişinde saklanır

## 📝 Notlar

- Tüm depolama seçenekleri aynı anda kullanılabilir
- Email gönderimi başarısız olsa bile raporlar kaydedilir
- Remote storage yüklemesi başarısız olsa bile lokal kopya saklanır
- Eski raporlar otomatik temizlenir (keep_last_n ayarına göre)

## 🔗 İlgili Dokümanlar

- [Usage Guide](USAGE.md)
- [AWX Setup Guide](AWX_SETUP.md)
- [Development Plan](../development/DEVELOPMENT_PLAN.md)
