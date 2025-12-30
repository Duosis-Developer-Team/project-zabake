# Netbox'tan Zabbix'e Veri Mapping Dokümantasyonu

## Genel Bakış

Bu dokümantasyon, Netbox (Loki) API'den alınan verilerin Zabbix'e nasıl aktarılacağını açıklar.

## Host Groups (Zabbix Host Groups)

Host Groups, Zabbix'te host'ları organize etmek için kullanılır. CSV'deki `HOST_GROUPS` alanına yazılır.

### Netbox'tan Alınacak Host Groups:

1. **Lokasyon** (Site)
   - **Netbox Source**: `device['site']['name']`
   - **Örnek**: "ISTANBUL", "ANKARA", "IZMIR"
   - **CSV Field**: `HOST_GROUPS` (virgülle ayrılmış liste)

2. **Cihaz Tipi** (Device Type)
   - **Netbox Source**: `device['device_type']['model']` veya `device['device_type']['display']`
   - **Örnek**: "3PAR", "PowerEdge R730", "ThinkSystem SR650"
   - **CSV Field**: `HOST_GROUPS` (virgülle ayrılmış liste)

### CSV Formatı:

```csv
DEVICE_TYPE,HOST_IP,HOSTNAME,DC_ID,HOST_GROUPS,TEMPLATE_TYPE,MACROS
Lenovo IPMI,10.0.0.1,server-01,DC13,"ISTANBUL,ThinkSystem SR650",snmpv3,{...}
```

**Not**: `HOST_GROUPS` alanı virgülle ayrılmış string olarak gönderilir. Zabbix migration scripti bu grupları otomatik olarak oluşturur.

## Tags (Zabbix Host Tags)

Tags, Zabbix'te host'lara metadata eklemek için kullanılır. CSV'deki `MACROS` alanına JSON formatında yazılır.

### Netbox'tan Alınacak Tags:

1. **Sorumlu Ekip**
   - **Netbox Source**: `device.get('custom_fields', {}).get('Sorumlu_Ekip')` veya `device.get('tenant', {}).get('name')`
   - **Tag Format**: `{"tag": "Sorumlu_Ekip", "value": "Ekip_Adı"}`
   - **Not**: Netbox'ta bu bilgi custom field veya tenant olabilir, discovery ile doğrulanmalı

2. **Cihaz Markası** (Manufacturer)
   - **Netbox Source**: `device['device_type']['manufacturer']['name']`
   - **Örnek**: "LENOVO", "HPE", "DELL", "Inspur"
   - **Tag Format**: `{"tag": "Manufacturer", "value": "LENOVO"}`

3. **Lokasyon Detayı**
   - **Netbox Source**: `device.get('location', {}).get('name')` veya `device['site']['name']`
   - **Örnek**: "Datacenter-1", "Rack-A1"
   - **Tag Format**: `{"tag": "Location_Detail", "value": "Datacenter-1"}`
   - **Not**: Location bilgisi varsa location, yoksa site kullanılır

4. **Cihaz Tipi** (Device Type)
   - **Netbox Source**: `device['device_type']['model']`
   - **Örnek**: "ThinkSystem SR650", "PowerEdge R730"
   - **Tag Format**: `{"tag": "Device_Type", "value": "ThinkSystem SR650"}`

5. **Müşteri** (Tenant - varsa)
   - **Netbox Source**: `device.get('tenant', {}).get('name')`
   - **Örnek**: "Customer-ABC", "Internal"
   - **Tag Format**: `{"tag": "Customer", "value": "Customer-ABC"}`
   - **Not**: Tenant yoksa bu tag gönderilmez

6. **Şehir** (City)
   - **Netbox Source**: `device['site']['name']` veya `device['site'].get('region', {}).get('name')`
   - **Örnek**: "ISTANBUL", "ANKARA"
   - **Tag Format**: `{"tag": "City", "value": "ISTANBUL"}`

7. **Loki ID** (Netbox Device ID)
   - **Netbox Source**: `device['id']`
   - **Örnek**: 12293
   - **Tag Format**: `{"tag": "Loki_ID", "value": "12293"}`

### CSV MACROS Formatı:

Zabbix migration scripti `MACROS` alanını JSON formatında bekler. Tags için şu format kullanılmalı:

```csv
DEVICE_TYPE,HOST_IP,HOSTNAME,DC_ID,HOST_GROUPS,TEMPLATE_TYPE,MACROS
Lenovo IPMI,10.0.0.1,server-01,DC13,"ISTANBUL,ThinkSystem SR650",snmpv3,"{""Manufacturer"":""LENOVO"",""Device_Type"":""ThinkSystem SR650"",""Location_Detail"":""ISTANBUL"",""City"":""ISTANBUL"",""Loki_ID"":""12293""}"
```

**Not**: CSV'de JSON string olduğu için çift tırnak escape edilmelidir (`""`).

## Netbox API Field Mapping

### Device Object Yapısı:

```python
device = {
    'id': 12293,  # Loki ID
    'name': 'server-01',  # Hostname
    'device_type': {
        'id': 592,
        'model': 'ThinkSystem SR650',  # Device Type
        'manufacturer': {
            'id': 2,
            'name': 'LENOVO',  # Manufacturer
            'slug': 'lenovo'
        }
    },
    'device_role': {
        'id': 1,
        'name': 'HOST',  # Device Role
        'slug': 'host'
    },
    'site': {
        'id': 1,
        'name': 'ISTANBUL',  # Site/City
        'slug': 'istanbul'
    },
    'location': {  # Optional
        'id': 5,
        'name': 'Datacenter-1',  # Location Detail
        'slug': 'datacenter-1'
    },
    'tenant': {  # Optional - Customer
        'id': 10,
        'name': 'Customer-ABC',
        'slug': 'customer-abc'
    },
    'primary_ip4': 12345,  # IP Address ID
    'tags': [],  # Existing Netbox tags
    'custom_fields': {
        'Sorumlu_Ekip': 'Network Team',  # Optional - Responsible Team
        # ... other custom fields
    }
}
```

## Implementation Örneği

### Python Kod Örneği:

```python
def extract_host_groups(device):
    """
    Netbox device'tan host groups çıkar
    """
    groups = []
    
    # Lokasyon (Site)
    if device.get('site'):
        groups.append(device['site']['name'])
    
    # Cihaz Tipi
    if device.get('device_type'):
        device_type = device['device_type'].get('model') or device['device_type'].get('display')
        if device_type:
            groups.append(device_type)
    
    return ','.join(groups) if groups else ''


def extract_tags(device):
    """
    Netbox device'tan Zabbix tags çıkar
    """
    tags = {}
    
    # Cihaz Markası
    if device.get('device_type', {}).get('manufacturer'):
        tags['Manufacturer'] = device['device_type']['manufacturer']['name']
    
    # Cihaz Tipi
    if device.get('device_type'):
        device_type = device['device_type'].get('model') or device['device_type'].get('display')
        if device_type:
            tags['Device_Type'] = device_type
    
    # Lokasyon Detayı
    if device.get('location'):
        tags['Location_Detail'] = device['location']['name']
    elif device.get('site'):
        tags['Location_Detail'] = device['site']['name']
    
    # Şehir
    if device.get('site'):
        tags['City'] = device['site']['name']
    
    # Müşteri (varsa)
    if device.get('tenant'):
        tags['Customer'] = device['tenant']['name']
    
    # Sorumlu Ekip (varsa)
    custom_fields = device.get('custom_fields', {})
    if custom_fields.get('Sorumlu_Ekip'):
        tags['Sorumlu_Ekip'] = custom_fields['Sorumlu_Ekip']
    
    # Loki ID
    if device.get('id'):
        tags['Loki_ID'] = str(device['id'])
    
    return tags


def create_csv_row(device, device_type, ip_address, dc_id):
    """
    Netbox device'tan CSV satırı oluştur
    """
    hostname = device.get('name', '')
    host_groups = extract_host_groups(device)
    tags = extract_tags(device)
    
    # Tags'ı JSON string'e çevir (CSV için escape edilmiş)
    tags_json = json.dumps(tags).replace('"', '""')
    
    return {
        'DEVICE_TYPE': device_type,
        'HOST_IP': ip_address,
        'HOSTNAME': hostname,
        'DC_ID': dc_id,
        'HOST_GROUPS': host_groups,
        'TEMPLATE_TYPE': '',  # templates.yml'den belirlenir
        'MACROS': tags_json
    }
```

## Zabbix API'de Tags Kullanımı

Zabbix API'de tags, `host.create` veya `host.update` metodunda `tags` parametresi ile gönderilir:

```json
{
  "jsonrpc": "2.0",
  "method": "host.create",
  "params": {
    "host": "server-01",
    "name": "server-01",
    "tags": [
      {"tag": "Manufacturer", "value": "LENOVO"},
      {"tag": "Device_Type", "value": "ThinkSystem SR650"},
      {"tag": "City", "value": "ISTANBUL"},
      {"tag": "Loki_ID", "value": "12293"}
    ]
  }
}
```

**Not**: Mevcut Zabbix migration scripti tags'ı doğrudan desteklemiyor gibi görünüyor. Tags desteği eklenmeli veya macros olarak gönderilmeli.

## Önerilen Güncellemeler

1. **Zabbix Migration Script'e Tags Desteği Ekle**: 
   - `per_record.yml` dosyasına tags işleme mantığı eklenmeli
   - CSV'den tags okunup Zabbix API'ye gönderilmeli

2. **MACROS vs Tags**:
   - Şu an MACROS alanı Zabbix macros için kullanılıyor
   - Tags için ayrı bir alan veya MACROS içinde tags formatı kullanılabilir
   - Veya Zabbix API'de tags direkt olarak gönderilebilir

3. **Discovery Script Güncellemesi**:
   - Sorumlu ekip bilgisinin Netbox'ta nerede olduğunu keşfet
   - Location detayının tam olarak nereden alınacağını belirle
   - Tenant bilgisinin varlığını kontrol et

## Sonraki Adımlar

1. Netbox'tan CSV oluşturma scripti yazılmalı (host groups ve tags dahil)
2. Zabbix migration script'e tags desteği eklenmeli
3. Test edilmeli ve doğrulanmalı


