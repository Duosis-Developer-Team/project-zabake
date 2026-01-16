# Netbox-Zabbix Güncelleme Geliştirmeleri - Özet

## Tamamlanan Geliştirmeler

### ✅ Adım 1: Zabbix Host Fetch
**Dosya**: `playbooks/roles/netbox_to_zabbix/tasks/fetch_all_zabbix_hosts.yml`

**Yapılanlar**:
- Zabbix'ten tüm host'ları toplu çekme
- Loki_ID tag'ine göre mapping oluşturma (`zabbix_hosts_by_loki_id`)
- Hostname'e göre fallback mapping (`zabbix_hosts_by_hostname`)
- `main.yml`'e entegrasyon

### ✅ Adım 2: Tag Extraction Güncelleme
**Dosya**: `playbooks/roles/netbox_to_zabbix/tasks/process_device.yml`

**Yapılanlar**:
- `extract_tags()` fonksiyonuna yeni tag'ler eklendi:
  - `Rack_Name`: `device['rack']['name']`
  - `Rack_Type`: `device['rack']['role']['name']`
  - `Cluster`: `device['cluster']['name']`
  - `Hall`: `device['location']['description']` veya `device['location']['name']`
  - `Kurulum_Tarihi`: `device['custom_fields']['Kurulum_Tarihi']`
  - Loki tags: `device['tags']` array'inden her tag name'i ayrı tag olarak (`Loki_Tag_*` prefix ile)

### ✅ Adım 3: Host Var/Yok Kontrolü
**Dosya**: `playbooks/roles/netbox_to_zabbix/tasks/process_device.yml`

**Yapılanlar**:
- Loki_ID tag'ine göre host kontrolü
- Hostname fallback kontrolü
- Senaryo belirleme (create/update)
- Senaryo bilgisini `zabbix_migration` role'üne aktarma

### ✅ Adım 4: Güncelleme Stratejisi
**Dosya**: `playbooks/roles/zabbix_migration/tasks/per_record.yml`

**Yapılanlar**:
- Tag'lerin ayrılması: Continuous vs Metadata
- **Create Senaryosu**: Tüm tag'ler (continuous + metadata) eklenir
- **Update Senaryosu**: Sadece continuous tag'ler güncellenir
- Sürekli güncellenecek alanlar:
  - `host` (hostname)
  - `name` (display name)
  - `interfaces[].ip` (IP adresi)
  - `monitored_by` ve `proxy_groupid` (DC_ID değişirse)
  - Continuous tags: `Loki_ID`, `Location_Detail`, `City`, `Contact`
- Sadece create'de set edilecek alanlar:
  - `templates` (template linking)
  - `groups` (host groups)
  - Metadata tags: `Rack_Name`, `Rack_Type`, `Cluster`, `Hall`, `Kurulum_Tarihi`, `Manufacturer`, `Device_Type`, `Sorumlu_Ekip`, Loki tags

## Değiştirilen Dosyalar

1. ✅ `playbooks/roles/netbox_to_zabbix/tasks/fetch_all_zabbix_hosts.yml` (YENİ)
2. ✅ `playbooks/roles/netbox_to_zabbix/tasks/main.yml` (GÜNCELLENDİ)
3. ✅ `playbooks/roles/netbox_to_zabbix/tasks/process_device.yml` (GÜNCELLENDİ)
4. ✅ `playbooks/roles/zabbix_migration/tasks/per_record.yml` (GÜNCELLENDİ)

## Yeni Özellikler

### 1. Toplu Veri Çekme
- Playbook başında hem Netbox hem Zabbix'ten veriler toplu çekiliyor
- Her device için ayrı API çağrısı yapılmıyor
- Performans optimizasyonu sağlandı

### 2. İki Senaryo Desteği
- **Senaryo 1 (Create)**: Host yok → Tüm alanlar ile yeni host oluşturulur
- **Senaryo 2 (Update)**: Host var → Sadece sürekli güncellenecek alanlar güncellenir

### 3. Akıllı Tag Yönetimi
- Continuous tags: Her update'de güncellenir
- Metadata tags: Sadece create'de set edilir, update'de korunur

### 4. Yeni Tag'ler
- Rack bilgileri (Name, Type)
- Cluster bilgisi
- Hall bilgisi
- Kurulum Tarihi
- Loki tags (Netbox'tan gelen tüm tag'ler)

## Kullanım

Playbook kullanımı değişmedi:

```bash
ansible-playbook netbox_to_zabbix.yaml \
  -e "netbox_url=https://loki.bulutistan.com/" \
  -e "netbox_token=YOUR_TOKEN" \
  -e "zabbix_url=http://zabbix.example.com/zabbix/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

## Notlar

1. **Backward Compatibility**: Mevcut çalışan özellikler korundu
2. **Idempotency**: Playbook tekrar çalıştırıldığında güvenli
3. **Performance**: Toplu veri çekme ile API çağrı sayısı azaltıldı
4. **Fallback**: Loki_ID yoksa hostname ile eşleştirme yapılıyor

## Test Edilmesi Gerekenler

1. ✅ Yeni host oluşturma (create senaryosu)
2. ✅ Mevcut host güncelleme (update senaryosu)
3. ✅ Tag'lerin doğru ayrılması (continuous vs metadata)
4. ✅ Loki_ID mapping'in çalışması
5. ✅ Hostname fallback'in çalışması
6. ✅ Yeni tag'lerin extract edilmesi

