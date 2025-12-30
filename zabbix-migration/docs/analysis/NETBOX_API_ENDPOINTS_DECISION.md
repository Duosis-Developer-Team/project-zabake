# Netbox API Endpoint'leri ve Veri Yapısı - Kesin Kararlar

## Analiz Tarihi
2025-01-XX - Gerçek Netbox ortamı analizi tamamlandı

## Netbox URL ve Token
- **URL**: `https://loki.bulutistan.com/`
- **API Base**: `https://loki.bulutistan.com/api/`

## 1. Ana Endpoint: Devices

### Endpoint
```
GET /api/dcim/devices/
```

### Kullanılacak Parametreler
- `limit`: Sayfalama için (varsayılan: 1000)
- `role_id`: Device role ID ile filtreleme (opsiyonel)
- Expansion: Related object'ler otomatik expand edilir

### Device Objesi Yapısı

#### Temel Alanlar
```json
{
  "id": 10805,
  "name": "10.6.2.89",
  "device_type": {
    "id": 123,
    "model": "ThinkSystem SR650",
    "manufacturer": {
      "id": 5,
      "name": "LENOVO"
    }
  },
  "role": {
    "id": 1,
    "name": "HOST"
  },
  "site": {
    "id": 4,
    "name": "ISTANBUL"
  },
  "primary_ip4": {
    "id": 12345,
    "address": "10.6.2.89/24"
  }
}
```

#### Rack Bilgisi
**Kaynak**: `device['rack']`
- **Tip**: Dict veya None
- **Yapı**:
  ```json
  {
    "id": 2,
    "name": "5002",
    "display": "5002",
    "rack_type": null,  // Genellikle null
    "role": {
      "id": 1,
      "name": "NETWORK RACK",
      "slug": "network-rack"
    }
  }
  ```
- **Kullanılacak Alanlar**:
  - `rack['name']` → Rack Name tag
  - `rack['role']['name']` → Rack Type tag (rack_type null olduğu için role kullanılacak)

#### Cluster Bilgisi
**Kaynak**: `device['cluster']`
- **Tip**: Dict veya None
- **Yapı**:
  ```json
  {
    "id": 88,
    "name": "DC13-G3-CLS-VEEAM",
    "display": "DC13-G3-CLS-VEEAM",
    "description": ""
  }
  ```
- **Kullanılacak Alan**: `cluster['name']` → Cluster tag

#### Location Bilgisi
**Kaynak**: `device['location']`
- **Tip**: Dict veya None
- **Yapı**:
  ```json
  {
    "id": 7,
    "name": "DH5",
    "display": "DH5",
    "slug": "dh5",
    "description": "DATA HALL 5",
    "parent": {
      "id": 3,
      "name": "DC13"
    }
  }
  ```
- **Kullanılacak Alanlar**:
  - `location['name']` → Location Detail tag
  - `location['parent']['name']` → DC_ID için (eğer parent varsa)
  - `location['description']` → Hall bilgisi olabilir (örnek: "DATA HALL 5")

#### Hall Bilgisi
**Kaynak**: `device['location']['description']` veya `device['location']['name']`
- **Analiz Sonucu**: Location description'da "DATA HALL X" formatı var
- **Kullanılacak**: `location['description']` veya `location['name']` → Hall tag

#### Custom Fields
**Kaynak**: `device['custom_fields']`
- **Tip**: Dict
- **Kurulum Tarihi**: `custom_fields['Kurulum_Tarihi']`
  - **Tip**: Date (format: "YYYY-MM-DD")
  - **Örnek**: "2023-01-15"

#### Tags (Loki Tags)
**Kaynak**: `device['tags']`
- **Tip**: Array of objects
- **Yapı**:
  ```json
  [
    {
      "id": 69,
      "name": "ESXI NUTANIX",
      "slug": "esxi-nutanix",
      "color": "795548"
    }
  ]
  ```
- **Kullanılacak**: Her tag'in `name` alanı → Zabbix tag olarak eklenecek

## 2. Rack Detay Endpoint (Gerekirse)

### Endpoint
```
GET /api/dcim/racks/{rack_id}/
```

### Kullanım Senaryosu
- Device'ta rack sadece ID olarak gelirse (int)
- Rack detaylarına ihtiyaç varsa

### Rack Objesi Yapısı
```json
{
  "id": 203,
  "name": "522",
  "rack_type": null,
  "role": {
    "id": 1,
    "name": "NETWORK RACK",
    "slug": "network-rack"
  },
  "location": {
    "id": 17,
    "name": "ICT11"
  },
  "custom_fields": {
    "Kabin_Enerji": "6",
    "kabin_pdu_a_IP": "10.70.19.21",
    "kabin_pdu_b_IP": "10.70.19.22"
  }
}
```

## 3. Cluster Detay Endpoint (Gerekirse)

### Endpoint
```
GET /api/virtualization/clusters/{cluster_id}/
```

### Kullanım Senaryosu
- Device'ta cluster sadece ID olarak gelirse (int)
- Cluster detaylarına ihtiyaç varsa

## 4. Location Detay Endpoint (Gerekirse)

### Endpoint
```
GET /api/dcim/locations/{location_id}/
```

### Kullanım Senaryosu
- Device'ta location sadece ID olarak gelirse (int)
- Parent location bilgisine ihtiyaç varsa

### Location Objesi Yapısı
```json
{
  "id": 18,
  "name": "AZ11",
  "slug": "az11",
  "site": {
    "id": 5,
    "name": "AZERBAYCAN"
  },
  "parent": null,
  "description": "AzinTelecom DC",
  "tags": [
    {
      "id": 69,
      "name": "ESXI NUTANIX"
    }
  ],
  "custom_fields": {}
}
```

## 5. Custom Fields Endpoint

### Endpoint
```
GET /api/extras/custom-fields/?content_types=dcim.device
```

### Kullanım
- Tüm custom field'ları listelemek için
- Field adlarını doğrulamak için

### Bulunan Custom Fields (İlgili Olanlar)
- `Kurulum_Tarihi` (date) - ✅ Kullanılacak
- `Sahiplik` (text) - Mevcut tag'lerde var
- `Sorumlu_Ekip` - Mevcut tag'lerde var (ancak analizde görünmedi, kontrol edilmeli)

## 6. Kesin Kararlar ve Mapping

### 6.1 Device Endpoint Kullanımı

**Endpoint**: `GET /api/dcim/devices/`

**Parametreler**:
```python
params = {
    'limit': 1000,  # Sayfalama
    # role_id ile filtreleme yapılabilir ama API'de role name ile değil ID ile çalışıyor
}
```

**Response Expansion**:
- Netbox API otomatik olarak related object'leri expand ediyor
- `rack`, `cluster`, `location` objeleri genellikle dict olarak geliyor
- Bazen sadece ID olarak gelebilir, bu durumda ayrı endpoint çağrısı gerekir

### 6.2 Field Mapping - Kesin Kararlar

| Zabbix Tag/Field | Netbox Source | Endpoint | Notlar |
|-----------------|---------------|----------|--------|
| **Rack_Name** | `device['rack']['name']` | `/api/dcim/devices/` | Rack dict olarak geliyor |
| **Rack_Type** | `device['rack']['role']['name']` | `/api/dcim/devices/` | rack_type null, role kullanılacak |
| **Cluster** | `device['cluster']['name']` | `/api/dcim/devices/` | Cluster dict olarak geliyor veya None |
| **Hall** | `device['location']['description']` veya `device['location']['name']` | `/api/dcim/devices/` | Description'da "DATA HALL X" formatı var |
| **Kurulum_Tarihi** | `device['custom_fields']['Kurulum_Tarihi']` | `/api/dcim/devices/` | Date format: "YYYY-MM-DD" |
| **Loki_Tags** | `device['tags']` (array) | `/api/dcim/devices/` | Her tag['name'] → Zabbix tag |
| **Lokasyon** | `device['location']['parent']['name']` veya `device['site']['name']` | `/api/dcim/devices/` | Parent varsa parent, yoksa site |
| **IP** | `device['primary_ip4']['address']` | `/api/dcim/devices/` | CIDR formatından IP extract edilmeli |
| **Hostname** | `device['name']` | `/api/dcim/devices/` | Direct mapping |

### 6.3 Fallback Senaryoları

#### Rack Sadece ID Olarak Gelirse
```python
if isinstance(device.get('rack'), int):
    rack_id = device['rack']
    rack = fetch_rack(rack_id)  # GET /api/dcim/racks/{rack_id}/
else:
    rack = device.get('rack')
```

#### Cluster Sadece ID Olarak Gelirse
```python
if isinstance(device.get('cluster'), int):
    cluster_id = device['cluster']
    cluster = fetch_cluster(cluster_id)  # GET /api/virtualization/clusters/{cluster_id}/
else:
    cluster = device.get('cluster')
```

#### Location Sadece ID Olarak Gelirse
```python
if isinstance(device.get('location'), int):
    location_id = device['location']
    location = fetch_location(location_id)  # GET /api/dcim/locations/{location_id}/
else:
    location = device.get('location')
```

## 7. Performans Optimizasyonu

### 7.1 Toplu Veri Çekme
- Device endpoint'inden tüm device'ları çek (pagination ile)
- Related object'ler (rack, cluster, location) genellikle expand edilmiş geliyor
- Ek endpoint çağrısı sadece gerekirse yapılmalı

### 7.2 Caching Stratejisi
- Rack, cluster, location objeleri cache'lenebilir
- Custom field'lar bir kez çekilip cache'lenebilir

## 8. Örnek Device Response (Gerçek Veri)

```json
{
  "id": 10805,
  "name": "10.6.2.89",
  "device_type": {
    "id": 123,
    "model": "ThinkSystem SR650",
    "manufacturer": {
      "id": 5,
      "name": "LENOVO"
    }
  },
  "role": {
    "id": 1,
    "name": "HOST"
  },
  "site": {
    "id": 4,
    "name": "ISTANBUL"
  },
  "location": {
    "id": 1,
    "name": "DC11",
    "parent": null,
    "description": "Premier DC"
  },
  "rack": {
    "id": 2,
    "name": "5002",
    "role": {
      "id": 1,
      "name": "NETWORK RACK"
    }
  },
  "cluster": null,
  "primary_ip4": {
    "id": 12345,
    "address": "10.6.2.89/24"
  },
  "tags": [
    {
      "id": 69,
      "name": "ESXI NUTANIX"
    }
  ],
  "custom_fields": {
    "Kurulum_Tarihi": "2023-01-15",
    "Sahiplik": "Infrastructure Team"
  }
}
```

## 9. Sonuç ve Uygulama

### Kullanılacak Endpoint'ler
1. **Ana Endpoint**: `GET /api/dcim/devices/` (pagination ile)
2. **Fallback Endpoint'ler** (gerekirse):
   - `GET /api/dcim/racks/{rack_id}/`
   - `GET /api/virtualization/clusters/{cluster_id}/`
   - `GET /api/dcim/locations/{location_id}/`

### Veri Çıkarma Stratejisi
1. Device endpoint'inden tüm device'ları çek
2. Her device için:
   - Rack: `device['rack']['name']` ve `device['rack']['role']['name']`
   - Cluster: `device['cluster']['name']` (varsa)
   - Hall: `device['location']['description']` veya `device['location']['name']`
   - Kurulum Tarihi: `device['custom_fields']['Kurulum_Tarihi']`
   - Loki Tags: `device['tags']` array'inden `name` alanları
3. Fallback: Eğer rack/cluster/location sadece ID ise, ayrı endpoint çağrısı yap

### Zabbix Tag Mapping
```python
tags = {
    "Rack_Name": device['rack']['name'] if device.get('rack') else None,
    "Rack_Type": device['rack']['role']['name'] if device.get('rack', {}).get('role') else None,
    "Cluster": device['cluster']['name'] if device.get('cluster') else None,
    "Hall": device['location']['description'] or device['location']['name'] if device.get('location') else None,
    "Kurulum_Tarihi": device['custom_fields'].get('Kurulum_Tarihi'),
    # Loki tags: device['tags'] array'inden her tag['name'] ayrı tag olarak
}
```

## 10. Notlar

- ✅ Rack type için `rack['role']['name']` kullanılacak (rack_type genellikle null)
- ✅ Cluster bazı device'larda None olabilir
- ✅ Location description'da "DATA HALL X" formatı var, bu Hall bilgisi olarak kullanılabilir
- ✅ Custom field `Kurulum_Tarihi` date formatında
- ✅ Tags array'inde her tag'in name'i Zabbix tag olarak eklenecek
- ⚠️ Related object'ler bazen sadece ID olarak gelebilir, fallback mekanizması gerekli

