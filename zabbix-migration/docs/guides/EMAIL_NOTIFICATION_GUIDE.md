# Email Notification Kullanım Kılavuzu

## Özet

Zabbix Migration playbook'u, başarısız işlemler (eklenemeyen sunucular) olduğunda otomatik olarak e-posta bildirimi gönderir.

## SMTP Konfigürasyonu

Varsayılan SMTP ayarları (sabit, değiştirilemez):
- **SMTP Sunucu**: `10.34.8.191`
- **SMTP Port**: `587`
- **Gönderen Adres**: `infrareport@alert.bulutistan.com`
- **User Authentication**: `False` (kullanıcı adı/şifre kullanılmaz)
- **TLS**: `False` (TLS kullanılmaz)

**Not**: SMTP ayarları varsayılan olarak yukarıdaki değerlere sabitlenmiştir. Değiştirilmesi gerekirse `defaults/main.yml` dosyasından güncellenebilir.

## Kullanım

### Temel Kullanım (E-posta ile)

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['user1@example.com','user2@example.com']"
```

### Tek Alıcı ile

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "mail_recipients=['admin@bulutistan.com']"
```

### E-posta Olmadan Çalıştırma

E-posta gönderilmesini istemiyorsanız, `mail_recipients` parametresini atlayın:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

## E-posta İçeriği

E-posta şu bilgileri içerir:

### Özet Bölümü
- Toplam işlem sayısı
- Başarılı (Eklendi) sayısı
- Güncellendi sayısı
- Başarısız (Eklenemedi) sayısı

### Detaylı Tablo
Her sunucu için:
- **Sunucu Adı**: Hostname
- **IP Adresi**: Primary IP
- **İşlem Durumu**: 
  - `EKLENDİ` (yeşil)
  - `GÜNCELLENDİ` (mavi)
  - `EKLENEMEDİ` (kırmızı)
- **Sebep/Açıklama**: Hata mesajı veya başarı durumu

## E-posta Gönderme Koşulları

E-posta **sadece** şu durumlarda gönderilir:
1. En az bir sunucu eklenemedi (`status: eklenemedi`)
2. `mail_recipients` parametresi tanımlı ve boş değil

Tüm işlemler başarılıysa e-posta gönderilmez.

## Eklenememe Sebepleri

Bir sunucu şu durumlarda eklenemez:

1. **Hostname eksik**: `HOSTNAME` alanı boş veya tanımsız
2. **IP adresi eksik**: `HOST_IP` alanı boş veya tanımsız
3. **Template bulunamadı**: Device type için template mapping bulunamadı
4. **Proxy group bulunamadı**: DC_ID için proxy group eşleşmesi yapılamadı
5. **Device type bulunamadı**: Netbox device type mapping'de eşleşme yok
6. **Zabbix API hatası**: Host create/update sırasında API hatası

## SMTP Ayarlarını Özelleştirme

Varsayılan SMTP ayarlarını değiştirmek için:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
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
Zabbix Migration İşlem Raporu

ÖZET:
Toplam İşlem: 10
Başarılı (Eklendi): 7
Güncellendi: 2
Başarısız (Eklenemedi): 1

DETAYLI LİSTE:
-------------

Sunucu: server-01
IP: 10.0.0.1
Durum: EKLENDİ
Sebep: -

Sunucu: server-02
IP: 10.0.0.2
Durum: GÜNCELLENDİ
Sebep: -

Sunucu: server-03
IP: 10.0.0.3
Durum: EKLENEMEDİ
Sebep: Template bulunamadı
```

## Notlar

- E-posta HTML formatında gönderilir (tablo formatında)
- Plain text versiyonu da eklenecektir
- E-posta gönderimi sadece başarısız işlemler varsa yapılır
- `mail_recipients` parametresi zorunlu değildir (opsiyonel)

