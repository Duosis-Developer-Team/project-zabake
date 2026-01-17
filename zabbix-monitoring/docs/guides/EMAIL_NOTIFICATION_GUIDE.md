# Email Notification Kullanım Kılavuzu

## Özet

Zabbix Monitoring Integration playbook'u, monitoring kontrolü tamamlandıktan sonra otomatik olarak e-posta bildirimi gönderir.

## SMTP Konfigürasyonu

Varsayılan SMTP ayarları:
- **SMTP Sunucu**: `10.34.8.191`
- **SMTP Port**: `587`
- **Gönderen Adres**: `infrareport@alert.bulutistan.com`
- **User Authentication**: `False` (kullanıcı adı/şifre kullanılmaz)
- **TLS**: `False` (TLS kullanılmaz)

**Not**: SMTP ayarları varsayılan olarak yukarıdaki değerlere sabitlenmiştir. Değiştirilmesi gerekirse `defaults/main.yml` dosyasından güncellenebilir.

## Kullanım

### Temel Kullanım (E-posta ile)

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['user1@example.com','user2@example.com']"
```

### Tek Alıcı ile

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['admin@bulutistan.com']"
```

### E-posta Olmadan Çalıştırma

E-posta gönderilmesini istemiyorsanız, `mail_recipients` parametresini atlayın:

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

## E-posta İçeriği

E-posta şu bilgileri içerir:

### Özet Bölümü
- Toplam host sayısı
- Connectivity'ye sahip host sayısı
- Connectivity sorunu olan host sayısı
- Ortalama connectivity skoru
- Toplam/aktif/inaktif item sayıları

### Durum Bilgisi
- Tüm host'lar sağlıklı mı?
- Sorun tespit edildi mi?

### Sorunlu Host'lar (Varsa)
- Hostname
- Connectivity skoru
- Item durumları
- Sorun detayları

## E-posta Gönderme Koşulları

E-posta **her zaman** gönderilir (başarılı veya başarısız fark etmez), ancak şu koşullar sağlanmalıdır:
1. `mail_recipients` parametresi tanımlı ve boş değil
2. Analiz sonuçları başarıyla oluşturulmuş olmalı

## SMTP Ayarlarını Özelleştirme

Varsayılan SMTP ayarlarını değiştirmek için:

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['user@example.com']" \
  -e "mail_smtp_host=10.34.8.191" \
  -e "mail_smtp_port=587" \
  -e "mail_from=infrareport@alert.bulutistan.com" \
  -e "mail_smtp_use_tls=false"
```

## Örnek E-posta Çıktısı

```
Zabbix Monitoring Connectivity Report

ÖZET:
-----
Toplam Host: 100
Connectivity'ye Sahip Host: 95
Connectivity Sorunu Olan Host: 5
Ortalama Connectivity Skoru: 0.92
Toplam Item: 500
Aktif Item: 475
İnaktif Item: 25

⚠️  CONNECTIVITY SORUNLARI TESPİT EDİLDİ
Bazı host'larda connectivity sorunları tespit edildi.
```

## Notlar

- E-posta HTML formatında gönderilir (tablo formatında)
- Plain text versiyonu da eklenir
- E-posta gönderimi her zaman yapılır (başarılı/başarısız fark etmez)
- `mail_recipients` parametresi zorunlu değildir (opsiyonel)
- Raporlar sadece email olarak gönderilir, lokal dosya sistemi veya remote storage kullanılmaz

## AWX'te Kullanım

AWX'te email gönderimi için:

1. Job Template'de `mail_recipients` extra variable'ını tanımlayın
2. SMTP ayarları varsayılan değerlerle çalışır
3. Email her job çalıştırmasında gönderilir

Örnek AWX extra_vars:
```yaml
mail_recipients:
  - "admin@example.com"
  - "team@example.com"
```

## 🔗 İlgili Dokümanlar

- [Usage Guide](USAGE.md)
- [AWX Setup Guide](AWX_SETUP.md)
- [Development Plan](../development/DEVELOPMENT_PLAN.md)
