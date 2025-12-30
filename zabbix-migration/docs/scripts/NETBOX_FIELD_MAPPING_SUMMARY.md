# Netbox'tan Zabbix'e Field Mapping Özeti

## Host Groups (Zabbix Host Groups)

CSV'deki `HOST_GROUPS` alanına virgülle ayrılmış olarak yazılır.

| Bilgi | Netbox Source | Örnek Değer |
|-------|---------------|------------|
| **Lokasyon** | `device['site']['name']` | "ISTANBUL", "ANKARA" |
| **Cihaz Tipi** | `device['device_type']['model']` | "ThinkSystem SR650", "PowerEdge R730" |

**CSV Formatı:**
```csv
HOST_GROUPS
"ISTANBUL,ThinkSystem SR650"
```

## Tags (Zabbix Host Tags)

CSV'deki `MACROS` alanına JSON formatında yazılır. Zabbix migration scripti bunları otomatik olarak tags formatına çevirir.

| Tag Adı | Netbox Source | Örnek Değer | Not |
|---------|---------------|-------------|-----|
| **Manufacturer** | `device['device_type']['manufacturer']['name']` | "LENOVO", "HPE" | Cihaz markası |
| **Device_Type** | `device['device_type']['model']` | "ThinkSystem SR650" | Cihaz tipi |
| **Location_Detail** | `device.get('location', {}).get('name')` veya `device['site']['name']` | "Datacenter-1" | Lokasyon detayı |
| **City** | `device['site']['name']` | "ISTANBUL" | Şehir |
| **Customer** | `device.get('tenant', {}).get('name')` | "Customer-ABC" | Müşteri (varsa) |
| **Sorumlu_Ekip** | `device.get('custom_fields', {}).get('Sorumlu_Ekip')` | "Network Team" | Sorumlu ekip (varsa) |
| **Loki_ID** | `device['id']` | "12293" | Netbox device ID |

**CSV Formatı:**
```csv
MACROS
"{""Manufacturer"":""LENOVO"",""Device_Type"":""ThinkSystem SR650"",""Location_Detail"":""ISTANBUL"",""City"":""ISTANBUL"",""Loki_ID"":""12293""}"
```

**Not**: CSV'de JSON string olduğu için çift tırnak escape edilmelidir (`""`).

## Python Implementation Örneği

```python
import json

def extract_host_groups(device):
    """Host groups çıkar"""
    groups = []
    
    # Lokasyon
    if device.get('site'):
        groups.append(device['site']['name'])
    
    # Cihaz Tipi
    if device.get('device_type'):
        device_type = device['device_type'].get('model') or device['device_type'].get('display')
        if device_type:
            groups.append(device_type)
    
    return ','.join(groups) if groups else ''


def extract_tags(device):
    """Tags çıkar"""
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
    """CSV satırı oluştur"""
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

## Zabbix API Tags Formatı

Zabbix migration scripti MACROS alanındaki JSON'u otomatik olarak Zabbix tags formatına çevirir:

**Input (CSV MACROS):**
```json
{"Manufacturer":"LENOVO","Device_Type":"ThinkSystem SR650","Loki_ID":"12293"}
```

**Output (Zabbix API tags):**
```json
[
  {"tag": "Manufacturer", "value": "LENOVO"},
  {"tag": "Device_Type", "value": "ThinkSystem SR650"},
  {"tag": "Loki_ID", "value": "12293"}
]
```

## Güncellemeler

✅ **Zabbix Migration Script'e Tags Desteği Eklendi**
- `per_record.yml` dosyasına tags parsing ve gönderme mantığı eklendi
- MACROS alanındaki JSON otomatik olarak Zabbix tags formatına çevriliyor

## Sonraki Adımlar

1. ✅ Tags desteği eklendi
2. ⏳ Netbox'tan CSV oluşturma scripti yazılmalı
3. ⏳ Test edilmeli ve doğrulanmalı


