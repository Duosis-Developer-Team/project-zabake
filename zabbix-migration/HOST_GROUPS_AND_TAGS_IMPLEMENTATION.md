# Host Groups ve Tags Implementation

## Özet

Netbox (Loki)'dan Zabbix'e host aktarımında, lokasyon ve cihaz tipi bilgileri **host groups** olarak, diğer metadata bilgileri ise **tags** olarak gönderilecek.

## Host Groups

### Netbox'tan Alınacak Bilgiler:

1. **Lokasyon**: `device['site']['name']` → Örnek: "ISTANBUL", "ANKARA"
2. **Cihaz Tipi**: `device['device_type']['model']` → Örnek: "ThinkSystem SR650", "PowerEdge R730"

### CSV Formatı:

```csv
DEVICE_TYPE,HOST_IP,HOSTNAME,DC_ID,HOST_GROUPS,TEMPLATE_TYPE,MACROS
Lenovo IPMI,10.0.0.1,server-01,DC13,"ISTANBUL,ThinkSystem SR650",snmpv3,{...}
```

**Not**: `HOST_GROUPS` alanı virgülle ayrılmış string olarak gönderilir. Zabbix migration scripti bu grupları otomatik olarak oluşturur.

## Tags

### Netbox'tan Alınacak Tags:

1. **Manufacturer** (Cihaz Markası)
   - Source: `device['device_type']['manufacturer']['name']`
   - Örnek: "LENOVO", "HPE", "DELL"

2. **Device_Type** (Cihaz Tipi)
   - Source: `device['device_type']['model']`
   - Örnek: "ThinkSystem SR650"

3. **Location_Detail** (Lokasyon Detayı)
   - Source: `device.get('location', {}).get('name')` veya `device['site']['name']`
   - Örnek: "Datacenter-1"

4. **City** (Şehir)
   - Source: `device['site']['name']`
   - Örnek: "ISTANBUL"

5. **Customer** (Müşteri - varsa)
   - Source: `device.get('tenant', {}).get('name')`
   - Örnek: "Customer-ABC"

6. **Sorumlu_Ekip** (Sorumlu Ekip - varsa)
   - Source: `device.get('custom_fields', {}).get('Sorumlu_Ekip')`
   - Örnek: "Network Team"

7. **Loki_ID** (Netbox Device ID)
   - Source: `device['id']`
   - Örnek: "12293"

### CSV Formatı:

Tags, CSV'deki `MACROS` alanına JSON formatında yazılır:

```csv
MACROS
"{""Manufacturer"":""LENOVO"",""Device_Type"":""ThinkSystem SR650"",""Location_Detail"":""ISTANBUL"",""City"":""ISTANBUL"",""Loki_ID"":""12293""}"
```

**Not**: CSV'de JSON string olduğu için çift tırnak escape edilmelidir (`""`).

## Zabbix Migration Script Güncellemeleri

### ✅ Yapılan Değişiklikler:

1. **Tags Parsing Eklendi** (`per_record.yml`):
   - MACROS alanındaki JSON otomatik olarak Zabbix tags formatına çevriliyor
   - Format: `[{"tag": "key", "value": "value"}]`

2. **Tags Zabbix API'ye Gönderiliyor**:
   - `host.create` metoduna `tags` parametresi eklendi
   - `host.update` metoduna `tags` parametresi eklendi

### Kod Değişiklikleri:

```yaml
# Tags parsing
- name: Parse tags from macros field
  vars:
    _macros_dict: "{{ zbx_macros | default({}) }}"
  set_fact:
    zbx_tags: >-
      {{ _macros_dict | dict2items | map('dict', tag='key', value='value') | list }}
  when: _macros_dict | length > 0

# Zabbix API'ye tags gönderme
tags: "{{ zbx_tags | default(omit) }}"
```

## Netbox'tan CSV Oluşturma

Netbox'tan CSV oluştururken şu format kullanılmalı:

```python
import json

def extract_host_groups(device):
    """Host groups çıkar"""
    groups = []
    if device.get('site'):
        groups.append(device['site']['name'])
    if device.get('device_type'):
        device_type = device['device_type'].get('model') or device['device_type'].get('display')
        if device_type:
            groups.append(device_type)
    return ','.join(groups) if groups else ''

def extract_tags(device):
    """Tags çıkar"""
    tags = {}
    if device.get('device_type', {}).get('manufacturer'):
        tags['Manufacturer'] = device['device_type']['manufacturer']['name']
    if device.get('device_type'):
        device_type = device['device_type'].get('model') or device['device_type'].get('display')
        if device_type:
            tags['Device_Type'] = device_type
    if device.get('location'):
        tags['Location_Detail'] = device['location']['name']
    elif device.get('site'):
        tags['Location_Detail'] = device['site']['name']
    if device.get('site'):
        tags['City'] = device['site']['name']
    if device.get('tenant'):
        tags['Customer'] = device['tenant']['name']
    custom_fields = device.get('custom_fields', {})
    if custom_fields.get('Sorumlu_Ekip'):
        tags['Sorumlu_Ekip'] = custom_fields['Sorumlu_Ekip']
    if device.get('id'):
        tags['Loki_ID'] = str(device['id'])
    return tags

# CSV satırı oluştur
host_groups = extract_host_groups(device)
tags = extract_tags(device)
tags_json = json.dumps(tags).replace('"', '""')  # CSV için escape

csv_row = {
    'DEVICE_TYPE': device_type,
    'HOST_IP': ip_address,
    'HOSTNAME': device['name'],
    'DC_ID': dc_id,
    'HOST_GROUPS': host_groups,
    'TEMPLATE_TYPE': '',
    'MACROS': tags_json
}
```

## Test

1. Netbox'tan örnek bir device al
2. Host groups ve tags'ı extract et
3. CSV formatına çevir
4. Zabbix migration scripti ile test et
5. Zabbix'te host groups ve tags'ın doğru oluşturulduğunu kontrol et

## Sonraki Adımlar

1. ✅ Host groups ve tags mapping dokümante edildi
2. ✅ Zabbix migration script'e tags desteği eklendi
3. ⏳ Netbox'tan CSV oluşturma scripti yazılmalı
4. ⏳ Test edilmeli ve doğrulanmalı

