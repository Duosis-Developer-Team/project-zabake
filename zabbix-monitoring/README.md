# Zabbix Monitoring Integration

Bu modül, HMDL (Host Metadata-Driven Lifecycle) projesinin bir parçasıdır ve Zabbix host'larındaki connectivity item'larının veri durumunu analiz ederek, host'lardan veri çekilip çekilemediğini tespit eder.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Proje Yapısı](#proje-yapısı)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Dokümantasyon](#dokümantasyon)
- [Geliştirme](#geliştirme)

## 🎯 Genel Bakış

Bu modül, Zabbix'te bulunan host'ların template'lerine göre belirlenen connectivity item'larının veri durumunu analiz eder:

### Özellikler

- ✅ **Template Analizi**: Host template'lerinden connectivity item'larını otomatik tespit etme
- ✅ **Veri Durumu Analizi**: Item'ların veri çekilme durumunu analiz etme
- ✅ **Host Connectivity Tespiti**: Host'lardan veri çekilip çekilemediğini belirleme
- ✅ **Zabbix API/DB Entegrasyonu**: API veya passive database'den veri çekme
- ✅ **Performans Optimizasyonu**: Zabbix'te ekstra yük oluşturmadan çalışma
- ✅ **AWX Orkestrasyonu**: Kubernetes üzerinde Ansible AWX ile otomasyon
- ✅ **Raporlama**: JSON, HTML, CSV formatlarında rapor üretme

### Teknik Detaylar

- **Orkestrasyon**: Kubernetes üzerinde Ansible AWX
- **Veri Kaynağı**: 
  - Development: Zabbix API
  - Production: Zabbix passive database (cluster)
- **İşleme**: Python ile veri analizi ve karşılaştırma
- **Performans**: Veri bir kez alınıp işlenir, Zabbix'te ekstra yük oluşturmaz

## 📁 Proje Yapısı

```
zabbix-monitoring/
├── docs/                    # Dokümantasyon
│   ├── guides/             # Kullanım kılavuzları
│   ├── analysis/           # Analiz dokümanları
│   ├── design/             # Tasarım dokümanları
│   └── development/        # Geliştirme dokümanları
├── playbooks/              # Ansible playbook'ları
│   └── roles/             # Ansible rolleri
├── scripts/                # Python scriptleri
│   ├── collectors/        # Veri toplayıcılar
│   ├── analyzers/         # Analiz modülleri
│   └── reports/           # Rapor modülleri
├── config/                 # Konfigürasyon dosyaları
├── tests/                  # Unit testler
└── examples/               # Örnek dosyalar
```

Detaylı yapı için: [DEVELOPMENT_PLAN.md](docs/development/DEVELOPMENT_PLAN.md)

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.8+
- Ansible 2.9+
- Ansible Collections:
  - `community.general` (>=8.0.0)
  - `community.zabbix` (>=2.0.0)

### Kurulum

```bash
cd zabbix-monitoring
ansible-galaxy collection install -r requirements.yml
pip install -r scripts/requirements.txt
```

### Kullanım

#### Ansible AWX ile Çalıştırma

```bash
ansible-playbook playbooks/zabbix_monitoring_check.yaml \
  -e "zabbix_url=https://zabbix.example.com/api_jsonrpc.php" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "output_format=json"
```

#### Python Script ile Çalıştırma

```bash
python scripts/main.py \
  --zabbix-url https://zabbix.example.com/api_jsonrpc.php \
  --zabbix-user admin \
  --zabbix-password password \
  --output-format json
```

## 📚 Dokümantasyon

### Kılavuzlar
- [AWX Kurulum Kılavuzu](docs/guides/AWX_SETUP.md)
- [Database Bağlantı Kılavuzu](docs/guides/DATABASE_CONNECTION.md)
- [Kullanım Kılavuzu](docs/guides/USAGE.md)

### Tasarım
- [Mimari Tasarım](docs/design/ARCHITECTURE.md)
- [Veri Akışı](docs/design/DATA_FLOW.md)
- [Veri Şeması](docs/design/SCHEMA.md)

### Geliştirme
- [Geliştirme Planı](docs/development/DEVELOPMENT_PLAN.md)
- [Görev Dağılımı](docs/development/TASK_BREAKDOWN.md)

### Analiz
- [Connectivity Item Analizi](docs/analysis/CONNECTIVITY_ITEMS.md)
- [Template Analizi](docs/analysis/TEMPLATE_ANALYSIS.md)

## 🔧 Konfigürasyon

Konfigürasyon dosyaları `config/` klasöründe bulunur:

- `zabbix_api_config.yml`: Zabbix API ayarları
- `db_config.yml`: Database bağlantı ayarları
- `monitoring_config.yml`: Monitoring konfigürasyonu

Örnek konfigürasyon için: [examples/sample_config.yml](examples/sample_config.yml)

## 🧪 Test

Unit testleri çalıştırmak için:

```bash
cd scripts
pytest tests/
```

## 📝 Geliştirme

Detaylı geliştirme planı için: [DEVELOPMENT_PLAN.md](docs/development/DEVELOPMENT_PLAN.md)

### Geliştirme Akışı

1. Development branch'inde çalışın
2. Her feature için ayrı branch oluşturun
3. Feature tamamlandığında development'a merge edin
4. Her feature için unit test yazın
5. Testleri çalıştırın ve başarılıysa GitHub'a push edin

## 🔄 Veri Akışı

```
Zabbix API/DB → Data Collection → Template Analysis → 
Connectivity Item Detection → Data Analysis → Report Generation
```

## 📊 Rapor Formatları

- **JSON**: Programatik kullanım için
- **HTML**: İnsan okunabilir raporlar
- **CSV**: Excel/Spreadsheet analizi için

## 🐛 Sorun Giderme

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Konfigürasyon dosyalarını doğrulayın
3. [Kullanım Kılavuzu](docs/guides/USAGE.md) bölümüne bakın

## 📞 Destek

Sorularınız için:
- Dokümantasyon: `docs/` klasörüne bakın
- Geliştirme planı: `docs/development/DEVELOPMENT_PLAN.md`

## 📄 Lisans

[Lisans bilgisi buraya eklenecek]

