# Legacy Workflow

Bu klasör, eski platform synchronization, datalake integration ve CSV-based Zabbix host creation workflow'larını içerir.

## 📋 İçerik

### Scripts

- **check_new_platform.py**: Netbox API'den yeni platform kayıtlarını çeker ve PostgreSQL veritabanına kaydeder
- **engine.py**: check_new_platform çıktısını parse eder ve datalake/zabbix entegrasyonu için JSON dosyaları oluşturur
- **datalake_integration.py**: Datalake configuration dosyasını günceller (IBM Power, Vmware, Nutanix)
- **zabbix_integration.py**: Zabbix API'ye host oluşturma işlemi yapar

### Playbooks

- **check_new_platform.yaml**: Platform synchronization scriptini çalıştırır
- **engine.yaml**: Engine scriptini çalıştırır ve çıktıları işler
- **datalake_integration.yaml**: Datalake integration işlemini yönetir
- **zabbix_integration.yaml**: Zabbix integration işlemini yönetir
- **zabbix_csv_import.yaml**: CSV dosyasından Zabbix'e host import işlemi (Legacy)

### Roles

- **zabbix_csv_import/**: CSV'den Zabbix'e host import rolü (Legacy)

## ⚠️ Not

Bu workflow'lar eski versiyonlardır. Yeni geliştirmeler için `zabbix-netbox/` klasöründeki modern çözümü kullanın.

## 🔧 Gereksinimler

- Python 3.8+
- Ansible 2.9+
- PostgreSQL (psycopg2) - Platform sync için
- requests
- Ansible Collections:
  - `community.general` (>=8.0.0)
  - `community.zabbix` (>=2.0.0) - CSV import için

## 📝 Kullanım

### CSV Import (Legacy)

```bash
ansible-playbook playbooks/zabbix_csv_import.yaml \
  -e "csv_path=/path/to/hosts.csv" \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### Platform Synchronization

Bu workflow, AWX/Ansible Tower üzerinden çalıştırılmak üzere tasarlanmıştır. Scriptler ve playbook'lar production ortamındaki belirli path'leri kullanır.

**Not:** Bu workflow'lar artık aktif olarak geliştirilmemektedir. Yeni özellikler için `zabbix-netbox/` projesine bakın.
