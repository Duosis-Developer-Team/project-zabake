# AWX Kullanım Rehberi — HMDL DB → Zabbix Sync

Bu rehber, `netbox_zabbix_sync` rolünü AWX üzerinde çalıştırmak için gereken tüm değişkenleri ve önerilen test sırasını açıklar.

---

## AWX'e Eklenecek Değişkenler (Extra Variables / Survey)

### Zorunlu: DB Bağlantısı

```yaml
discovery_db_host: "<postgresql_host>"
discovery_db_port: 5432
discovery_db_name: "<db_name>"         # örn. bulutlake
discovery_db_user: "<db_user>"
discovery_db_password: "<db_password>"
```

### Zorunlu: Zabbix Bağlantısı

```yaml
zabbix_url: "https://<zabbix_host>/api_jsonrpc.php"
zabbix_user: "<zabbix_api_user>"
zabbix_password: "<zabbix_api_password>"
zabbix_validate_certs: false
```

### Opsiyonel: HMDL Log (Önerilir)

```yaml
hmdl_log_enabled: true
hmdl_log_schema: hmdl
hmdl_log_table: zabbix_sync_log
hmdl_playbook_name: db_to_zabbix_sync
```

> Log için aynı discovery DB bağlantısı kullanılır. Farklı bir DB kullanılacaksa
> `hmdl_db_host`, `hmdl_db_port`, `hmdl_db_name`, `hmdl_db_user`, `hmdl_db_password`
> değişkenleri ayrıca override edilebilir.

### Opsiyonel: Filtreleme

```yaml
device_limit: 0          # 0 = tüm cihazlar; test için örn. 10
location_filter: ""      # Boş = tüm lokasyonlar; örn. "ICT11" veya "DC14"
```

### Çalışma Modu

```yaml
sync_devices: true        # Device sync açık
sync_platforms: false     # Platform sync (varsayılan kapalı)
only_fetch: false         # Sadece DB'den çek, Zabbix'e hiçbir şey yapma
dry_run: false            # Dry-run modu (aşağıya bak)
report_izlenmeyecek: true # İzlenmeyecek cihazları rapora/loga ekle
```

---

## Çalıştırma Senaryoları

### 1. İlk Test — Dry-Run (Hiçbir şey yazma, sadece önizle)

Zabbix'e hiçbir host eklenmez/güncellenmez. Sadece hangi değerlerin gönderileceği görülür.

```yaml
dry_run: true
hmdl_log_enabled: true    # dry_run logları DB'ye yazılır (status = dry_run)
sync_devices: true
sync_platforms: false
device_limit: 10           # İlk testte az sayıda cihazla dene
```

AWX çıktısında her device için şunu göreceksin:
- Hangi hostname/IP kullanılacaktı
- Hangi template seçildi
- Hangi host group'lar oluşacaktı
- Hangi proxy group eşleşti
- Zabbix'te zaten var mıydı (update mi, create mi olacaktı)
- Validasyon geçti mi, geçemediyse neden

`hmdl.zabbix_sync_log` tablosunda sonuçları sorgulayabilirsin:
```sql
SELECT zabbix_hostname, device_type, status, reason, operation, processed_at
FROM hmdl.zabbix_sync_log
WHERE status = 'dry_run'
ORDER BY processed_at DESC;
```

---

### 2. İkinci Test — Sadece DB'den Çek (Zabbix'e dokunma)

```yaml
only_fetch: true
sync_devices: true
```

Device listesini loglar; Zabbix'e login dahi olmaz.

---

### 3. Gerçek Çalıştırma — Sınırlı Cihaz

İlk gerçek sync'i sınırlı cihazla yap:

```yaml
dry_run: false
hmdl_log_enabled: true
sync_devices: true
sync_platforms: false
device_limit: 20
location_filter: "ICT11"   # Tek lokasyonla başla
```

---

### 4. Tam Çalıştırma — Tüm Cihazlar

```yaml
dry_run: false
hmdl_log_enabled: true
sync_devices: true
sync_platforms: false
device_limit: 0
location_filter: ""
```

---

## AWX Job Template Önerilen Ayarları

| Alan | Değer |
|---|---|
| **Inventory** | `localhost` (playbook `delegate_to: localhost` ile çalışır) |
| **Credentials** | AWX Vault veya Custom Credential (DB + Zabbix şifreleri için) |
| **Extra Variables** | Yukarıdaki YAML bloğu |
| **Verbosity** | `1` (normal) veya `2` (debug için) |
| **Job Tags** | Boş (tüm tasklar çalışır) |

---

## HMDL Log Tablosu Sorgular

### Son çalışmadaki özet

```sql
SELECT status, operation, COUNT(*) AS adet
FROM hmdl.zabbix_sync_log
WHERE run_id = '<RUN_ID>'
GROUP BY status, operation
ORDER BY adet DESC;
```

### Başarısız kayıtlar (son 24 saat)

```sql
SELECT
    processed_at,
    source_device_name,
    zabbix_hostname,
    zabbix_host_ip,
    device_type,
    status,
    reason
FROM hmdl.zabbix_sync_log
WHERE processed_at >= NOW() - INTERVAL '24 hours'
  AND status = 'eklenemedi'
ORDER BY processed_at DESC;
```

### Dry-run sonuçları

```sql
SELECT
    source_device_name,
    zabbix_hostname,
    zabbix_host_ip,
    device_type,
    operation,
    reason
FROM hmdl.zabbix_sync_log
WHERE status = 'dry_run'
ORDER BY processed_at DESC;
```

### Cihaz bazlı son durum

```sql
SELECT DISTINCT ON (source_device_id)
    source_device_id,
    source_device_name,
    zabbix_hostname,
    zabbix_host_ip,
    status,
    reason,
    processed_at
FROM hmdl.zabbix_sync_log
ORDER BY source_device_id, processed_at DESC;
```

---

## Status Değerleri Referansı

| Status | Anlamı |
|---|---|
| `eklendi` | Host Zabbix'e yeni eklendi |
| `güncellendi` | Var olan host güncellendi |
| `güncel` | Host zaten güncel, işlem yapılmadı |
| `eklenemedi` | Hata nedeniyle eklenemedi/güncellenemedi |
| `atlandı` | `izlenmeli=Hayır` olduğu için işlenmedi |
| `dry_run` | `dry_run: true` modunda çalıştı, API çağrısı yapılmadı |

---

## Notlar

- `AWX_JOB_ID` AWX tarafından otomatik olarak ortam değişkeni olarak set edilir; log tablosuna otomatik yazılır.
- `run_id` aynı playbook çalışmasındaki tüm kayıtlar için ortaktır; `WHERE run_id = '...'` ile filtrelenebilir.
- Log insert hatası ana Zabbix sync akışını kesmez; hata AWX çıktısına debug olarak yazılır.
- `hmdl.zabbix_sync_log` tablosu ve indexler ilk çalışmada otomatik oluşturulur.
