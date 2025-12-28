# Netbox Device Type Mapping

Bu dosya, Netbox device'larının Zabbix DEVICE_TYPE'ına nasıl map edileceğini tanımlar.

## Dosya Yapısı

```yaml
mappings:
  - device_type: "Device Type Name"
    conditions:
      device_role: "HOST"  # veya ["HOST", "OTHER"]
      manufacturer: "LENOVO"  # veya ["LENOVO", "HPE"]
      model_contains: ["ICT", "XCC"]  # Model içinde bu stringler var mı?
      model_suffix: "M6"  # Model bu suffix ile bitiyor mu?
      name_contains: ["ILO"]  # Device name içinde bu stringler var mı?
    priority: 1  # Düşük sayı = yüksek öncelik
```

## Koşul Tipleri

### device_role
Device role'ü kontrol eder. String veya liste olabilir.

```yaml
device_role: "HOST"
# veya
device_role: ["HOST", "SERVER"]
```

### manufacturer
Manufacturer adını kontrol eder. String veya liste olabilir. Case-insensitive.

```yaml
manufacturer: "LENOVO"
# veya
manufacturer: ["HPE", "HP"]
```

### model_contains
Device type model'inde belirtilen stringlerin olup olmadığını kontrol eder. Liste olabilir.

```yaml
model_contains: ["ICT", "XCC"]
```

### model_suffix
Device type model'inin belirtilen suffix ile bitip bitmediğini kontrol eder.

```yaml
model_suffix: "M6"
```

### name_contains
Device name'inde belirtilen stringlerin olup olmadığını kontrol eder. Liste olabilir.

```yaml
name_contains: ["ILO"]
```

## Priority (Öncelik)

Mapping'ler priority'ye göre sıralanır. Düşük sayı = yüksek öncelik. İlk eşleşen mapping kullanılır.

Örnek:
- Priority 1: Özel koşullar (örn: Lenovo ICT, Inspur M6)
- Priority 2: Genel koşullar (örn: Lenovo IPMI, HPE IPMI)
- Priority 999: Fallback (örn: Network Generic)

## Örnek Mapping

```yaml
mappings:
  - device_type: "Lenovo ICT"
    conditions:
      device_role: "HOST"
      manufacturer: "LENOVO"
      model_contains: ["ICT", "XCC"]
    priority: 1

  - device_type: "Lenovo IPMI"
    conditions:
      device_role: "HOST"
      manufacturer: "LENOVO"
    priority: 2
```

Bu örnekte:
1. Önce "Lenovo ICT" kontrol edilir (priority 1)
   - Device role HOST mu?
   - Manufacturer LENOVO mu?
   - Model'de ICT veya XCC var mı?
   - Hepsi eşleşirse "Lenovo ICT" döner

2. Eşleşmezse "Lenovo IPMI" kontrol edilir (priority 2)
   - Device role HOST mu?
   - Manufacturer LENOVO mu?
   - Eşleşirse "Lenovo IPMI" döner

## Yeni Mapping Ekleme

1. `mappings/netbox_device_type_mapping.yml` dosyasını açın
2. Yeni bir mapping ekleyin:

```yaml
- device_type: "Yeni Device Type"
  conditions:
    device_role: "HOST"
    manufacturer: "YENI_MANUFACTURER"
    model_contains: ["MODEL_KEYWORD"]
  priority: 1
```

3. Priority'yi uygun şekilde ayarlayın (daha spesifik = daha düşük sayı)
4. Dosyayı kaydedin

## Notlar

- Tüm string karşılaştırmaları case-insensitive'dir
- Koşullar AND mantığıyla birleştirilir (tümü eşleşmeli)
- İlk eşleşen mapping kullanılır
- Hiçbir mapping eşleşmezse `None` döner ve device atlanır

