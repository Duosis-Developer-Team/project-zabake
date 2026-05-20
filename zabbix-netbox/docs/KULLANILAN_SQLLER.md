# Kullanılan SQL'ler ve Alan Kaynakları

Bu doküman, `fetch_all_db_devices.py` script'inin çalıştırdığı SQL'i parçalara ayırarak hangi değerin hangi tablodan/sütundan geldiğini açıklar.

---

## Ana Sorgu Yapısı

```
WITH RECURSIVE location_tree  →  Lokasyon hiyerarşisini düzleştir
             root_locations   →  Her lokasyonun en üst parent'ını bul
             cluster_map      →  Site bazında cluster isimlerini topla
SELECT ...
FROM discovery_netbox_inventory_device d
LEFT JOIN discovery_loki_location l         ON d.location_id = l.id
LEFT JOIN root_locations rl                 ON d.location_id = rl.start_location_id
LEFT JOIN discovery_netbox_platform p       ON d.platform_id = p.id
LEFT JOIN cluster_map cm                    ON d.site_name = cm.site_name
WHERE d.status_value = 'active'
  AND <izlenmeli_condition>
  AND <location_filter_condition>
```

---

## CTE 1 — `location_tree` (Recursive)

**Amaç:** `discovery_loki_location` tablosundaki parent-child ilişkisini recursive olarak düzleştirir. Her lokasyon için köke kadar olan tüm ataları listeler.

```sql
WITH RECURSIVE location_tree AS (
    -- Başlangıç: tüm lokasyonlar (level=0)
    SELECT
        l.id,
        l.name,
        l.parent_id,
        l.parent_name,
        l.description,
        l.site_name,
        l.id    AS start_location_id,
        0       AS level
    FROM public.discovery_loki_location l

    UNION ALL

    -- Recursive adım: her lokasyonun parent'ına çık
    SELECT
        parent.id,
        parent.name,
        parent.parent_id,
        parent.parent_name,
        parent.description,
        parent.site_name,
        lt.start_location_id,   -- başlangıç noktasını koru
        lt.level + 1
    FROM public.discovery_loki_location parent
    INNER JOIN location_tree lt ON lt.parent_id = parent.id
)
```

**Kullanılan tablo:** `public.discovery_loki_location`

| Sütun | Kullanım amacı |
|---|---|
| `id` | Lokasyon kimliği |
| `name` | Lokasyon adı |
| `parent_id` | Recursive join koşulu |
| `parent_name` | Üst lokasyon adı |
| `description` | Hall/konum detayı |
| `site_name` | Site adı |
| `start_location_id` | Recursive adımda başlangıç noktası (kaybolmaması için) |
| `level` | Kaçıncı ata olduğu (0 = kendisi) |

**Örnek sonuç:**

| start_location_id | id | name | parent_id | level |
|---|---|---|---|---|
| 10 | 10 | DH4 | 5 | 0 |
| 10 | 5 | DC13 | NULL | 1 |

---

## CTE 2 — `root_locations`

**Amaç:** `location_tree`'den her `start_location_id` için **en üst parent**'ı (root) seçer. Bu değer Zabbix'te `DC_ID` olarak kullanılır.

```sql
root_locations AS (
    SELECT DISTINCT ON (start_location_id)
        start_location_id,
        id          AS root_location_id,
        name        AS root_location_name,
        description AS root_location_description
    FROM location_tree
    WHERE parent_id IS NULL          -- sadece root'lar (parent'ı olmayan)
    ORDER BY start_location_id, level DESC
)
```

**Mantık:**
- `parent_id IS NULL` → en üst lokasyon (root)
- `DISTINCT ON (start_location_id)` → her başlangıç lokasyonu için tek satır
- `ORDER BY level DESC` → en yüksek seviyedeki (en üstteki) seçilir

**Üretilen alanlar ve Zabbix karşılığı:**

| SQL Alias | Kaynak sütun | Zabbix kullanımı |
|---|---|---|
| `root_location_name` | `location_tree.name` (root satırı) | **DC_ID** (birincil) |
| `root_location_description` | `location_tree.description` (root satırı) | Referans bilgi |

**Örnek:**

| start_location_id | root_location_id | root_location_name |
|---|---|---|
| 10 (DH4) | 5 | DC13 |
| 5 (DC13) | 5 | DC13 |

---

## CTE 3 — `cluster_map`

**Amaç:** Aynı site altında birden fazla cluster olabileceğinden, `site_name` bazında tüm cluster isimlerini birleştirir.

```sql
cluster_map AS (
    SELECT
        site_name,
        STRING_AGG(DISTINCT cluster_name, ', ' ORDER BY cluster_name) AS resolved_cluster_name
    FROM public.discovery_netbox_virtualization_vm
    WHERE cluster_name IS NOT NULL
      AND site_name    IS NOT NULL
    GROUP BY site_name
)
```

**Kullanılan tablo:** `public.discovery_netbox_virtualization_vm`

| Sütun | Kullanım amacı |
|---|---|
| `site_name` | Ana tabloyla join anahtarı |
| `cluster_name` | Toplanacak cluster adları |

**Üretilen alan:**

| SQL Alias | Açıklama | Zabbix kullanımı |
|---|---|---|
| `resolved_cluster_name` | Virgülle ayrılmış cluster adları | `Cluster` tag'i |

**Örnek:**

| site_name | resolved_cluster_name |
|---|---|
| DC11 | CLS-DC11-01, CLS-DC11-02 |
| DC13 | CLS-DC13-01 |

---

## Ana SELECT — Alan Kaynakları

### Cihaz Temel Bilgileri

```sql
d.id,
d.name,
d.device_type_name  AS device_model,
d.manufacturer_name,
d.device_role_name,
d.primary_ip_address,
```

**Tablo:** `public.discovery_netbox_inventory_device` (alias: `d`)

| SQL Alias / Sütun | DB Sütunu | Zabbix / İşleme kullanımı |
|---|---|---|
| `id` | `d.id` | `Loki_ID` tag'i |
| `name` | `d.name` | Zabbix hostname |
| `device_model` | `d.device_type_name` | Device type mapping koşulu + `Device_Type` tag'i |
| `manufacturer_name` | `d.manufacturer_name` | Device type mapping koşulu + `Manufacturer` tag'i |
| `device_role_name` | `d.device_role_name` | Device type mapping koşulu + host group |
| `primary_ip_address` | `d.primary_ip_address` | Zabbix host IP adresi |

---

### Site / Lokasyon Bilgileri

```sql
d.site_id,
d.site_name,
d.location_id,
d.location_name,
l.description        AS location_description,
l.parent_id          AS location_parent_id,
l.parent_name        AS location_parent_name,
rl.root_location_name,
rl.root_location_description,
```

**Tablolar:**
- `d.*` → `public.discovery_netbox_inventory_device`
- `l.*` → `public.discovery_loki_location` (JOIN: `d.location_id = l.id`)
- `rl.*` → `root_locations` CTE (JOIN: `d.location_id = rl.start_location_id`)

| SQL Alias | Kaynak | Zabbix / İşleme kullanımı |
|---|---|---|
| `site_id` | `d.site_id` | Referans |
| `site_name` | `d.site_name` | `City` tag, DC_ID fallback (4. sıra) |
| `location_id` | `d.location_id` | CTE join anahtarı |
| `location_name` | `d.location_name` | `Location_Detail` tag, DC_ID fallback (3. sıra) |
| `location_description` | `l.description` | `Hall` tag (birincil) |
| `location_parent_id` | `l.parent_id` | Referans |
| `location_parent_name` | `l.parent_name` | DC_ID fallback (2. sıra) |
| `root_location_name` | CTE `root_locations` | **DC_ID (1. sıra / birincil)** |
| `root_location_description` | CTE `root_locations` | Referans |

#### DC_ID Fallback Sırası (Python'da uygulanır)

```
1. root_location_name        → Recursive SQL ile bulunan en üst parent
2. location_parent_name      → l.parent_name (direkt parent)
3. location_name             → d.location_name (cihazın lokasyonu)
4. site_name                 → d.site_name (son çare)
```

---

### Tenant Bilgisi

```sql
d.tenant_id,
d.tenant_name,
```

**Tablo:** `public.discovery_netbox_inventory_device`

| SQL Alias | DB Sütunu | Zabbix / İşleme kullanımı |
|---|---|---|
| `tenant_id` | `d.tenant_id` | Referans |
| `tenant_name` | `d.tenant_name` | `Tenant` tag'i |

> **Not:** Tenant bilgisi doğrudan ana tablodan gelir. Ayrıca API veya başka tablo join'i yapılmaz.

---

### Platform Bilgisi

```sql
d.platform_id,
d.platform_name,
p.parent_name        AS platform_parent_name,
p.manufacturer_name  AS platform_manufacturer_name,
p.cf_dc              AS platform_cf_dc,
p.cf_site            AS platform_cf_site,
p.cf_ip_addresses    AS platform_cf_ip_addresses,
p.cf_port            AS platform_cf_port,
p.cf_url             AS platform_cf_url,
```

**Tablo:** `public.discovery_netbox_platform` (alias: `p`, JOIN: `d.platform_id = p.id`)

| SQL Alias | Kaynak | Kullanım |
|---|---|---|
| `platform_id` | `d.platform_id` | Join anahtarı |
| `platform_name` | `d.platform_name` | Referans |
| `platform_parent_name` | `p.parent_name` | Platform üst grubu |
| `platform_manufacturer_name` | `p.manufacturer_name` | Platform üreticisi |
| `platform_cf_dc` | `p.cf_dc` | Platform custom field |
| `platform_cf_site` | `p.cf_site` | Platform custom field |
| `platform_cf_ip_addresses` | `p.cf_ip_addresses` | Platform IP |
| `platform_cf_port` | `p.cf_port` | Platform port |
| `platform_cf_url` | `p.cf_url` | Platform URL |

---

### Cluster Bilgisi

```sql
cm.resolved_cluster_name AS cluster_name,
```

**Tablo:** `cluster_map` CTE → `public.discovery_netbox_virtualization_vm` (JOIN: `d.site_name = cm.site_name`)

| SQL Alias | Kaynak | Zabbix / İşleme kullanımı |
|---|---|---|
| `cluster_name` | CTE `cluster_map` | `Cluster` tag'i |

---

### Custom Alanlar ve İzleme Bayrakları

```sql
d.custom_fields,
d.sahiplik,
d.kurulum_tarihi,
d.izlenmeli,
d.zabbix_monitoring,
d.datalake_monitoring,
```

**Tablo:** `public.discovery_netbox_inventory_device`

| SQL Alias | DB Sütunu | Zabbix / İşleme kullanımı |
|---|---|---|
| `custom_fields` | `d.custom_fields` | JSONB; `Sorumlu_Ekip` gibi ek alanlar buradan |
| `sahiplik` | `d.sahiplik` | `Contact` tag'i, host group |
| `kurulum_tarihi` | `d.kurulum_tarihi` | `Kurulum_Tarihi` tag'i |
| `izlenmeli` | `d.izlenmeli` | **WHERE filtresi** + skip/monitor ayrımı |
| `zabbix_monitoring` | `d.zabbix_monitoring` | Referans |
| `datalake_monitoring` | `d.datalake_monitoring` | Referans |

#### `izlenmeli` WHERE Koşulları

| AWX Mode | SQL Koşulu | Açıklama |
|---|---|---|
| `monitor` | `(d.izlenmeli IS NULL OR d.izlenmeli != 'Hayır')` | İzlenecek cihazlar |
| `skip` | `(d.izlenmeli = 'Hayir' OR d.izlenmeli = 'Hayır')` | Raporlanacak ama işlenmeyecek cihazlar |

---

### Tag Alanları

```sql
d.tags1_name,
d.tags2_name,
d.tags3_name,
d.tags4_name,
d.tags5_name,
```

**Tablo:** `public.discovery_netbox_inventory_device`

| DB Sütunu | Zabbix / İşleme kullanımı |
|---|---|
| `tags1_name` | `Loki_Tag_<değer>` tag'i olarak Zabbix'e yazılır |
| `tags2_name` | `Loki_Tag_<değer>` tag'i olarak Zabbix'e yazılır |
| `tags3_name` | `Loki_Tag_<değer>` tag'i olarak Zabbix'e yazılır |
| `tags4_name` | `Loki_Tag_<değer>` tag'i olarak Zabbix'e yazılır |
| `tags5_name` | `Loki_Tag_<değer>` tag'i olarak Zabbix'e yazılır |

> NULL olan tag sütunları atlanır.

---

### Meta Alanlar

```sql
d.created::text,
d.last_updated::text,
```

**Tablo:** `public.discovery_netbox_inventory_device`

| DB Sütunu | Kullanım |
|---|---|
| `created` | Referans (timestamp → text cast) |
| `last_updated` | Referans (timestamp → text cast) |

---

## WHERE Koşulları

```sql
WHERE d.status_value = 'active'        -- sadece aktif cihazlar
  AND <izlenmeli_condition>            -- monitor veya skip modu
  AND <location_filter_condition>      -- opsiyonel lokasyon filtresi
```

### `location_filter` Koşulu

AWX'te `location_filter` değişkeni doluysa parameterized query ile eklenir:

```sql
AND (d.location_name ILIKE %s OR d.site_name ILIKE %s)
-- parametre: '%DC11%', '%DC11%'
```

Boşsa bu koşul eklenmez (tüm aktif cihazlar gelir).

---

## JOIN Özeti

| JOIN | Kaynak | Hedef | Koşul | Tür |
|---|---|---|---|---|
| Ana tablo | `discovery_netbox_inventory_device d` | — | — | — |
| Lokasyon detayı | `discovery_loki_location l` | `d` | `d.location_id = l.id` | LEFT JOIN |
| Root lokasyon | `root_locations rl` (CTE) | `d` | `d.location_id = rl.start_location_id` | LEFT JOIN |
| Platform | `discovery_netbox_platform p` | `d` | `d.platform_id = p.id` | LEFT JOIN |
| Cluster | `cluster_map cm` (CTE) | `d` | `d.site_name = cm.site_name` | LEFT JOIN |

> **Rack tablosu (`discovery_loki_rack`) kullanılmamaktadır.**
> `rack_id` ile `discovery_loki_rack.id` eşleşmediğinden join yapılmamıştır.

---

## Zabbix Alan Eşleme Özeti

| Zabbix Alanı | SQL / Python Kaynağı |
|---|---|
| Hostname | `d.name` |
| Host IP | `d.primary_ip_address` |
| DC_ID (location) | `root_location_name` → `location_parent_name` → `location_name` → `site_name` |
| Device Type (mapping) | `d.device_type_name` (`device_model` alias) |
| Manufacturer | `d.manufacturer_name` |
| Device Role | `d.device_role_name` |
| Tenant | `d.tenant_name` |
| Cluster tag | `cm.resolved_cluster_name` |
| Contact tag | `d.sahiplik` |
| Hall tag | `l.description` → `d.location_name` |
| Kurulum_Tarihi tag | `d.kurulum_tarihi` |
| Loki_ID tag | `d.id` |
| Loki_Tag_* tags | `d.tags1_name` … `d.tags5_name` |
| Sorumlu_Ekip tag | `d.custom_fields->>'Sorumlu_Ekip'` (JSONB) |
