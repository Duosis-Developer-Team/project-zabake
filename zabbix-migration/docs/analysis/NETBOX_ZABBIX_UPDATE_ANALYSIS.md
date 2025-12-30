# Netbox-Zabbix Güncelleme Analizi ve Geliştirme Planı

## Analiz Özeti

Bu dokümantasyon, Netbox entegrasyonu ile Zabbix güncelleme özelliklerinin analizini ve geliştirme planını içerir.

## 1. Netbox API'den Alınacak Yeni Alanlar

### 1.1 Rack Bilgileri
- **Rack Name**: `device['rack']['name']` veya `device['rack']` (ID ise API'den çekilmeli)
- **Rack Type**: `device['rack']['type']['name']` veya rack objesinden `type` alanı
- **API Endpoint**: `/api/dcim/racks/{rack_id}/` (rack ID ise)
- **Not**: Rack objesi expanded olabilir veya sadece ID olabilir

### 1.2 Cluster Bilgisi
- **Cluster Name**: `device['cluster']['name']` veya `device['cluster']` (ID ise API'den çekilmeli)
- **API Endpoint**: `/api/virtualization/clusters/{cluster_id}/` (cluster ID ise)
- **Not**: Cluster objesi expanded olabilir veya sadece ID olabilir

### 1.3 Hall Bilgisi
- **Hall**: Location objesi içinde `custom_fields` veya `site` içinde olabilir
- **Olası Kaynaklar**:
  - `device['location']['custom_fields']['Hall']`
  - `device['site']['custom_fields']['Hall']`
  - `device['location']['name']` (eğer hall location name ise)
- **Not**: Discovery ile doğrulanmalı

### 1.4 Custom Field - Kurulum Tarihi
- **Kurulum Tarihi**: `device['custom_fields']['Kurulum_Tarihi']` veya benzeri field adı
- **Olası Field Adları**:
  - `Kurulum_Tarihi`
  - `Kurulum Tarihi`
  - `Installation_Date`
  - `installation_date`
- **Not**: Discovery ile doğrulanmalı, field adı ortamdan ortama değişebilir

### 1.5 Loki Tags
- **Loki Tags**: `device['tags']` (array of tag objects)
- **Format**: Her tag bir obje: `{"id": 1, "name": "tag-name", "slug": "tag-slug", ...}`
- **Zabbix'e Aktarım**: Tag name'leri Zabbix tag'leri olarak eklenmeli
- **Not**: Mevcut tags ile birleştirilmeli (üzerine yazılmamalı)

## 2. Zabbix API'den Alınacak Veriler

### 2.1 Tüm Host'ları Çekme
```json
{
  "jsonrpc": "2.0",
  "method": "host.get",
  "params": {
    "output": ["hostid", "host", "name"],
    "selectInterfaces": ["interfaceid", "ip", "dns", "port"],
    "selectTags": ["tag", "value"],
    "selectGroups": ["groupid", "name"]
  },
  "auth": "{{ zabbix_auth }}",
  "id": 1
}
```

### 2.2 Host Mapping Stratejisi
- **Loki_ID Tag'ine Göre**: Her host'un tags'lerinden `Loki_ID` tag'ini bul
- **Mapping Yapısı**: `{loki_id: {hostid, host, name, interfaces, tags, ...}}`
- **Hostname'e Göre Fallback**: Loki_ID yoksa hostname ile eşleştir

## 3. Güncelleme Stratejisi

### 3.1 Sürekli Güncellenecek Alanlar
Bu alanlar hem create hem update sırasında güncellenir:
- **Lokasyon (DC_ID)**: Proxy group assignment için
- **IP (HOST_IP)**: Interface IP adresi
- **Hostname (HOSTNAME)**: Host adı ve display name

### 3.2 Sadece Create Sırasında Güncellenecek Alanlar
Bu alanlar sadece yeni host oluşturulurken set edilir, update sırasında değiştirilmez:
- **Templates**: Template linking
- **Host Groups**: Host group assignment (DEVICE_TYPE + HOST_GROUPS)
- **Tags (Metadata)**: Rack, cluster, hall, kurulum tarihi, loki tags
- **Proxy/Proxy Group**: İlk atama (update sırasında değiştirilmez)

### 3.3 Tags Güncelleme Stratejisi
- **Create**: Tüm tags eklenir
- **Update**: Sadece sürekli güncellenecek alanların tags'leri güncellenir (Lokasyon, IP, Hostname ile ilgili)
- **Metadata Tags**: Rack, cluster, hall, kurulum tarihi, loki tags sadece create sırasında eklenir

## 4. İki Senaryo Implementasyonu

### Senaryo 1: Host Yok (Yeni Cihaz)
**Koşul**: Netbox device ID'si ile Zabbix'teki `Loki_ID` tag'i eşleşmiyor veya hostname ile eşleşen host yok

**İşlemler**:
1. Host oluştur (tüm alanlar ile)
2. Templates link et
3. Host groups assign et
4. Tüm tags ekle (metadata dahil)
5. Proxy/Proxy group assign et
6. Interface oluştur

### Senaryo 2: Host Var Ama Uyumsuz (Mevcut Cihaz)
**Koşul**: Netbox device ID'si ile Zabbix'teki `Loki_ID` tag'i eşleşiyor veya hostname ile eşleşen host var

**İşlemler**:
1. Host'u güncelle (sadece sürekli güncellenecek alanlar):
   - Lokasyon (DC_ID) → Proxy group güncelleme
   - IP (HOST_IP) → Interface IP güncelleme
   - Hostname (HOSTNAME) → Host adı güncelleme
2. Metadata tags güncellenmez (rack, cluster, hall, kurulum tarihi, loki tags)
3. Templates, host groups, proxy assignment değiştirilmez

## 5. Performans Optimizasyonu

### 5.1 Toplu Veri Çekme
Playbook başında:
1. **Netbox'tan**: Tüm matching device'ları çek (zaten mevcut)
2. **Zabbix'ten**: Tüm host'ları çek (yeni eklenecek)
3. **Mapping Oluştur**: Loki_ID → Zabbix host mapping

### 5.2 API Çağrı Optimizasyonu
- Her device için ayrı API çağrısı yapılmamalı
- Toplu işlemler tercih edilmeli
- Cache mekanizması kullanılmalı

## 6. Netbox API Field Mapping

### 6.1 Mevcut Alanlar
| Zabbix Alanı | Netbox Source | Not |
|--------------|---------------|-----|
| HOSTNAME | `device['name']` | Direct mapping |
| HOST_IP | `device['primary_ip4']` | IP extraction needed |
| DC_ID | `device['location']['parent']['name']` veya `device['site']['name']` | Location hierarchy |
| DEVICE_TYPE | Mapping'den belirlenir | Manufacturer + Model |
| HOST_GROUPS | `device['site']['name']` + `device['device_type']['model']` | Comma-separated |

### 6.2 Yeni Alanlar (Tags)
| Zabbix Tag | Netbox Source | Not |
|------------|---------------|-----|
| Manufacturer | `device['device_type']['manufacturer']['name']` | Mevcut |
| Device_Type | `device['device_type']['model']` | Mevcut |
| Location_Detail | `device['location']['name']` veya `device['site']['name']` | Mevcut |
| City | `device['site']['name']` | Mevcut |
| Contact | `device['tenant']['name']` | Mevcut |
| Sorumlu_Ekip | `device['custom_fields']['Sorumlu_Ekip']` | Mevcut |
| Loki_ID | `device['id']` | Mevcut |
| **Rack_Name** | `device['rack']['name']` | **YENİ** |
| **Rack_Type** | `device['rack']['type']['name']` | **YENİ** |
| **Hall** | `device['location']['custom_fields']['Hall']` veya discovery | **YENİ** |
| **Cluster** | `device['cluster']['name']` | **YENİ** |
| **Kurulum_Tarihi** | `device['custom_fields']['Kurulum_Tarihi']` | **YENİ** |
| **Loki_Tags** | `device['tags']` (array) | **YENİ** - Her tag name'i ayrı tag olarak |

## 7. Zabbix API Update Metodları

### 7.1 Host Update
```json
{
  "jsonrpc": "2.0",
  "method": "host.update",
  "params": {
    "hostid": "{{ hostid }}",
    "host": "{{ new_hostname }}",
    "name": "{{ new_hostname }}",
    "interfaces": [{
      "interfaceid": "{{ interfaceid }}",
      "ip": "{{ new_ip }}"
    }],
    "tags": [{
      "tag": "Loki_ID",
      "value": "{{ loki_id }}"
    }]
  }
}
```

### 7.2 Proxy Group Update
```json
{
  "jsonrpc": "2.0",
  "method": "host.update",
  "params": {
    "hostid": "{{ hostid }}",
    "monitored_by": 2,
    "proxy_groupid": "{{ proxy_group_id }}"
  }
}
```

## 8. Geliştirme Adımları

1. ✅ **Analiz Tamamlandı**: Netbox API field mapping ve Zabbix update stratejisi belirlendi
2. ⏳ **Netbox Device Processor Güncelleme**: Yeni alanları extract eden fonksiyonlar eklenecek
3. ⏳ **Zabbix Host Fetch**: Playbook başında tüm host'ları çeken task eklenecek
4. ⏳ **Mapping Oluşturma**: Loki_ID → Zabbix host mapping oluşturulacak
5. ⏳ **İki Senaryo Logic**: Host yok/var kontrolü ve işlem akışı
6. ⏳ **Güncelleme Stratejisi**: Sürekli vs sadece create alanları ayrımı
7. ⏳ **Tags Güncelleme**: Yeni tags'lerin eklenmesi ve güncelleme stratejisi

## 9. Örnek Netbox Device Response

```json
{
  "id": 12293,
  "name": "server-01",
  "device_type": {
    "manufacturer": {"name": "LENOVO"},
    "model": "ThinkSystem SR650"
  },
  "site": {"name": "ISTANBUL"},
  "location": {
    "id": 123,
    "name": "Datacenter-1",
    "parent": {"name": "DC14"}
  },
  "rack": {
    "id": 45,
    "name": "Rack-A-01",
    "type": {"name": "2-post"}
  },
  "cluster": {
    "id": 10,
    "name": "Production-Cluster"
  },
  "primary_ip4": {
    "address": "10.0.0.1/24"
  },
  "tags": [
    {"id": 1, "name": "production"},
    {"id": 2, "name": "critical"}
  ],
  "custom_fields": {
    "Kurulum_Tarihi": "2023-01-15",
    "Sorumlu_Ekip": "Infrastructure Team"
  }
}
```

## 10. Örnek Zabbix Host Response

```json
{
  "hostid": "10001",
  "host": "server-01",
  "name": "server-01",
  "interfaces": [{
    "interfaceid": "1",
    "ip": "10.0.0.1",
    "port": "161"
  }],
  "tags": [
    {"tag": "Loki_ID", "value": "12293"},
    {"tag": "Manufacturer", "value": "LENOVO"}
  ],
  "groups": [{"groupid": "1", "name": "Lenovo IPMI"}]
}
```

## Sonraki Adımlar

1. Netbox device processor script'ini güncelle (yeni alanları extract et)
2. Zabbix host fetch task'ını ekle (playbook başında)
3. Mapping logic'i implement et (Loki_ID → Zabbix host)
4. İki senaryo logic'ini implement et
5. Güncelleme stratejisini uygula (sürekli vs sadece create)
6. Test ve doğrulama

