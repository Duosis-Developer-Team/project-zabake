# Template Macros Feature - Implementation Summary

## Tarih: 2026-01-19

## Genel Bakış

Netbox-Zabbix entegrasyonuna API-tabanlı template'ler için otomatik makro yönetimi özelliği eklendi. Bu özellik, özellikle Redfish API, FortiGate API gibi API kullanan monitoring template'leri için gerekli makroların otomatik olarak eklenmesini ve yönetilmesini sağlar.

## Problem

Daha önce sistem sadece tek tip template'leri destekliyordu (sadece SNMP veya sadece agent). API kullanan template'ler için:
- Makro ekleme yapılmıyordu
- Manuel olarak her host için makro tanımlanması gerekiyordu
- IP adresleri manuel girilmeliydi
- Birden fazla interface tipini (SNMP + API) desteklemiyordu

## Çözüm

### 1. Template Macros Tanımlama

`zabbix-netbox/mappings/templates.yml` dosyasına her template için `macros` alanı eklendi:

```yaml
HPE IPMI:
  - name: BLT - HPE ProLiant DL380 by SNMP
    type: snmpv2
  - name: HPE iLO by HTTP
    type: api
    macros:
      "{$REDFISH.API.URL}": "https://{HOST.IP}/"
      "{$REDFISH.PASSWORD}": "change_me"
      "{$REDFISH.USER}": "zabbix"
```

### 2. Otomatik IP Enjeksiyonu

`{HOST.IP}` değişkeni kullanılarak cihazın IP adresi otomatik olarak makrolara enjekte edilir:
- `{HOST.IP}` → Netbox'tan alınan primary_ip4 adresi
- Örnek: `"https://{HOST.IP}/"` → `"https://10.100.1.21/"`

### 3. Makro İşleme Mantığı

`zabbix_host_operations.yml` dosyasında aşağıdaki işlemler eklendi:

#### Host Create İşlemi:
1. Template'lerden makroları topla
2. `{HOST.IP}` değişkenlerini değiştir
3. Zabbix API formatına dönüştür
4. Host create sırasında makroları ekle

#### Host Update İşlemi:
1. Mevcut host makrolarını çek
2. Yeni makroları template'lerden al
3. Mevcut makrolarla birleştir (yeni değerler öncelikli)
4. Değişiklik varsa güncelle
5. Update raporunda makro değişikliklerini göster

## Değiştirilen Dosyalar

### 1. `zabbix-netbox/mappings/templates.yml`
- HPE IPMI için Redfish API template'i ve makroları eklendi
- Dell IPMI için Redfish API template'i ve makroları eklendi
- FortiGate için API makroları eklendi
- Dosya başına `{HOST.IP}` değişkeni açıklaması eklendi

### 2. `zabbix-netbox/playbooks/roles/netbox_zabbix_sync/tasks/zabbix_host_operations.yml`
- Makro toplama mantığı eklendi
- `{HOST.IP}` değişken değiştirme mantığı eklendi
- Host create işlemine makro desteği eklendi
- Host update işlemine makro desteği eklendi
- Makro değişiklik algılama mantığı eklendi
- Update raporuna makro değişiklikleri eklendi

### 3. `zabbix-netbox/README.md`
- Yeni özellik özelliklere eklendi
- Template Macros Kılavuzu referansı eklendi
- Mapping dosyaları açıklaması güncellendi

### 4. `zabbix-netbox/docs/guides/TEMPLATE_MACROS_GUIDE.md` (YENİ)
- Kapsamlı kullanım kılavuzu oluşturuldu
- Örnekler ve best practice'ler eklendi
- Güvenlik uyarıları eklendi
- Troubleshooting bölümü eklendi

## Özellikler

### ✅ Otomatik IP Enjeksiyonu
- `{HOST.IP}` değişkeni otomatik değiştirilir
- Netbox'tan alınan primary_ip4 kullanılır
- URL'lerde, endpoint'lerde kullanılabilir

### ✅ Çoklu Template Desteği
- Bir device type için birden fazla template tanımlanabilir
- Her template'in kendi makroları olabilir
- Farklı interface tipleri desteklenir (SNMP + API)

### ✅ Akıllı Makro Birleştirme
- Update sırasında mevcut makrolar korunur
- Yeni makrolar mevcut olanlarla birleştirilir
- Manuel eklenen makrolar silinmez

### ✅ Değişiklik Algılama
- Sadece değişen makrolar için update yapılır
- Gereksiz API çağrıları önlenir
- Update raporunda değişiklikler gösterilir

### ✅ Kapsamlı Dokümantasyon
- Detaylı kullanım kılavuzu
- Güvenlik best practice'leri
- Troubleshooting rehberi
- Gerçek dünya örnekleri

## Kullanım Örnekleri

### HPE iLO Redfish API

```yaml
HPE IPMI:
  - name: HPE iLO by HTTP
    type: api
    macros:
      "{$REDFISH.API.URL}": "https://{HOST.IP}/"
      "{$REDFISH.PASSWORD}": "change_me"
      "{$REDFISH.USER}": "zabbix"
```

**Sonuç:** Cihaz IP'si 10.100.1.21 ise:
- `{$REDFISH.API.URL}` = `https://10.100.1.21/`
- `{$REDFISH.PASSWORD}` = `change_me`
- `{$REDFISH.USER}` = `zabbix`

### Dell iDRAC Redfish API

```yaml
Dell IPMI:
  - name: Dell iDRAC by Redfish
    type: api
    macros:
      "{$IDRAC.API.URL}": "https://{HOST.IP}/"
      "{$IDRAC.PASSWORD}": "change_me"
      "{$IDRAC.USER}": "root"
```

### FortiGate HTTP API

```yaml
Fortigate Firewall:
  - name: FortiGate by HTTP
    type: api
    macros:
      "{$FORTIGATE.API.URL}": "https://{HOST.IP}/"
      "{$FORTIGATE.API.KEY}": "change_me"
```

## Güvenlik Notları

⚠️ **ÖNEMLİ:**
- `change_me` değerleri placeholder'dır
- Gerçek şifreleri templates.yml dosyasına yazmayın
- AWX/Tower encrypted variables kullanın
- Ansible Vault kullanın
- Veya Zabbix UI'dan manuel güncelleyin

## Test Senaryoları

### 1. Yeni Host Ekleme (API Template ile)
```bash
# HPE sunucu eklendiğinde:
# - SNMP template eklenir
# - API template eklenir
# - API template için makrolar otomatik eklenir
# - {$REDFISH.API.URL} cihaz IP'si ile doldurulur
```

### 2. Mevcut Host Güncelleme
```bash
# IP değiştiğinde:
# - Host IP'si güncellenir
# - {$REDFISH.API.URL} makrosu otomatik güncellenir
# - Diğer makrolar korunur
```

### 3. Birden Fazla Template
```bash
# Hem SNMP hem API kullanan cihaz:
# - SNMP template → interface type 2 (SNMP)
# - API template → interface type 1 (agent) + makrolar
# - Her ikisi de aynı cihaza atanır
```

## Gelecek Geliştirmeler

Potansiyel iyileştirmeler:
- [ ] Ek değişkenler: `{HOST.NAME}`, `{LOCATION}`, vb.
- [ ] Makro inheritance (device type bazlı)
- [ ] Template-specific macro override
- [ ] Encrypted macro desteği
- [ ] Makro validasyon
- [ ] Bulk macro updates

## Implementasyon Detayları

### Ansible Task Flow

```
1. Load templates.yml
2. Extract template names and types
3. Collect macros from all templates
4. Replace {HOST.IP} with actual IP
5. Format macros for Zabbix API
6. [For update] Get existing macros
7. [For update] Merge with new macros
8. [For update] Check if update needed
9. Create/Update host with macros
10. Report changes
```

### Zabbix API Format

Template'deki format:
```yaml
macros:
  "{$REDFISH.API.URL}": "https://{HOST.IP}/"
```

Zabbix API'ye gönderilen format:
```json
"macros": [
  {
    "macro": "{$REDFISH.API.URL}",
    "value": "https://10.100.1.21/"
  }
]
```

## Referanslar

- [Template Macros Guide](docs/guides/TEMPLATE_MACROS_GUIDE.md)
- [Netbox to Zabbix Guide](docs/guides/NETBOX_TO_ZABBIX_README.md)
- [Design Document](docs/design/DESIGN.md)

## Katkıda Bulunanlar

- Feature implementation: AI Assistant
- Documentation: AI Assistant
- Testing: Pending

## Versiyon

- Feature Version: 1.0
- Implementation Date: 2026-01-19
- Status: Implemented, Testing Pending
