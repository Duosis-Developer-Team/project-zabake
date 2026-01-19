# Konfigürasyon Verileri ve AWX Entegrasyon Kılavuzu

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Netbox-Zabbix Entegrasyonu](#netbox-zabbix-entegrasyonu)
- [Zabbix Monitoring](#zabbix-monitoring)
- [Konfigürasyon Dosyaları Karşılaştırması](#konfigürasyon-dosyaları-karşılaştırması)
- [AWX Entegrasyon Stratejileri](#awx-entegrasyon-stratejileri)
- [Best Practices](#best-practices)

---

## 🎯 Genel Bakış

Bu dokümantasyon, project-zabake repository'sindeki iki ana projenin konfigürasyon verilerinin nerede tutulduğunu ve Ansible AWX ile nasıl kullanılabileceğini açıklar:

1. **zabbix-netbox**: Netbox'tan Zabbix'e cihaz senkronizasyonu
2. **zabbix-monitoring**: Zabbix tag-based connectivity monitoring

### Temel Konfigürasyon Yönetim Yaklaşımları

Her iki proje için 3 farklı konfigürasyon seviyesi bulunmaktadır:

| Seviye | Konum | Amaç | AWX'te Yönetim |
|--------|-------|------|----------------|
| **1. Mapping Files** | `mappings/` klasörleri | Sabit mapping'ler (templates, device types, datacenters) | SCM (Git) üzerinden, kod değişikliği gerektirir |
| **2. Default Variables** | `roles/*/defaults/main.yml` | Varsayılan değerler ve parametreler | SCM (Git) üzerinden |
| **3. Runtime Variables** | Playbook execution time | Çalışma zamanı parametreleri (credentials, URL'ler, filters) | AWX Extra Variables veya Survey |

---

## 🔄 Netbox-Zabbix Entegrasyonu

### 1️⃣ Konfigürasyon Dosyaları

#### A. Mapping Files (Git Repo - `zabbix-netbox/mappings/`)

Bu dosyalar **statik konfigürasyon verilerini** içerir ve genellikle değişmez. Git repository'de tutulur.

##### `templates.yml`
**Amaç:** Netbox device type'larını Zabbix template'lerine eşleştirir.

**Konum:** `zabbix-netbox/mappings/templates.yml`

**İçerik Yapısı:**
```yaml
DEVICE_TYPE:
  - name: "Zabbix Template Name"
    type: "snmpv2|snmpv3|api|agent"
    macros:  # Opsiyonel - API-based template'ler için
      "{$MACRO_NAME}": "value"
      "{$ANOTHER_MACRO}": "{HOST.IP}"  # {HOST.IP} otomatik inject edilir
```

**Örnek:**
```yaml
Dell IPMI:
  - name: BLT - Dell iDRAC SNMP
    type: snmpv2
    macros:
      "{$IDRAC.API.URL}": "https://{HOST.IP}/"
      "{$IDRAC.PASSWORD}": "A!UCZcCUSRwZ"
      "{$IDRAC.USER}": "root"

Fortigate Firewall:
  - name: FortiGate by HTTP
    type: api
    macros:
      "{$FORTIGATE.API.URL}": "https://{HOST.IP}/"
      "{$FORTIGATE.API.KEY}": "change_me"
```

**AWX'te Kullanım:**
- SCM Project'ten otomatik çekilir
- Değişiklik için kod değişikliği ve commit gerekir
- Template isimleri Zabbix'teki template'lerle birebir eşleşmelidir

---

##### `template_types.yml`
**Amaç:** Template type'larına (snmpv2, snmpv3, api, agent) göre interface konfigürasyonlarını tanımlar.

**Konum:** `zabbix-netbox/mappings/template_types.yml`

**İçerik Yapısı:**
```yaml
<type_name>:
  interface:
    type: <1=agent, 2=snmp>
    port: <port_number>
    useip: <0|1>
    dns: ""
    details:
      version: <2|3>  # SNMP version
      community: "community_string"  # SNMPv2 için
      # SNMPv3 için authentication detayları
      securityname: "username"
      securitylevel: <0|1|2>
      authprotocol: <0|1>
      authpassphrase: "password"
      privprotocol: <0|1>
      privpassphrase: "password"
```

**Örnek:**
```yaml
snmpv2:
  interface:
    type: 2
    port: 161
    useip: 1
    dns: ""
    details:
      version: 2
      bulk: 1
      community: "Bltdcsnmp"

snmpv3:
  interface:
    type: 2
    port: 161
    useip: 1
    dns: ""
    details:
      version: 3
      bulk: 1
      securityname: "readonly"
      securitylevel: 2
      authprotocol: 1
      authpassphrase: "U357a3D9Tw3928aV"
      privprotocol: 1
      privpassphrase: "ZFlK0O44y412!!"

api:
  interface: null
```

**AWX'te Kullanım:**
- SCM Project'ten otomatik çekilir
- SNMP community string'leri ve credentials bu dosyada tanımlanır
- Değişiklik için kod değişikliği gerekir

---

##### `datacenters.yml`
**Amaç:** Netbox location/datacenter bilgilerini Zabbix proxy/proxy group'larına eşleştirir.

**Konum:** `zabbix-netbox/mappings/datacenters.yml`

**İçerik Yapısı:**
```yaml
<Location_Name>:
  proxy_groupid: <group_id>
  # veya
  proxyid: <proxy_id>
```

**Örnek:**
```yaml
DEMO 2-3:
  proxy_groupid: 1

Otomasyon Test:
  proxy_groupid: 4
```

**AWX'te Kullanım:**
- SCM Project'ten otomatik çekilir
- Datacenter ID'leri Zabbix proxy group ID'leri ile eşleştirilir

---

##### `netbox_device_type_mapping.yml`
**Amaç:** Netbox'tan hangi cihazların Zabbix'e senkronize edileceğini filtreler.

**Konum:** `zabbix-netbox/mappings/netbox_device_type_mapping.yml`

**İçerik Yapısı:**
```yaml
mappings:
  - device_type: "Device Type Name"
    conditions:
      device_role: "ROLE_NAME"
      manufacturer: "MANUFACTURER"  # veya ["MAN1", "MAN2"]
      model_contains: ["keyword"]  # Opsiyonel
      model_suffix: "suffix"  # Opsiyonel
    priority: 1
```

**Örnek:**
```yaml
mappings:
  - device_type: "Lenovo IPMI"
    conditions:
      device_role: "HOST"
      manufacturer: "LENOVO"
    priority: 1

  - device_type: "Inspur M6"
    conditions:
      device_role: "HOST"
      manufacturer: ["INSPUR", "Inspur"]
      model_contains: ["M6"]
      model_suffix: "M6"
    priority: 1
```

**AWX'te Kullanım:**
- SCM Project'ten otomatik çekilir
- Device filtering kurallarını belirler

---

#### B. Default Variables (Git Repo)

**Konum:** `zabbix-netbox/playbooks/roles/netbox_zabbix_sync/defaults/main.yml`

**Amaç:** Role için varsayılan değerleri tanımlar.

**İçerik:**
```yaml
# Netbox connection settings
netbox_url: ""
netbox_token: ""
netbox_verify_ssl: false

# Zabbix connection settings
zabbix_url: ""
zabbix_user: ""
zabbix_password: ""
zabbix_validate_certs: false

# Device filtering
device_limit: 0  # 0 = no limit
location_filter: ""  # e.g., "DC11", "ISTANBUL"

# Mapping file paths (otomatik resolve edilir)
templates_map_path: "{{ playbook_dir }}/../mappings/templates.yml"
datacenters_map_path: "{{ playbook_dir }}/../mappings/datacenters.yml"
device_type_mapping_path: "{{ playbook_dir }}/../mappings/netbox_device_type_mapping.yml"

# Email notification settings
mail_smtp_host: "10.34.8.191"
mail_smtp_port: 587
mail_smtp_username: ""
mail_smtp_password: ""
mail_smtp_use_tls: false
mail_recipients: []  # Playbook input olarak verilmeli
mail_from: "infrareport@alert.bulutistan.com"
```

**AWX'te Override Edilmesi Gereken Değerler:**
- `netbox_url`, `netbox_token`
- `zabbix_url`, `zabbix_user`, `zabbix_password`
- `mail_recipients` (opsiyonel)
- `location_filter` (opsiyonel)

---

#### C. Runtime Variables (AWX Extra Variables)

**Konum:** AWX Job Template → Extra Variables

**Amaç:** Çalışma zamanında playbook'a parametre geçirme.

**Minimal Gerekli Variables:**
```yaml
---
netbox_url: "https://loki.bulutistan.com/"
netbox_token: "your_netbox_token"
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"
```

**Tam Örnek (Tüm Opsiyonlarla):**
```yaml
---
# Netbox Credentials (Required)
netbox_url: "https://loki.bulutistan.com/"
netbox_token: "your_netbox_token"
netbox_verify_ssl: false

# Zabbix Credentials (Required)
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"
zabbix_validate_certs: false

# Device Filtering (Optional)
device_limit: 0  # 0 = all devices
location_filter: "DC11"  # Specific location

# Email Notifications (Optional)
mail_recipients:
  - "admin@example.com"
  - "team@example.com"
```

---

### 2️⃣ AWX Entegrasyonu

#### Job Template Oluşturma

1. **SCM Project Oluşturma**
   - **Name:** `project-zabake`
   - **SCM Type:** Git
   - **SCM URL:** Repository URL
   - **SCM Branch:** `development` veya `main`
   - **Update on Launch:** ✅ (Önerilir)

2. **Inventory Oluşturma**
   - **Name:** `localhost-inventory`
   - **Host:** `localhost`
   - **Variables:** (Boş bırakılabilir)

3. **Credentials Oluşturma**

   **a) Netbox Credential (Custom Credential Type)**
   - **Name:** `Netbox Loki Token`
   - **Credential Type:** Custom
   - **Input Configuration:**
     ```json
     {
       "fields": [{
         "id": "netbox_token",
         "type": "string",
         "label": "Netbox Token",
         "secret": true
       }]
     }
     ```
   - **Injector Configuration:**
     ```json
     {
       "extra_vars": {
         "netbox_token": "{{ netbox_token }}"
       }
     }
     ```

   **b) Zabbix Credential**
   - **Name:** `Zabbix API Credentials`
   - **Credential Type:** Custom
   - **Input Configuration:**
     ```json
     {
       "fields": [
         {
           "id": "zabbix_user",
           "type": "string",
           "label": "Zabbix Username"
         },
         {
           "id": "zabbix_password",
           "type": "string",
           "label": "Zabbix Password",
           "secret": true
         }
       ]
     }
     ```
   - **Injector Configuration:**
     ```json
     {
       "extra_vars": {
         "zabbix_user": "{{ zabbix_user }}",
         "zabbix_password": "{{ zabbix_password }}"
       }
     }
     ```

4. **Job Template Oluşturma**
   - **Name:** `Netbox to Zabbix Sync`
   - **Job Type:** Run
   - **Inventory:** `localhost-inventory`
   - **Project:** `project-zabake`
   - **Playbook:** `zabbix-netbox/playbooks/netbox_zabbix_sync.yaml`
   - **Credentials:** 
     - Netbox Loki Token
     - Zabbix API Credentials
   - **Extra Variables:**
     ```yaml
     ---
     netbox_url: "https://loki.bulutistan.com/"
     zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
     location_filter: "DC11"  # Opsiyonel
     mail_recipients:
       - "admin@example.com"
     ```
   - **Options:**
     - ✅ Enable Concurrent Jobs (çakışan çalışmalar için)

5. **Survey Ekleme (Opsiyonel - Dinamik Input için)**
   
   Survey ekleyerek kullanıcının her çalıştırmada parametreleri girmesini sağlayabilirsiniz:
   
   - **Location Filter:**
     - **Prompt:** Enter location filter (optional)
     - **Answer Variable Name:** `location_filter`
     - **Answer Type:** Text
     - **Required:** ❌
     - **Default:** ` ` (boş)
   
   - **Device Limit:**
     - **Prompt:** Limit number of devices (0 = all)
     - **Answer Variable Name:** `device_limit`
     - **Answer Type:** Integer
     - **Required:** ✅
     - **Default:** `0`
   
   - **Send Email:**
     - **Prompt:** Send email notification?
     - **Answer Variable Name:** `send_email`
     - **Answer Type:** Multiple Choice (single select)
     - **Choices:**
       - `true`
       - `false`
     - **Default:** `false`

---

### 3️⃣ Konfigürasyon Değişiklik Workflow'u

#### Senaryo 1: Yeni Template Ekleme

**Durum:** Zabbix'e yeni bir template eklenmiş ve bu template'in device type mapping'e eklenmesi gerekiyor.

**Adımlar:**
1. `zabbix-netbox/mappings/templates.yml` dosyasını düzenle:
   ```yaml
   New Device Type:
     - name: "New Zabbix Template Name"
       type: snmpv2
       macros:
         "{$CUSTOM_MACRO}": "value"
   ```
2. `zabbix-netbox/mappings/netbox_device_type_mapping.yml` dosyasını düzenle:
   ```yaml
   mappings:
     - device_type: "New Device Type"
       conditions:
         device_role: "HOST"
         manufacturer: "MANUFACTURER_NAME"
       priority: 1
   ```
3. Değişiklikleri commit et ve push et
4. AWX'te Job Template'i çalıştır (SCM update otomatik olacak)

**AWX'te Değişiklik Gerekmez** - Mapping dosyaları SCM üzerinden otomatik güncellenir.

---

#### Senaryo 2: Yeni Datacenter/Location Ekleme

**Durum:** Yeni bir datacenter eklenmiş ve Zabbix proxy mapping'e eklenmesi gerekiyor.

**Adımlar:**
1. `zabbix-netbox/mappings/datacenters.yml` dosyasını düzenle:
   ```yaml
   New DC Name:
     proxy_groupid: 5
   ```
2. Değişiklikleri commit et ve push et
3. AWX'te Job Template'i çalıştır

---

#### Senaryo 3: SNMP Credentials Güncelleme

**Durum:** SNMP community string veya SNMPv3 credentials değişti.

**Adımlar:**
1. `zabbix-netbox/mappings/template_types.yml` dosyasını düzenle:
   ```yaml
   snmpv2:
     interface:
       details:
         community: "NewCommunityString"
   
   snmpv3:
     interface:
       details:
         authpassphrase: "NewAuthPassword"
         privpassphrase: "NewPrivPassword"
   ```
2. **SECURITY WARNING:** Credentials'ları plain text olarak saklamak güvenli değildir. Ansible Vault kullanın veya AWX'te Credential Management kullanın.
3. Değişiklikleri commit et ve push et

**Daha Güvenli Alternatif:**
- Credentials'ları AWX Custom Credentials olarak sakla
- Mapping dosyasında placeholder kullan
- Playbook çalışırken AWX'ten inject et

---

#### Senaryo 4: Runtime Parametreleri Değiştirme

**Durum:** Sadece belirli bir location'ı veya limit sayıda cihazı senkronize etmek istiyorsunuz.

**Adımlar:**
1. AWX Job Template'i aç
2. Extra Variables'ı güncelle veya Survey kullan:
   ```yaml
   location_filter: "ISTANBUL"
   device_limit: 50
   ```
3. Job'ı çalıştır

**Kod Değişikliği Gerekmez** - Runtime parametreler AWX üzerinden değiştirilebilir.

---

### 4️⃣ Güvenli Credential Yönetimi

#### Yaklaşım 1: AWX Credentials (Önerilir)

```yaml
# Job Template Extra Variables
netbox_url: "https://loki.bulutistan.com/"
# netbox_token AWX credential'ından inject edilir

zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
# zabbix_user ve zabbix_password AWX credential'ından inject edilir
```

#### Yaklaşım 2: Ansible Vault (Git Repo için)

```bash
# Vault file oluştur
ansible-vault create zabbix-netbox/vars/vault.yml

# İçerik
vault_netbox_token: "secret_token"
vault_zabbix_password: "secret_password"
```

```yaml
# Playbook'ta kullan
netbox_token: "{{ vault_netbox_token }}"
zabbix_password: "{{ vault_zabbix_password }}"
```

**AWX'te Vault Password Credential ekle:**
- Credential Type: Vault
- Vault Password: `your_vault_password`

---

---

## 📊 Zabbix Monitoring

### 1️⃣ Konfigürasyon Dosyaları

#### A. Mapping Files (Git Repo - `zabbix-monitoring/mappings/`)

##### `templates.yml` (LEGACY - Artık Kullanılmıyor)

**Amaç:** Template-based connectivity monitoring için item mapping'leri (DEPRECATED).

**Konum:** `zabbix-monitoring/mappings/templates.yml`

**Not:** Tag-based monitoring modu ile bu dosya artık kullanılmamaktadır. Tag-based modda, Zabbix'te item'lara `connection status` tag'i eklenerek monitoring yapılır.

**Legacy İçerik Yapısı:**
```yaml
templates:
  - name: "Template Name"
    connection_check_items:
      - key: "item.key"
        name: "Item Name"
        required: true|false
        priority: "high|medium|low"
    master_items:
      - key: "master.item.key"
        name: "Master Item Name"
```

**AWX'te Kullanım:**
- **Tag-based mod kullanın** (default) - Bu dosya gerekmez
- Legacy mode için: `use_legacy_mode: true` set edilmeli (Deprecated, Haziran 2026'da kaldırılacak)

---

#### B. Default Variables (Git Repo)

**Konum:** `zabbix-monitoring/playbooks/roles/zabbix_monitoring/defaults/main.yml`

**İçerik:**
```yaml
# ========================================
# Zabbix Connection Settings (Required from AWX)
# ========================================
zabbix_url: ""  # e.g., "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: ""  # e.g., "Admin"
zabbix_password: ""  # Use AWX Credentials or Vault

# ========================================
# Tag-Based Connectivity Settings
# ========================================
connection_tag: "connection status"  # Tag name to identify connection items
history_limit: 10  # Number of history values to analyze
threshold_percentage: 70.0  # Minimum acceptable connectivity %
host_groups: ""  # Filter by host groups (empty = all)

# ========================================
# Email Notification Settings
# ========================================
send_email: true
smtp_server: "localhost"
smtp_port: 25
smtp_username: ""
smtp_password: ""
email_from: "zabbix-monitoring@example.com"
email_to: "admin@example.com"

# ========================================
# Debug and Logging Settings
# ========================================
debug_enabled: false
debug_output_dir: "/tmp/zabbix_monitoring_output"
log_level: "INFO"
log_file: "/tmp/zabbix_tag_based_monitoring.log"

# ========================================
# Legacy Mode Settings (DEPRECATED)
# ========================================
use_legacy_mode: false  # DO NOT USE - Will be removed in June 2026

# ========================================
# Advanced Settings
# ========================================
max_data_age: 3600  # seconds
inactive_threshold: 7200
master_item_threshold: 1800
min_connectivity_score: 0.8
```

---

#### C. Runtime Variables (AWX Extra Variables)

##### Minimal Configuration

**Konum:** AWX Job Template → Extra Variables

```yaml
---
# Zabbix API Connection (REQUIRED)
zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"
```

##### Tam Configuration (Email Notification ile)

```yaml
---
# Zabbix API Connection (REQUIRED)
zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"

# Email Notification (OPTIONAL)
send_email: true
smtp_server: "smtp.example.com"
smtp_port: 25
email_from: "zabbix-monitoring@example.com"
email_to: "admin@example.com"

# Tag-Based Connectivity Settings (OPTIONAL)
connection_tag: "connection status"
history_limit: 10
threshold_percentage: 70.0
host_groups: ""  # Empty = all hosts

# Debug Settings (OPTIONAL)
debug_enabled: true
log_level: "INFO"
```

##### Advanced Configuration (Filtering)

```yaml
---
zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"

# Filter by specific host groups
host_groups: "Linux Servers,Windows Servers"

# Custom threshold
threshold_percentage: 80.0

# More history for analysis
history_limit: 20

# Custom connection tag
connection_tag: "connectivity_check"
```

---

### 2️⃣ AWX Entegrasyonu

#### Job Template Oluşturma

1. **SCM Project (Önceden Oluşturulmuş)**
   - **Name:** `project-zabake`
   - **SCM Branch:** `development` veya `main`

2. **Inventory (Önceden Oluşturulmuş)**
   - **Name:** `localhost-inventory`

3. **Credentials (Önceden Oluşturulmuş veya Yeni)**
   - **Zabbix API Credentials** (Custom credential kullan)

4. **Job Template Oluşturma**
   - **Name:** `Zabbix Tag-Based Connectivity Monitoring`
   - **Job Type:** Run
   - **Inventory:** `localhost-inventory`
   - **Project:** `project-zabake`
   - **Playbook:** `zabbix-monitoring/playbooks/zabbix_tag_based_monitoring.yaml`
   - **Credentials:** Zabbix API Credentials
   - **Extra Variables:**
     ```yaml
     ---
     zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
     send_email: true
     email_to: "admin@example.com"
     threshold_percentage: 70.0
     ```

5. **Survey Ekleme (Opsiyonel)**

   - **Email Recipient:**
     - **Prompt:** Email Recipient
     - **Answer Variable Name:** `email_to`
     - **Answer Type:** Text
     - **Required:** ❌
     - **Default:** `admin@example.com`
   
   - **Send Email:**
     - **Prompt:** Send email notification?
     - **Answer Variable Name:** `send_email`
     - **Answer Type:** Multiple Choice
     - **Choices:** `true`, `false`
     - **Default:** `true`
   
   - **Threshold Percentage:**
     - **Prompt:** Connectivity Threshold (%)
     - **Answer Variable Name:** `threshold_percentage`
     - **Answer Type:** Integer
     - **Required:** ✅
     - **Default:** `70`
     - **Min:** `0`
     - **Max:** `100`
   
   - **Host Groups Filter:**
     - **Prompt:** Filter by host groups (comma-separated, empty = all)
     - **Answer Variable Name:** `host_groups`
     - **Answer Type:** Text
     - **Required:** ❌
     - **Default:** ` ` (boş)
   
   - **Debug Mode:**
     - **Prompt:** Enable debug mode?
     - **Answer Variable Name:** `debug_enabled`
     - **Answer Type:** Multiple Choice
     - **Choices:** `true`, `false`
     - **Default:** `false`

---

### 3️⃣ Tag-Based Monitoring Kullanımı

#### Zabbix'te Item Tagging

Tag-based monitoring modunda, **konfigürasyon dosyası gerekmez**. Sadece Zabbix'te item'lara tag ekleyin:

1. **Zabbix UI'da:**
   - Configuration → Hosts
   - Bir host seç → Items
   - Connectivity item'ı seç (örn: "ICMP ping", "SNMP availability")
   - Tags sekmesine git
   - **Tag Name:** `connection status`
   - **Tag Value:** (boş bırak)
   - Save

2. **Toplu Tag Ekleme (Çok Sayıda Item için):**
   - Configuration → Hosts
   - Mass update kullan
   - Birden fazla item seç
   - Tags → Add tags
   - `connection status` tag'ini ekle

3. **Template Seviyesinde Tag Ekleme:**
   - Configuration → Templates
   - Template'i seç → Items
   - Connectivity item'ları seç
   - Tag ekle
   - Template'i kullanan tüm host'larda otomatik tag eklenir

#### Monitoring Workflow

1. **Item'lar tag'lenir** (Zabbix UI)
2. **AWX Job çalıştırılır** (schedule veya manual)
3. **Playbook:**
   - Zabbix API'den `connection status` tag'li item'ları toplar
   - Her item için son N (default: 10) history değerini analiz eder
   - Connectivity score hesaplar (başarılı değer sayısı / toplam değer sayısı)
   - Threshold altındaki item'ları raporlar
   - Connection item'ı olmayan host'ları tespit eder
   - Email raporu gönderir (opsiyonel)

#### Örnek Rapor Çıktısı

```
PROBLEMATIC ITEMS (Below 70% Threshold)
========================================
Host             Item                Score   Status
---------------------------------------------------------
Server-A         SNMP Availability   45%     CRITICAL
Server-A         Agent Status        60%     WARNING
Server-B         ICMP Ping           55%     WARNING

HOSTS WITHOUT CONNECTION ITEMS
========================================
- Server-C
- Server-D
```

---

### 4️⃣ Konfigürasyon Değişiklik Workflow'u

#### Senaryo 1: Threshold Değiştirme

**Durum:** Connectivity threshold'unu %70'ten %80'e çıkarmak istiyorsunuz.

**Adımlar:**
1. AWX Job Template'i aç
2. Extra Variables güncelle:
   ```yaml
   threshold_percentage: 80.0
   ```
3. Job'ı çalıştır

**Kod Değişikliği Gerekmez.**

---

#### Senaryo 2: Email Recipient Değiştirme

**Durum:** Email'leri farklı bir adrese göndermek istiyorsunuz.

**Adımlar:**
1. AWX Job Template'i aç
2. Extra Variables güncelle:
   ```yaml
   email_to: "new_admin@example.com"
   # Veya birden fazla recipient:
   send_email: true
   smtp_server: "smtp.example.com"
   email_to: "team@example.com"
   ```
3. Job'ı çalıştır

**Kod Değişikliği Gerekmez.**

---

#### Senaryo 3: Belirli Host Group'ları Filtreleme

**Durum:** Sadece "Production Servers" ve "Critical Infrastructure" host group'larını monitor etmek istiyorsunuz.

**Adımlar:**
1. AWX Job Template'i aç
2. Extra Variables güncelle:
   ```yaml
   host_groups: "Production Servers,Critical Infrastructure"
   ```
3. Job'ı çalıştır

**Kod Değişikliği Gerekmez.**

---

#### Senaryo 4: Custom Tag Name Kullanma

**Durum:** Default `connection status` tag'i yerine `connectivity_check` tag'ini kullanmak istiyorsunuz.

**Adımlar:**
1. Zabbix'te item'lara `connectivity_check` tag'ini ekle
2. AWX Job Template'i aç
3. Extra Variables güncelle:
   ```yaml
   connection_tag: "connectivity_check"
   ```
4. Job'ı çalıştır

**Kod Değişikliği Gerekmez.**

---

#### Senaryo 5: History Limit Artırma

**Durum:** Daha doğru analiz için son 20 değeri kontrol etmek istiyorsunuz.

**Adımlar:**
1. AWX Job Template'i aç
2. Extra Variables güncelle:
   ```yaml
   history_limit: 20
   ```
3. Job'ı çalıştır

**Kod Değişikliği Gerekmez.**

---

---

## 📊 Konfigürasyon Dosyaları Karşılaştırması

### Netbox-Zabbix vs Zabbix-Monitoring

| Özellik | Netbox-Zabbix | Zabbix-Monitoring |
|---------|---------------|-------------------|
| **Amaç** | Netbox → Zabbix cihaz senkronizasyonu | Zabbix connectivity monitoring |
| **Mapping Dosyaları** | ✅ 4 dosya (templates, template_types, datacenters, netbox_device_type_mapping) | ❌ Artık kullanılmıyor (tag-based) |
| **Konfigürasyon Yaklaşımı** | Mapping-driven (Git-based) | Tag-driven (Zabbix UI) |
| **Runtime Variables** | Netbox + Zabbix credentials, location filter | Zabbix credentials, threshold, email |
| **Credential Requirement** | Netbox token, Zabbix user/pass | Zabbix user/pass |
| **AWX Survey Kullanımı** | Location filter, device limit, send email | Threshold, host groups, email recipient |
| **Kod Değişikliği Gerektiren Değişiklikler** | Template mapping, device type mapping, datacenter mapping, SNMP credentials | ❌ Hiçbiri (tüm değişiklikler runtime) |
| **UI-Based Değişiklikler** | ❌ Mapping dosyaları gerekli | ✅ Zabbix UI'da tag ekleme |
| **Email Notification** | ✅ (başarısız işlemler için) | ✅ (connectivity raporu için) |

---

### Konfigürasyon Tipi Karşılaştırması

| Konfigürasyon Tipi | Netbox-Zabbix | Zabbix-Monitoring | Nerede Değiştirilir |
|-------------------|---------------|-------------------|---------------------|
| **Sabit Mapping'ler** | ✅ (templates.yml, template_types.yml, datacenters.yml, netbox_device_type_mapping.yml) | ❌ | Git repo → Commit required |
| **Connection Credentials** | ✅ Netbox + Zabbix | ✅ Zabbix | AWX Credentials veya Extra Variables |
| **Filtering Rules** | ✅ (location_filter, device_limit) | ✅ (host_groups) | AWX Extra Variables |
| **Notification Settings** | ✅ (email recipients, SMTP) | ✅ (email recipients, SMTP, threshold) | AWX Extra Variables |
| **Runtime Behavior** | ✅ (device_limit, location_filter) | ✅ (threshold, history_limit, connection_tag) | AWX Extra Variables |
| **Item Selection** | Mapping file (device type conditions) | Tag-based (Zabbix UI) | Mapping file (Git) vs Zabbix UI |

---

---

## 🚀 AWX Entegrasyon Stratejileri

### Strateji 1: Minimal Configuration (Basit Kullanım)

**Amaç:** En az değişkenle hızlıca çalıştırma.

#### Netbox-Zabbix
```yaml
---
netbox_url: "https://loki.bulutistan.com/"
netbox_token: "{{ vault_netbox_token }}"
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "{{ vault_zabbix_user }}"
zabbix_password: "{{ vault_zabbix_password }}"
```

#### Zabbix-Monitoring
```yaml
---
zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "{{ vault_zabbix_user }}"
zabbix_password: "{{ vault_zabbix_password }}"
```

**Avantajlar:**
- Hızlı kurulum
- Minimum değişken
- Default ayarlar kullanılır

**Dezavantajlar:**
- Tüm cihazlar işlenir (filtering yok)
- Email notification yok

---

### Strateji 2: Survey-Based Configuration (Dinamik Input)

**Amaç:** Her çalıştırmada kullanıcıdan input almak.

#### Netbox-Zabbix Survey
- Location Filter (text)
- Device Limit (integer)
- Send Email Notification (bool)
- Email Recipients (text)

#### Zabbix-Monitoring Survey
- Host Groups Filter (text)
- Threshold Percentage (integer, 0-100)
- Send Email (bool)
- Email Recipient (text)
- Debug Mode (bool)

**Avantajlar:**
- Kullanıcı dostu
- Farklı senaryolar için esneklik
- GUI üzerinden kolay değişiklik

**Dezavantajlar:**
- Her çalıştırmada input gerekir
- Automation için uygun değil

---

### Strateji 3: Multi-Environment Setup (Farklı Ortamlar)

**Amaç:** Dev, Test, Prod ortamları için farklı job template'ler.

#### Örnek: Prod Netbox-Zabbix
```yaml
---
netbox_url: "https://loki.bulutistan.com/"
netbox_token: "{{ vault_netbox_prod_token }}"
zabbix_url: "https://zabbix.prod.example.com/api_jsonrpc.php"
zabbix_user: "{{ vault_zabbix_prod_user }}"
zabbix_password: "{{ vault_zabbix_prod_password }}"
device_limit: 0  # All devices
mail_recipients:
  - "prod_team@example.com"
  - "infrastructure@example.com"
```

#### Örnek: Test Netbox-Zabbix
```yaml
---
netbox_url: "https://loki.test.bulutistan.com/"
netbox_token: "{{ vault_netbox_test_token }}"
zabbix_url: "https://zabbix.test.example.com/api_jsonrpc.php"
zabbix_user: "{{ vault_zabbix_test_user }}"
zabbix_password: "{{ vault_zabbix_test_password }}"
device_limit: 10  # Limited for testing
location_filter: "Test DC"
mail_recipients:
  - "test_team@example.com"
```

**Avantajlar:**
- Ortam izolasyonu
- Farklı credential'lar
- Güvenli prod deployment

---

### Strateji 4: Scheduled Automation (Periyodik Çalıştırma)

**Amaç:** Düzenli aralıklarla otomatik çalıştırma.

#### AWX Schedule Oluşturma

1. Job Template → Schedules → Add
2. **Name:** `Daily Netbox Sync`
3. **Start Date/Time:** `2026-01-20 02:00:00`
4. **Repeat Frequency:** Every 1 Days
5. **Variables:** (Extra Variables Override)
   ```yaml
   ---
   location_filter: ""  # All locations
   mail_recipients:
     - "noc@example.com"
   ```

#### Örnek Schedule'lar

| Schedule | Frequency | Purpose | Variables |
|----------|-----------|---------|-----------|
| **Full Sync** | Daily 02:00 | Tüm cihazları senkronize et | `device_limit: 0`, `location_filter: ""` |
| **DC11 Sync** | Every 4 hours | DC11 cihazlarını senkronize et | `location_filter: "DC11"` |
| **Connectivity Check** | Hourly | Connectivity monitoring | `threshold_percentage: 70`, `send_email: true` |
| **Weekly Report** | Weekly (Monday 09:00) | Haftalık connectivity raporu | `threshold_percentage: 80`, `send_email: true` |

**Avantajlar:**
- Otomatik çalışma
- Düzenli güncellemeler
- İnsan müdahalesi gerektirmez

---

### Strateji 5: Workflow Template (Multi-Step)

**Amaç:** Birden fazla job'ı sıralı veya paralel çalıştırma.

#### Örnek Workflow: Full Infrastructure Sync

```
Workflow Template: "Full Infrastructure Sync"

┌──────────────────────┐
│ Netbox to Zabbix Sync│
└──────────┬───────────┘
           │ On Success
           ▼
┌──────────────────────┐
│ Connectivity Check   │
└──────────┬───────────┘
           │ On Success
           ▼
┌──────────────────────┐
│ Send Summary Report  │
└──────────────────────┘
```

**Node Configurations:**

1. **Netbox to Zabbix Sync:**
   - Job Template: `Netbox to Zabbix Sync`
   - Variables:
     ```yaml
     device_limit: 0
     mail_recipients: []  # No email for intermediate step
     ```

2. **Connectivity Check:**
   - Job Template: `Zabbix Tag-Based Connectivity Monitoring`
   - Variables:
     ```yaml
     send_email: false  # Will send final report
     threshold_percentage: 70
     ```

3. **Send Summary Report:**
   - Job Template: `Send Infrastructure Summary`
   - Variables:
     ```yaml
     email_to: "infrastructure_team@example.com"
     ```

**Avantajlar:**
- Complex automation
- Error handling
- Conditional execution
- Comprehensive reporting

---

---

## ✅ Best Practices

### 1. Credential Management

#### ✅ DO
- AWX Custom Credentials kullan
- Sensitive data'yı Ansible Vault'ta sakla
- Environment-specific credentials oluştur (dev, test, prod)
- Credential rotation policy uygula

#### ❌ DON'T
- Plain text credentials Git'e commit etme
- Extra Variables'da plain text password kullanma
- Tüm ortamlarda aynı credentials kullanma

---

### 2. Mapping Files

#### ✅ DO (Netbox-Zabbix için)
- Mapping file'ları Git'te version control et
- Template isimleri Zabbix'teki template'lerle birebir eşleştir
- SNMP credentials için Ansible Vault kullan
- Değişiklikleri test ortamında test et

#### ❌ DON'T
- Mapping file'ları manuel olarak AWX'te güncelleme
- Template isimleri typo yapma
- Plain text SNMP credentials kullanma

---

### 3. Tag-Based Monitoring (Zabbix-Monitoring için)

#### ✅ DO
- Template seviyesinde tag ekle (tüm host'lara otomatik yayılır)
- Tag naming convention kullan (örn: `connection status`)
- Critical item'ları öncelikle tag'le
- Düzenli olarak tag'leri audit et

#### ❌ DON'T
- Her host'ta manuel tag ekleme (template kullan)
- Farklı tag isimleri kullanma (consistency önemli)
- Eski template-based mapping file'ları kullanma

---

### 4. AWX Job Template Design

#### ✅ DO
- Environment-specific job template'ler oluştur
- Survey kullanarak kullanıcı deneyimini iyileştir
- Extra Variables'da sane default'lar kullan
- Job template'lere açıklayıcı isimler ve description'lar ekle
- Concurrent job execution'ı enable et (gerekirse)

#### ❌ DON'T
- Tek bir job template tüm ortamlar için kullanma
- Required olmayan survey field'ları zorunlu yapma
- Default'ları boş bırakma

---

### 5. Error Handling ve Monitoring

#### ✅ DO
- Email notification'ı enable et
- Debug mode'u geliştirme sırasında kullan
- Log file'ları düzenli olarak kontrol et
- Failed job'ları analiz et
- Notification recipient listesini güncel tut

#### ❌ DON'T
- Email notification'ı disable etme (production'da)
- Debug file'ları production'da saklamama
- Error'ları ignore etme

---

### 6. Scheduling

#### ✅ DO
- Düşük kullanım saatlerinde schedule et (örn: 02:00)
- Farklı job'lar için farklı schedule'lar kullan
- Schedule conflict'lerini önle
- Maintenance window'ları göz önünde bulundur

#### ❌ DON'T
- Peak saatlerde sync job'ları çalıştırma
- Çok sık schedule etme (gereksiz yük)
- Schedule'ları dokümante etmeme

---

### 7. Testing ve Validation

#### ✅ DO
- Her değişikliği test ortamında test et
- Device limit kullanarak sınırlı test yap
- Debug mode enable ederek çıktıları incele
- Survey kullanarak farklı senaryoları test et

#### ❌ DON'T
- Direkt production'da test etme
- Tüm cihazları ilk testte işleme
- Test sonuçlarını dokümante etmeme

---

### 8. Documentation

#### ✅ DO
- Mapping file değişikliklerini dokümante et
- AWX job template konfigürasyonlarını kaydet
- Troubleshooting adımlarını dokümante et
- Change log tut

#### ❌ DON'T
- Undocumented değişiklikler yapma
- Eski dokümantasyonu güncellememe

---

---

## 📞 Troubleshooting

### Netbox-Zabbix Sorunları

#### Hata: "Template not found in Zabbix"
**Neden:** `templates.yml`'daki template ismi Zabbix'teki template ismiyle eşleşmiyor.

**Çözüm:**
1. Zabbix UI → Configuration → Templates'te template ismini kontrol et
2. `templates.yml` dosyasında template ismini düzelt
3. Commit ve push et

#### Hata: "Device type mapping not found"
**Neden:** Netbox'taki cihaz tipi `netbox_device_type_mapping.yml`'de tanımlanmamış.

**Çözüm:**
1. Netbox'ta device type, manufacturer, model bilgilerini kontrol et
2. `netbox_device_type_mapping.yml`'e mapping ekle
3. Commit ve push et

#### Hata: "Proxy group not found"
**Neden:** `datacenters.yml`'deki proxy group ID Zabbix'te mevcut değil.

**Çözüm:**
1. Zabbix UI → Administration → Proxies'te proxy group ID'yi kontrol et
2. `datacenters.yml` dosyasını güncelle
3. Commit ve push et

---

### Zabbix-Monitoring Sorunları

#### Hata: "No items with tag 'connection status' found"
**Neden:** Zabbix'te hiçbir item'a `connection status` tag'i eklenmemiş.

**Çözüm:**
1. Zabbix UI → Configuration → Hosts → Items
2. Connectivity item'larını seç
3. `connection status` tag'ini ekle

#### Hata: "Email sending failed"
**Neden:** SMTP ayarları yanlış veya SMTP sunucusuna erişim yok.

**Çözüm:**
1. AWX Extra Variables'da SMTP ayarlarını kontrol et
2. SMTP sunucusuna network erişimi test et
3. SMTP credentials'ı doğrula

#### Hata: "Connectivity score always 0%"
**Neden:** Item'ların history verisi yok veya expected value yanlış.

**Çözüm:**
1. Zabbix UI'da item history'yi kontrol et
2. Item'ın data toplama durumunu kontrol et
3. `history_limit` değerini artır

---

### AWX Genel Sorunları

#### Hata: "Playbook not found"
**Neden:** SCM project path'i yanlış veya branch güncel değil.

**Çözüm:**
1. AWX → Projects → Project'i aç
2. "Update" butonuna tıkla (SCM sync)
3. Job Template'te playbook path'ini kontrol et

#### Hata: "Authentication failed"
**Neden:** Credential'lar yanlış veya expired.

**Çözüm:**
1. AWX → Credentials → Credential'ı kontrol et
2. Credential'ı test et
3. Gerekirse credentials'ı güncelle

#### Hata: "Job timeout"
**Neden:** Job çok uzun sürüyor.

**Çözüm:**
1. Job Template → Timeout değerini artır
2. `device_limit` kullanarak işlenen cihaz sayısını azalt
3. `host_groups` filtresi kullan

---

---

## 📚 İlgili Dokümantasyon

### Netbox-Zabbix
- [Netbox to Zabbix README](zabbix-netbox/README.md)
- [AWX Guide](zabbix-netbox/docs/guides/AWX_GUIDE.md)
- [Template Macros Guide](zabbix-netbox/docs/guides/TEMPLATE_MACROS_GUIDE.md)
- [Email Notification Guide](zabbix-netbox/docs/guides/EMAIL_NOTIFICATION_GUIDE.md)

### Zabbix-Monitoring
- [Tag-Based Connectivity README](zabbix-monitoring/TAG_BASED_CONNECTIVITY_README.md)
- [AWX Testing Guide](zabbix-monitoring/docs/guides/AWX_TESTING.md)
- [Email Notification Guide](zabbix-monitoring/docs/guides/EMAIL_NOTIFICATION_GUIDE.md)
- [Usage Guide](zabbix-monitoring/docs/guides/USAGE.md)

---

## 📝 Changelog

### 2026-01-19
- İlk versiyon oluşturuldu
- Netbox-Zabbix ve Zabbix-Monitoring konfigürasyon analizi eklendi
- AWX entegrasyon stratejileri dokümante edildi
- Best practices ve troubleshooting eklendi

---

## 📄 Lisans

Bu dokümantasyon project-zabake repository'sinin bir parçasıdır.
