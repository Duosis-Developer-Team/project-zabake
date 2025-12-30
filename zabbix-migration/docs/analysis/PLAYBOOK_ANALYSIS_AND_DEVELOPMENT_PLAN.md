# Netbox to Zabbix Playbook Analizi ve Geliştirme Planı

## Mevcut Playbook Yapısı Analizi

### 1. Ana Playbook: `netbox_to_zabbix.yaml`

**Yapı**:
- Host: `localhost`
- Pre-tasks: Credential validation
- Role: `netbox_to_zabbix` çağrılıyor

**Akış**:
```
1. Validation (netbox_url, token, zabbix credentials)
2. netbox_to_zabbix role çağrısı
```

### 2. Role: `netbox_to_zabbix`

#### 2.1 `main.yml` - Ana Task Dosyası

**Mevcut İşlemler**:
1. Device limit kontrolü
2. Mapping dosyalarını yükleme:
   - `templates.yml`
   - `datacenters.yml`
   - `netbox_device_type_mapping.yml`
3. `fetch_all_devices.yml` ile Netbox'tan device'ları çekme
4. Device limit uygulama
5. Her device için `process_device.yml` çağrısı

**Eksikler**:
- ❌ Zabbix'ten host'ları toplu çekme yok
- ❌ Loki_ID mapping yok
- ❌ Host var/yok kontrolü yok

#### 2.2 `fetch_all_devices.yml` - Netbox Device Fetch

**Mevcut İşlemler**:
1. Python script oluşturma (mapping-based filtering ile)
2. Netbox API'den pagination ile device'ları çekme
3. Mapping koşullarına göre filtreleme
4. Sonuçları JSON olarak döndürme

**Durum**: ✅ İyi çalışıyor, değişiklik gerekmiyor

#### 2.3 `process_device.yml` - Device Processing

**Mevcut İşlemler**:
1. Python script oluşturma (device processing için)
2. Device'ı işleme:
   - `determine_device_type()` - Device type belirleme
   - `get_primary_ip()` - IP çıkarma
   - `get_location_name()` - Location/DC_ID belirleme
   - `extract_host_groups()` - Host groups çıkarma
   - `extract_tags()` - Tags çıkarma (ESKİ - yeni tag'ler yok)
3. Zabbix login
4. `zabbix_migration` role'ünü `per_record` task'ı ile çağırma

**Eksikler**:
- ❌ Yeni tag'ler extract edilmiyor (rack, cluster, hall, kurulum tarihi, loki tags)
- ❌ Host var/yok kontrolü yok
- ❌ Güncelleme stratejisi yok (sürekli vs sadece create)

### 3. Role: `zabbix_migration`

#### 3.1 `per_record.yml` - Zabbix Host Create/Update

**Mevcut İşlemler**:
1. Tags parse etme (MACROS field'ından)
2. Template resolution
3. Interface spec resolution
4. Proxy group matching
5. Host groups yönetimi
6. Host create (eğer yoksa)
7. Host update (eğer varsa - sadece "already exists" hatası durumunda)

**Eksikler**:
- ❌ Loki_ID tag'ine göre host bulma yok
- ❌ Güncelleme stratejisi yok (sürekli güncellenecek vs sadece create)
- ❌ Host var/yok kontrolü playbook başında yapılmıyor

## Geliştirme Planı

### Aşama 1: Playbook Başında Toplu Veri Çekme

#### 1.1 Zabbix Host Fetch Task'ı Ekleme

**Yer**: `netbox_to_zabbix/tasks/main.yml` (fetch_all_devices.yml'den sonra)

**Yeni Task**: `fetch_all_zabbix_hosts.yml`

**İşlemler**:
1. Zabbix login
2. Tüm host'ları çekme:
   ```json
   {
     "method": "host.get",
     "params": {
       "output": ["hostid", "host", "name"],
       "selectInterfaces": ["interfaceid", "ip", "dns", "port"],
       "selectTags": ["tag", "value"],
       "selectGroups": ["groupid", "name"]
     }
   }
   ```
3. Loki_ID tag'ine göre mapping oluşturma:
   ```python
   zabbix_hosts_by_loki_id = {}
   for host in zabbix_hosts:
       loki_id = find_loki_id_tag(host['tags'])
       if loki_id:
           zabbix_hosts_by_loki_id[loki_id] = host
   ```
4. Hostname'e göre fallback mapping:
   ```python
   zabbix_hosts_by_hostname = {}
   for host in zabbix_hosts:
       zabbix_hosts_by_hostname[host['host']] = host
   ```

### Aşama 2: Yeni Tag'leri Extract Etme

#### 2.1 `extract_tags()` Fonksiyonunu Güncelleme

**Yer**: `process_device.yml` içindeki Python script

**Yeni Tag'ler**:
```python
def extract_tags(device):
    tags = {
        # Mevcut tag'ler
        'Manufacturer': device['device_type']['manufacturer']['name'],
        'Device_Type': device['device_type']['model'],
        'Location_Detail': device['location']['name'] or device['site']['name'],
        'City': device['site']['name'],
        'Contact': device['tenant']['name'] if device.get('tenant') else None,
        'Loki_ID': str(device['id']),
        
        # YENİ TAG'LER
        'Rack_Name': device['rack']['name'] if device.get('rack') else None,
        'Rack_Type': device['rack']['role']['name'] if device.get('rack', {}).get('role') else None,
        'Cluster': device['cluster']['name'] if device.get('cluster') else None,
        'Hall': device['location']['description'] or device['location']['name'] if device.get('location') else None,
        'Kurulum_Tarihi': device['custom_fields'].get('Kurulum_Tarihi'),
    }
    
    # Loki tags (device['tags'] array'inden)
    loki_tags = []
    for tag in device.get('tags', []):
        if isinstance(tag, dict):
            loki_tags.append(tag.get('name'))
        elif isinstance(tag, str):
            loki_tags.append(tag)
    
    # None değerleri temizle
    tags = {k: v for k, v in tags.items() if v is not None}
    
    return tags, loki_tags  # İki ayrı return: tags dict ve loki_tags list
```

### Aşama 3: İki Senaryo Implementasyonu

#### 3.1 Host Var/Yok Kontrolü

**Yer**: `process_device.yml` (device_info parse edildikten sonra)

**Yeni Task'lar**:
```yaml
- name: Check if host exists in Zabbix
  set_fact:
    zbx_existing_host: "{{ zabbix_hosts_by_loki_id.get(device_info.tags.Loki_ID | string) }}"
  when: 
    - zabbix_hosts_by_loki_id is defined
    - device_info.tags.Loki_ID is defined

- name: Fallback to hostname matching if Loki_ID not found
  set_fact:
    zbx_existing_host: "{{ zabbix_hosts_by_hostname.get(netbox_device.name) }}"
  when:
    - zbx_existing_host is not defined
    - zabbix_hosts_by_hostname is defined

- name: Determine scenario
  set_fact:
    zbx_scenario: "{{ 'update' if zbx_existing_host is defined else 'create' }}"
```

#### 3.2 Senaryo 1: Host Yok (Create)

**Yer**: `zabbix_migration/tasks/per_record.yml`

**Mevcut**: ✅ Zaten var (host.create)

**Değişiklik**: Tüm tag'ler (metadata dahil) eklenecek

#### 3.3 Senaryo 2: Host Var Ama Uyumsuz (Update)

**Yer**: `zabbix_migration/tasks/per_record.yml`

**Yeni Logic**:
```yaml
- name: Update existing host (only continuous fields)
  when: zbx_scenario == 'update'
  uri:
    url: "{{ zabbix_url }}"
    method: POST
    body_format: json
    body:
      jsonrpc: "2.0"
      method: "host.update"
      params:
        hostid: "{{ zbx_existing_host.hostid }}"
        host: "{{ zbx_record.HOSTNAME }}"  # Sürekli güncellenecek
        name: "{{ zbx_record.HOSTNAME }}"  # Sürekli güncellenecek
        interfaces: >-
          {{ [ {
            'interfaceid': zbx_existing_host.interfaces[0].interfaceid,
            'ip': zbx_record.HOST_IP,  # Sürekli güncellenecek
            # ... diğer interface alanları
          } ] }}
        # NOT: templates, groups, metadata tags güncellenmez
        # NOT: proxy_groupid güncellenmez (sadece create'de set edilir)
```

### Aşama 4: Güncelleme Stratejisi

#### 4.1 Sürekli Güncellenecek Alanlar

**Create ve Update'de güncellenir**:
- `host` (hostname)
- `name` (display name)
- `interfaces[].ip` (IP adresi)
- `monitored_by` ve `proxy_groupid` (DC_ID değişirse)

#### 4.2 Sadece Create'de Set Edilecek Alanlar

**Sadece yeni host oluşturulurken**:
- `templates` (template linking)
- `groups` (host groups)
- Metadata tags:
  - `Rack_Name`
  - `Rack_Type`
  - `Cluster`
  - `Hall`
  - `Kurulum_Tarihi`
  - Loki tags (device['tags'] array'inden)

**Update'de değiştirilmez**:
- Mevcut metadata tags korunur
- Templates değiştirilmez
- Host groups değiştirilmez

### Aşama 5: Yeni Task Dosyaları

#### 5.1 `fetch_all_zabbix_hosts.yml`

**Yer**: `netbox_to_zabbix/tasks/`

**İçerik**:
```yaml
---
- name: Zabbix login to obtain auth token
  uri:
    url: "{{ zabbix_url }}"
    method: POST
    body_format: json
    validate_certs: "{{ zabbix_validate_certs }}"
    body:
      jsonrpc: "2.0"
      method: "user.login"
      params:
        username: "{{ zabbix_user }}"
        password: "{{ zabbix_password }}"
      id: 0
  register: zbx_login_resp
  run_once: true
  delegate_to: localhost

- name: Set zabbix_auth from login
  set_fact:
    zabbix_auth: "{{ zbx_login_resp.json.result }}"
  run_once: true
  delegate_to: localhost

- name: Fetch all hosts from Zabbix
  uri:
    url: "{{ zabbix_url }}"
    method: POST
    body_format: json
    validate_certs: "{{ zabbix_validate_certs }}"
    body:
      jsonrpc: "2.0"
      method: "host.get"
      params:
        output: ["hostid", "host", "name"]
        selectInterfaces: ["interfaceid", "ip", "dns", "port", "type"]
        selectTags: ["tag", "value"]
        selectGroups: ["groupid", "name"]
      auth: "{{ zabbix_auth }}"
      id: 100
  register: zbx_hosts_resp
  run_once: true
  delegate_to: localhost

- name: Build Loki_ID to host mapping
  set_fact:
    zabbix_hosts_by_loki_id: >-
      {%- set mapping = {} -%}
      {%- for host in zbx_hosts_resp.json.result -%}
      {%- set loki_id = None -%}
      {%- for tag in host.tags | default([]) -%}
      {%- if tag.tag == 'Loki_ID' -%}
      {%- set loki_id = tag.value -%}
      {%- endif -%}
      {%- endfor -%}
      {%- if loki_id -%}
      {%- set _ = mapping.update({loki_id: host}) -%}
      {%- endif -%}
      {%- endfor -%}
      {{ mapping }}

- name: Build hostname to host mapping (fallback)
  set_fact:
    zabbix_hosts_by_hostname: >-
      {{ zbx_hosts_resp.json.result | items2dict(key_name='host', value_name='host') }}
```

## Geliştirme Adımları (Sıralı)

### Adım 1: Zabbix Host Fetch
1. ✅ `fetch_all_zabbix_hosts.yml` oluştur
2. ✅ `main.yml`'e ekle (fetch_all_devices.yml'den sonra)
3. ✅ Loki_ID mapping oluştur
4. ✅ Hostname mapping oluştur (fallback)

### Adım 2: Tag Extraction Güncelleme
1. ✅ `process_device.yml` içindeki Python script'i güncelle
2. ✅ `extract_tags()` fonksiyonuna yeni tag'leri ekle
3. ✅ Loki tags'i ayrı return et

### Adım 3: Host Var/Yok Kontrolü
1. ✅ `process_device.yml`'e host kontrolü ekle
2. ✅ Senaryo belirleme (create/update)

### Adım 4: Güncelleme Stratejisi
1. ✅ `per_record.yml`'de update logic'i güncelle
2. ✅ Sürekli güncellenecek alanları belirle
3. ✅ Metadata tags'i sadece create'de ekle

### Adım 5: Test ve Doğrulama
1. ✅ Test senaryoları oluştur
2. ✅ Create senaryosu test et
3. ✅ Update senaryosu test et

## Dosya Değişiklik Özeti

### Yeni Dosyalar
- `netbox_to_zabbix/tasks/fetch_all_zabbix_hosts.yml`

### Değiştirilecek Dosyalar
- `netbox_to_zabbix/tasks/main.yml` - Zabbix host fetch ekleme
- `netbox_to_zabbix/tasks/process_device.yml` - Host kontrolü ve yeni tag'ler
- `zabbix_migration/tasks/per_record.yml` - Güncelleme stratejisi

### Değişmeyecek Dosyalar
- `netbox_to_zabbix.yaml` - Ana playbook (değişiklik yok)
- `fetch_all_devices.yml` - Netbox fetch (değişiklik yok)

## Notlar

1. **Performans**: Zabbix host fetch playbook başında bir kez yapılacak, her device için tekrar edilmeyecek
2. **Mapping**: Loki_ID → Zabbix host mapping cache'lenecek
3. **Fallback**: Loki_ID yoksa hostname ile eşleştirme yapılacak
4. **Idempotency**: Playbook tekrar çalıştırıldığında güvenli olmalı
5. **Backward Compatibility**: Mevcut çalışan özellikler korunmalı

