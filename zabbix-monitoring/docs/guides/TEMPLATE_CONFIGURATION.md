# Template Configuration Guide

Bu kılavuz, YAML tabanlı template ve item yapılandırmasını açıklar.

## 📋 Genel Bakış

Template ve item tanımlamaları `mappings/templates.yml` dosyasında yönetilir. Bu dosya, hangi template'lerin hangi connection check item'larına ve master item'lara sahip olduğunu tanımlar.

## 📁 Dosya Yapısı

```yaml
templates:
  - name: "Template Name"
    vendor: "Vendor Name"
    type: "SNMP" | "API"
    conditions:
      device_role: "HOST"
      manufacturer: "Vendor"
    connection_check_items:
      - key: "item.key"
        name: "Item Name"
        required: true
        priority: "high" | "medium" | "low"
    master_items:
      - key: "master.item.key"
        name: "Master Item Name"
        required: true
        priority: "high"
```

## 🔧 Template Tanımlama

### Temel Yapı

Her template için şu bilgiler tanımlanır:

- **name**: Zabbix'teki template adı (tam eşleşme gerekir)
- **vendor**: Vendor adı (Lenovo, Inspur, HPE, Dell, Supermicro)
- **type**: Monitoring tipi (SNMP, API)
- **conditions**: Template'in hangi host'lara uygulanacağını belirleyen koşullar
- **connection_check_items**: Connectivity kontrolü için kullanılan item'lar
- **master_items**: Master item'lar (varsa)

### Conditions (Koşullar)

Conditions, template'in hangi host'lara uygulanacağını belirler:

```yaml
conditions:
  device_role: "HOST"          # Zorunlu
  manufacturer: "Lenovo"         # Vendor adı
  type_suffix: "M6"             # Opsiyonel (Inspur M5/M6 için)
```

### Connection Check Items

Connectivity kontrolü için kullanılan item'lar:

```yaml
connection_check_items:
  - key: "snmp.availability"
    name: "Snmp agent availability"
    required: true
    priority: "high"
    is_discovery: false         # Opsiyonel
    discovery_rule_note: ""     # Opsiyonel
```

**Özellikler:**
- **key**: Item key (Zabbix'teki item key ile eşleşmeli)
- **name**: Item adı (görsel amaçlı)
- **required**: Zorunlu item mı?
- **priority**: Öncelik seviyesi (high, medium, low)
- **is_discovery**: Discovery rule item'ı mı?
- **discovery_rule_note**: Discovery rule notu

### Master Items

Master item'lar (bağımlı item'lar için):

```yaml
master_items:
  - key: "redfish.get.metrics"
    name: "Redfish: Get metrics"
    required: true
    priority: "high"
```

## 📝 Örnekler

### Lenovo IPMI Template

```yaml
- name: "BLT - Lenovo ICT XCC Monitoring"
  vendor: "Lenovo"
  type: "SNMP"
  conditions:
    device_role: "HOST"
    manufacturer: "Lenovo"
  connection_check_items:
    - key: "snmp.availability"
      name: "Snmp agent availability"
      required: true
      priority: "high"
    - key: "icmpping"
      name: "ICMP ping"
      required: true
      priority: "high"
  master_items: []
  notes: "Api'dan psu watt değerleri eklenecek"
```

### Dell IPMI Template (Discovery Rule ile)

```yaml
- name: "BLT - Dell iDRAC SNMP"
  vendor: "Dell"
  type: "SNMP"
  conditions:
    device_role: "HOST"
    manufacturer: "DELL"
  connection_check_items:
    - key: "snmp.availability"
      name: "Snmp agent availability"
      required: true
      priority: "high"
    - key: "cant.get.data.from"
      name: "Can't get data from {#SECTION}"
      required: false
      priority: "low"
      is_discovery: true
      discovery_rule_note: "Discovery rule Endpoint kontrolü için"
  master_items: []
```

### Supermicro Template (Master Item ile)

```yaml
- name: "BLT- Supermicro ILO by Redfish API"
  vendor: "Supermicro"
  type: "API"
  conditions:
    device_role: "HOST"
    manufacturer: "-"
  connection_check_items: []
  master_items:
    - key: "redfish.get.metrics"
      name: "Redfish: Get metrics"
      required: true
      priority: "high"
```

## 🔍 Global Patterns

Template'e özel item tanımlanmamışsa, global pattern'ler kullanılır:

```yaml
global_connection_patterns:
  - pattern: "snmp.availability"
    name_pattern: "*agent availability*"
    priority: "high"
  - pattern: "icmpping"
    name_pattern: "*ping*"
    priority: "high"
```

## ⚙️ Thresholds

Analiz için kullanılan eşik değerleri:

```yaml
thresholds:
  max_data_age: 3600              # Son veri yaşı (saniye)
  min_connectivity_score: 0.8     # Minimum connectivity skoru
  inactive_threshold: 7200         # Inactive eşiği (saniye)
  master_item_threshold: 1800     # Master item eşiği (saniye)
```

## 🚀 Kullanım

### YAML Dosyasını Güncelleme

1. `mappings/templates.yml` dosyasını düzenleyin
2. Yeni template ekleyin veya mevcut template'i güncelleyin
3. Connection check item'ları ve master item'ları tanımlayın
4. Playbook'u çalıştırın

### Template Eşleştirme

Sistem şu sırayla template eşleştirmesi yapar:

1. Host'un template'lerini alır
2. `templates.yml` dosyasındaki template tanımlarını kontrol eder
3. Template adı eşleşirse, o template'in connection check item'larını ve master item'larını kullanır
4. Eşleşme yoksa, global pattern'leri kullanır

### Item Kontrolü

Her host için:

1. Template'lerden connection check item'ları tespit edilir
2. Bu item'ların veri durumu kontrol edilir
3. Master item'lar kontrol edilir (varsa)
4. Sonuçlar analiz edilir ve raporlanır

## 📊 Öncelik Seviyeleri

- **high**: Kritik item'lar (mutlaka çalışmalı)
- **medium**: Önemli item'lar
- **low**: Opsiyonel item'lar

Öncelik seviyeleri, connectivity score hesaplamasında ağırlık olarak kullanılır.

## 🔗 İlgili Dokümanlar

- [Usage Guide](USAGE.md)
- [Development Plan](../development/DEVELOPMENT_PLAN.md)
- [Schema Documentation](../design/SCHEMA.md)
