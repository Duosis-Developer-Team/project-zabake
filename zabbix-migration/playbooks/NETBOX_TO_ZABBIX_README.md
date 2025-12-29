# Netbox to Zabbix Migration Playbook

Bu playbook, Netbox (Loki) API'den device'ları çekerek, template mapping'lere göre Zabbix'e aktarır.

## Özellikler

- ✅ Netbox API'den device'ları otomatik çeker
- ✅ Template mapping koşullarına göre filtreler
- ✅ Host groups ve tags'ı otomatik extract eder
- ✅ Zabbix'e direkt gönderir (CSV aracılığı olmadan)
- ✅ Device limit desteği (kaç adet cihaz gönderileceği belirlenebilir)
- ✅ Filtreleme desteği (role, site, manufacturer)

## Gereksinimler

- Ansible 2.9+
- Python 3.6+
- `requests` kütüphanesi
- Netbox API erişimi
- Zabbix API erişimi

## Kullanım

### Temel Kullanım

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com" \
  -e "netbox_token=YOUR_NETBOX_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Device Limit ile Kullanım

Sadece ilk 10 device'ı göndermek için:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com" \
  -e "netbox_token=YOUR_NETBOX_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "device_limit=10"
```

### Filtreleme ile Kullanım

Belirli bir site'den device'ları göndermek için:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com" \
  -e "netbox_token=YOUR_NETBOX_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "site_filter=ISTANBUL"
```

Belirli bir manufacturer'dan device'ları göndermek için:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com" \
  -e "netbox_token=YOUR_NETBOX_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "manufacturer_filter=LENOVO"
```

### Tüm Parametreler

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com" \
  -e "netbox_token=YOUR_NETBOX_TOKEN" \
  -e "netbox_verify_ssl=false" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "zabbix_validate_certs=false" \
  -e "device_limit=0" \
  -e "device_role_filter=HOST" \
  -e "site_filter=" \
  -e "manufacturer_filter="
```

## Parametreler

### Zorunlu Parametreler

| Parametre | Açıklama | Örnek |
|-----------|----------|-------|
| `netbox_url` | Netbox base URL | `https://loki.bulutistan.com` |
| `netbox_token` | Netbox API token | `13201880f324d54b1edb7351175a6fe2d4d833e9` |
| `zabbix_url` | Zabbix API URL | `http://zabbix.example.com/zabbix/api_jsonrpc.php` |
| `zabbix_user` | Zabbix kullanıcı adı | `admin` |
| `zabbix_password` | Zabbix şifresi | `password` |

### Opsiyonel Parametreler

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `device_limit` | `0` | Kaç adet device gönderileceği (0 = tümü) |
| `device_role_filter` | `HOST` | Device role filtresi |
| `site_filter` | `` | Site filtresi (boş = tüm siteler) |
| `manufacturer_filter` | `` | Manufacturer filtresi (boş = tüm manufacturer'lar) |
| `netbox_verify_ssl` | `false` | Netbox SSL doğrulama |
| `zabbix_validate_certs` | `false` | Zabbix SSL doğrulama |

## Device Type Mapping

Playbook, Netbox device'larını template mapping'lere göre otomatik olarak eşleştirir:

- **Lenovo IPMI**: Device role HOST, Manufacturer LENOVO
- **Lenovo ICT**: Device role HOST, Manufacturer LENOVO, Model'de ICT veya XCC var
- **Inspur M6**: Device role HOST, Manufacturer INSPUR, Model'de M6 var
- **Inspur M5**: Device role HOST, Manufacturer INSPUR, Model'de M5 var
- **HPE IPMI**: Device role HOST, Manufacturer HPE
- **HP ILO**: Device role HOST, Manufacturer HPE, Model veya name'de ILO var
- **Dell IPMI**: Device role HOST, Manufacturer DELL
- Diğer device type'lar: Manufacturer ve model'e göre templates.yml'deki mapping'lere göre eşleştirilir

## Host Groups

Her device için otomatik olarak şu host groups oluşturulur:

1. **Lokasyon**: `device['site']['name']` (örn: "ISTANBUL")
2. **Cihaz Tipi**: `device['device_type']['model']` (örn: "ThinkSystem SR650")

## Tags

Her device için otomatik olarak şu tags oluşturulur:

1. **Manufacturer**: Cihaz markası
2. **Device_Type**: Cihaz tipi
3. **Location_Detail**: Lokasyon detayı
4. **City**: Şehir
5. **Customer**: Müşteri (varsa)
6. **Sorumlu_Ekip**: Sorumlu ekip (varsa)
7. **Loki_ID**: Netbox device ID

## Örnek Çıktı

```
PLAY [Netbox to Zabbix Migration] ********************************************

TASK [netbox_to_zabbix : Load template mappings] ******************************
ok: [localhost]

TASK [netbox_to_zabbix : Fetch devices from Netbox API] ***********************
ok: [localhost]

TASK [netbox_to_zabbix : Display device count] *********************************
ok: [localhost] => {
    "msg": "Found 25 devices to process (limit: 10)"
}

TASK [netbox_to_zabbix : Process each device] *********************************
included: .../process_device.yml for server-01
included: .../process_device.yml for server-02
...
```

## Hata Ayıklama

Playbook'u verbose modda çalıştırarak daha fazla bilgi alabilirsiniz:

```bash
ansible-playbook netbox_to_zabbix.yaml -vvv ...
```

## Notlar

- Device'ların `primary_ip4` alanı dolu olması gerekir
- Device role'ü "HOST" olmalıdır (varsayılan filtre)
- Template mapping'lerde eşleşmeyen device'lar atlanır
- Zabbix'te host groups otomatik oluşturulur
- Tags Zabbix API'ye direkt gönderilir


