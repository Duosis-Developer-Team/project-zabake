# Netbox API Mapping Analysis Report

## Özet

Netbox API discovery scripti başarıyla çalıştırıldı ve aşağıdaki veriler toplandı:

- **Toplam Device**: 1995
- **Device Roles**: 50 (HOST dahil)
- **Manufacturers**: 86 (LENOVO, HPE, DELL, Inspur, Supermicro dahil)
- **Device Types**: 594
- **Sites**: 7 (ISTANBUL, ANKARA, IZMIR, vb.)
- **Custom Fields**: 55
- **Tags**: 85

## CSV Koşullarından Netbox Mapping

### 1. Device Role Koşulu

**CSV Koşulu**: `Device Role: HOST`

**Netbox Mapping**:
```python
device['device_role']['name'] == "HOST"
# veya
device['device_role']['slug'] == "host"
```

**Netbox'ta Bulunan Device Roles**:
- HOST (slug: host) ✓
- ESXI KLASIK HOST
- ESXI NUTANIX HOST
- AHV NUTANIX HOST
- HYPER-V KLASIK HOST
- IBM POWER HOST
- vb.

### 2. Manufacturer/Üretici Koşulu

**CSV Koşulları**:
- Üretici: Lenovo
- Üretici: Inspur
- Üretici: HPE
- Üretici: DELL

**Netbox Mapping**:
```python
manufacturer_name = device['device_type']['manufacturer']['name']
# Örnek değerler: "LENOVO", "HPE", "DELL", "Inspur"
```

**Netbox'ta Bulunan Manufacturers**:
- LENOVO (slug: lenovo) ✓
- HPE (slug: hpe) ✓
- DELL (slug: dell) ✓
- Inspur (slug: inspur) ✓
- Supermicro (slug: supermicro) ✓

**Not**: Netbox'ta manufacturer isimleri büyük harfle olabilir, case-insensitive karşılaştırma yapılmalı.

### 3. Device Type Suffix Koşulu

**CSV Koşulları**:
- Type: M6 (suffix) → Inspur M6
- Type: M5 (suffix) → Inspur M5

**Netbox Mapping**:
```python
device_type_model = device['device_type']['model']
# Suffix çıkarımı: Model'in sonundaki M6, M5 gibi suffix'leri kontrol et
# Örnek: "Inspur M6", "Inspur M5" gibi modellerde suffix var
```

**Netbox'ta Bulunan Device Types Örnekleri**:
- Inspur ile başlayan modeller kontrol edilmeli
- Model isimlerinde "M6", "M5" gibi suffix'ler aranmalı

### 4. Hostname Mapping

**CSV Field**: `HOSTNAME`

**Netbox Mapping**:
```python
hostname = device['name']
```

### 5. IP Address Mapping

**CSV Field**: `HOST_IP`

**Netbox Mapping**:
```python
primary_ip = device.get('primary_ip4')  # ID döner
# IP adresini almak için:
# 1. primary_ip4 bir ID ise, /api/ipam/ip-addresses/{id}/ endpoint'inden al
# 2. Veya device.primary_ip string ise, direkt kullan
# 3. CIDR formatında olabilir (10.0.0.1/24), IP'yi extract et
```

**Not**: Netbox'ta IP adresleri CIDR formatında olabilir, sadece IP kısmını almak gerekebilir.

### 6. DC_ID Mapping

**CSV Field**: `DC_ID`

**Netbox Mapping**:
```python
site_name = device['site']['name']  # Örnek: "ISTANBUL", "ANKARA"
site_slug = device['site']['slug']  # Örnek: "istanbul", "ankara"
# DC_ID mapping için site name veya slug kullanılabilir
```

**Netbox'ta Bulunan Sites**:
- ISTANBUL (slug: istanbul)
- ANKARA (slug: ankara)
- IZMIR (slug: izmir)
- ALMANYA (slug: frankfurt)
- ANKARA (slug: ankara)
- AZERBAYCAN (slug: azerbaycan)
- INGILTERE (slug: ingiltere)
- OZBEKISTAN (slug: ozbekistan)

### 7. Tags Mapping

**CSV Field**: `TAGS` (Zabbix macro formatında)

**Netbox Mapping**:
```python
tags = device.get('tags', [])
# Her tag bir dict: {'id': 1, 'name': 'TAG_NAME', 'slug': 'tag-name'}
# Zabbix macro formatına çevir: {$TAG_NAME:value}
```

**Netbox'ta Bulunan Tags Örnekleri**:
- DC13-G1-CLS
- ESXI NUTANIX
- NUTANIX
- vb.

### 8. Notes/Custom Fields Mapping

**CSV Field**: `NOTES`

**Netbox Mapping**:
```python
# Seçenek 1: Custom Fields
custom_fields = device.get('custom_fields', {})
notes = custom_fields.get('Notes')  # Eğer 'Notes' custom field varsa

# Seçenek 2: Comments
comments = device.get('comments', '')
```

**Netbox'ta Bulunan Custom Fields**:
- 55 custom field var
- Notes için uygun bir custom field olabilir veya `comments` field'ı kullanılabilir

## Template Matching Logic

### CSV Template Conditions Örnekleri:

1. **Lenovo IPMI**:
   - Condition: `Device Role: HOST, Üretici: Lenovo`
   - Template: `Lenovo ICT XCC Monitoring`
   - Type: `snmpv3`

2. **Inspur M6**:
   - Condition: `Device Role: HOST, Üretici: Inspur, Type: M6 (suffix)`
   - Template: `Lenovo Inspur M6 Template`
   - Type: `snmpv2`

3. **Inspur M5**:
   - Condition: `Device Role: HOST, Üretici: Inspur, Type: M5 (suffix)`
   - Template: `Server Inspur BMC All Items 4 Zabbix5.0`
   - Type: `snmpv2`

4. **HPE IPMI**:
   - Condition: `Device Role: HOST, Üretici: HPE`
   - Template: `HPE ProLiant DL380 SNMP`
   - Type: `snmpv2`

5. **Dell IPMI**:
   - Condition: `Device Role: HOST, Üretici: DELL`
   - Template: `Dell iDRAC SNMP`
   - Type: `snmpv2`

### Netbox'tan Template Belirleme Algoritması:

```python
def determine_device_type(device):
    """
    Device'tan DEVICE_TYPE belirleme mantığı
    """
    role = device['device_role']['name']
    manufacturer = device['device_type']['manufacturer']['name'].upper()
    model = device['device_type']['model']
    
    # Koşul 1: Device Role HOST olmalı
    if role != "HOST":
        return None
    
    # Koşul 2: Manufacturer kontrolü
    if manufacturer == "LENOVO":
        # Lenovo IPMI veya Lenovo ICT kontrolü
        if "ICT" in model.upper() or "XCC" in model.upper():
            return "Lenovo ICT"
        else:
            return "Lenovo IPMI"
    
    elif manufacturer == "INSPUR":
        # M6 veya M5 suffix kontrolü
        if model.upper().endswith("M6") or " M6" in model.upper():
            return "Inspur M6"
        elif model.upper().endswith("M5") or " M5" in model.upper():
            return "Inspur M5"
    
    elif manufacturer == "HPE":
        # HPE IPMI veya HP ILO kontrolü
        if "ILO" in model.upper() or "ILO" in device.get('name', '').upper():
            return "HP ILO"
        else:
            return "HPE IPMI"
    
    elif manufacturer == "DELL":
        return "Dell IPMI"
    
    # Diğer manufacturer'lar için benzer mantık...
    
    return None
```

## Önerilen Implementation

### 1. Netbox API Query Örneği

```python
# HOST role'üne sahip tüm device'ları çek
devices = session.get(
    f"{api_url}/dcim/devices/",
    params={
        'role': 'host',  # slug kullan
        'limit': 1000,
        'offset': 0
    }
).json()

# Her device için:
for device in devices['results']:
    # Manufacturer kontrolü
    manufacturer = device['device_type']['manufacturer']['name']
    
    # Device type belirleme
    device_type = determine_device_type(device)
    
    # IP adresi al
    ip_address = get_primary_ip(device)
    
    # CSV satırı oluştur
    csv_row = create_csv_row(device, device_type, ip_address)
```

### 2. IP Address Extraction

```python
def get_primary_ip(device):
    """
    Device'tan primary IP adresini çıkar
    """
    primary_ip_id = device.get('primary_ip4')
    if not primary_ip_id:
        return None
    
    # Eğer ID ise, IP adresini al
    if isinstance(primary_ip_id, int):
        ip_response = session.get(f"{api_url}/ipam/ip-addresses/{primary_ip_id}/")
        ip_data = ip_response.json()
        address = ip_data.get('address', '')
        # CIDR'den IP'yi çıkar (10.0.0.1/24 -> 10.0.0.1)
        return address.split('/')[0] if '/' in address else address
    
    # Eğer string ise direkt kullan
    return primary_ip_id.split('/')[0] if '/' in primary_ip_id else primary_ip_id
```

### 3. Site to DC_ID Mapping

```python
def map_site_to_dc_id(site_name):
    """
    Netbox site name'ini DC_ID'ye map et
    """
    site_mapping = {
        'ISTANBUL': 'DC13',  # Örnek mapping
        'ANKARA': 'DC11',
        'IZMIR': 'DC12',
        # ... diğer mapping'ler
    }
    return site_mapping.get(site_name.upper(), site_name)
```

## Sonuç ve Öneriler

1. **Device Role Filtresi**: Sadece `HOST` role'üne sahip device'ları çek
2. **Manufacturer Normalizasyonu**: Case-insensitive karşılaştırma yap
3. **Model Suffix Kontrolü**: Inspur M6/M5 gibi suffix'leri model isminden çıkar
4. **IP Address Handling**: CIDR formatından IP'yi extract et
5. **Site Mapping**: Site name'lerini DC_ID'ye map et
6. **Template Matching**: templates.csv'deki koşullara göre template belirle
7. **Error Handling**: Eksik veriler için uygun default değerler kullan

## Sonraki Adımlar

1. Netbox'tan CSV oluşturma scripti yazılmalı
2. Template matching logic implement edilmeli
3. Site to DC_ID mapping dosyası oluşturulmalı
4. Test edilmeli ve doğrulanmalı


