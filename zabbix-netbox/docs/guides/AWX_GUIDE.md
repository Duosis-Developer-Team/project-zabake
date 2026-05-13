# Ansible AWX / AAP — NetBox (Loki) ↔ Zabbix senkronu

Bu kılavuz **`zabbix-netbox`** modülündeki ana playbook [`playbooks/netbox_zabbix_sync.yaml`](../../playbooks/netbox_zabbix_sync.yaml) ve rol `netbox_zabbix_sync` için AWX / Ansible Automation Platform üzerinde çalıştırma adımlarını ve **Extra Variables** parametrelerini tanımlar.

> **Not:** Bu dosyanın eski sürümünde başka bir repo yoluna (`zabbix-migration`) ait CSV migration anlatılıyordu; o akış bu `zabbix-netbox` dizininde yoktur. NetBox’tan Zabbix’e senkron için aşağıdaki playbook kullanılır.

## 1) Ön koşullar

- AWX execution environment, NetBox (Loki) API ve Zabbix JSON-RPC URL’ine ağ erişimi sağlar.
- SCM project bu repository’yi (veya `project-zabake` içinde `zabbix-netbox` yolunu) checkout eder.
- Playbook **`hosts: localhost`** kullanır; inventory’de `localhost` veya playbook’u çalıştıracak bir grup tanımlanır (çoğu kurulumda “Demo Inventory” + localhost yeterlidir).

## 2) Playbook ve rol

| Bileşen | Yol |
|--------|-----|
| Playbook | `zabbix-netbox/playbooks/netbox_zabbix_sync.yaml` |
| Rol | `zabbix-netbox/playbooks/roles/netbox_zabbix_sync/` |
| Varsayılanlar | [`defaults/main.yml`](../../playbooks/roles/netbox_zabbix_sync/defaults/main.yml) |

## 3) AWX Job Template

- **Inventory:** `localhost` içeren bir inventory (veya playbook hedefiyle uyumlu tek host).
- **Project:** Bu repo / alt modül checkout.
- **Playbook:** `playbooks/netbox_zabbix_sync.yaml` (project root’u `zabbix-netbox` olarak ayarladıysanız göreli yol buna göre).
- **Execution Environment:** Ansible 2.12+ önerilir; rol `uri` ve `lookup('file')` kullanır. [`requirements.yml`](../../requirements.yml) içindeki collection’lar EE’de yüklü olmalıdır.

## 4) Zorunlu Extra Variables

Playbook `pre_tasks` içinde doğrulanır; AWX’te **Extra Variables** (YAML veya JSON) ile verilir:

| Değişken | Açıklama |
|----------|----------|
| `netbox_url` | NetBox kök URL (örn. `https://loki.example.com`) |
| `netbox_token` | NetBox API token |
| `zabbix_url` | Zabbix API JSON-RPC uç noktası (örn. `https://zabbix.example.com/api_jsonrpc.php`) |
| `zabbix_user` | Zabbix API kullanıcısı |
| `zabbix_password` | Zabbix API şifresi (Vault / AWX credential önerilir) |

> `only_fetch: true` olsa bile playbook şu an bu alanları doğruladığı için Zabbix bilgileri job’da yine sağlanmalıdır (yalnızca NetBox okuma yapılır, Zabbix API çağrılmaz).

## 5) Senkron kapsamı (boolean bayraklar)

Rol varsayılanları `defaults/main.yml` içindedir; AWX’te ihtiyaca göre override edin:

| Değişken | Varsayılan | Açıklama |
|----------|-------------|----------|
| `sync_devices` | `true` | NetBox `dcim/devices` senkronu |
| `sync_platforms` | `false` | NetBox `dcim/platforms` senkronu |
| `sync_virtual_fws` | `false` | NetBox Plugins `custom-objects/virtual_fws` (`fw_status=active`) senkronu |
| `only_fetch` | `false` | `true` ise yalnızca NetBox verisi çekilir ve debug çıktısı üretilir; Zabbix create/update ve e-posta raporu çalışmaz |

En az biri açık olmalıdır: `sync_devices`, `sync_platforms`, `sync_virtual_fws` veya `only_fetch: true`.

## 6) İsteğe bağlı davranış ve filtreler

| Değişken | Varsayılan | Açıklama |
|----------|-------------|----------|
| `netbox_verify_ssl` | `false` | NetBox TLS doğrulama |
| `zabbix_validate_certs` | `false` | Zabbix TLS doğrulama |
| `location_filter` | `""` | Cihaz ve (virtual FW script’inde) lokasyon adı/slug alt string filtresi |
| `device_limit` | `0` | `0` = limitsiz; sadece device senkronunda ilk N cihaz |
| `create_devices_disabled` | `false` | Yeni **device** host’ları Zabbix’te disabled oluşturulsun |
| `create_platforms_disabled` | `false` | Yeni **platform** host’ları disabled |
| `create_virtual_fws_disabled` | `false` | Yeni **virtual firewall** host’ları disabled |
| `report_izlenmeyecek` | `true` | İzlenmeyecek (izlenmeli=Hayır vb.) kayıtların rapora eklenmesi |
| `mail_recipients` | `[]` | Başarısızlık özet e-postası; boş liste ile e-posta gönderilmez. SMTP varsayılanları `defaults/main.yml` |

## 7) Mapping dosya yolları (override)

Repo içi göreli yol varsayılanları `defaults/main.yml` içindedir. AWX checkout yapısı farklıysa aynı isimlerle override edilebilir:

| Değişken | Varsayılan mantığı |
|----------|---------------------|
| `templates_map_path` | `../mappings/templates.yml` (playbook dizinine göre) |
| `datacenters_map_path` | `../mappings/datacenters.yml` |
| `device_type_mapping_path` | `../mappings/netbox_device_type_mapping.yml` |
| `platform_mapping_path` | `../mappings/netbox_platform_mapping.yml` |
| `virtual_fw_mapping_path` | `../mappings/virtual_fw_mapping.yml` |
| `host_groups_config_path` | `../mappings/host_groups_config.yml` |
| `tags_config_path` | `../mappings/tags_config.yml` |

## 8) Örnek Extra Variables (YAML)

Aşağıdaki örnekte cihaz + sanal firewall senkronu birlikte açıktır:

```yaml
netbox_url: "https://loki.example.com"
netbox_token: "{{ netbox_token_from_credential }}"
netbox_verify_ssl: false

zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "awx-zabbix-api"
zabbix_password: "{{ vault_zabbix_password }}"
zabbix_validate_certs: false

sync_devices: true
sync_platforms: false
sync_virtual_fws: true

only_fetch: false
location_filter: ""
device_limit: 0

create_devices_disabled: false
create_platforms_disabled: false
create_virtual_fws_disabled: false

mail_recipients:
  - "ops@example.com"
```

Sadece NetBox’tan virtual firewall listesini görmek (Zabbix’e yazmadan):

```yaml
netbox_url: "https://loki.example.com"
netbox_token: "{{ netbox_token_from_credential }}"
zabbix_url: "https://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "dummy"
zabbix_password: "dummy"

sync_devices: false
sync_platforms: false
sync_virtual_fws: true
only_fetch: true
```

## 9) Virtual firewall eşlemesi

- Mapping: [`mappings/virtual_fw_mapping.yml`](../../mappings/virtual_fw_mapping.yml)
- Şablonlar: [`mappings/templates.yml`](../../mappings/templates.yml) içindeki `device_type` anahtarları ile birebir eşleşmeli
- Ayrıntı: [README_CONFIG.md](../../mappings/README_CONFIG.md) (Virtual firewalls bölümü), [docs/mappings/README.md](../mappings/README.md)

## 10) Sorun giderme

| Belirti | Kontrol |
|---------|---------|
| `netbox_url is required` | Extra vars’ta `netbox_url` / token / Zabbix alanları eksik |
| Şablon bulunamadı | `templates.yml` içindeki şablon adları Zabbix UI ile birebir aynı mı |
| Virtual FW eşleşmiyor | `virtual_fw_mapping.yml` içindeki `vendor` NetBox `vendor.name` ile aynı mı (büyük/küçük harf duyarsız tam eşleşme) |
| Proxy atanmıyor | `lokasyon.name` / `DC_ID` ile Zabbix proxy group adındaki DC kodu eşleşiyor mu; gerekirse `templates.yml` içinde `proxy_group_by_dc` |

## 11) Güvenlik

- NetBox ve Zabbix parolalarını AWX **Credentials** veya **Vault** ile verin; SCM’e commit etmeyin.
- Job Template için RBAC sınırlayın; production’da `*_verify_ssl` / `*_validate_certs` mümkünse `true` yapın.
