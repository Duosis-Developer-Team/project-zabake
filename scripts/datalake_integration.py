import json
import sys

config_file = "/Datalake_Project/configuration_file.json"

def update_configuration(config, manufacturer, new_ip):
    """
    Verilen konfigürasyon sözlüğünde, manufacturer bilgisine göre ilgili bölümü
    bularak IP/hostname alanına yeni IP değerini virgülle ekler.
    """
    if manufacturer == "IBM Power":
        section = "IBM-HMC"
        key = "hmc_hostname"
    elif manufacturer == "Vmware":
        section = "VmWare"
        key = "VMwareIP"
    elif manufacturer == "Nutanix":
        section = "Nutanix"
        key = "PRISM_IP"
    else:
        print(f"Desteklenmeyen manufacturer: {manufacturer}")
        return config

    current_value = config.get(section, {}).get(key, "")
    if current_value:
        updated_value = current_value + "," + new_ip
    else:
        updated_value = new_ip

    if section in config:
        config[section][key] = updated_value
    else:
        config[section] = {key: updated_value}

    return config

def main():
    """
    Script, komut satırından input JSON dosya yolu alır.
    Örnek kullanım:
    python3 datalake_integration.py input.json
    Gerekli JSON dosyası, beklenen formatta 'manufacturer' ve 'ip' anahtarlarını içermelidir.
    Ardından 'configuration_file.json' dosyası okunup güncellenir.
    """
    if len(sys.argv) < 2:
        print("Kullanım: python3 script.py <input_json_dosyasi>")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Girdi dosyası okunurken hata: {e}")
        sys.exit(1)

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Konfigürasyon dosyası okunurken hata: {e}")
        sys.exit(1)

    # JSON verisi tek kayıt veya liste şeklinde olabilir.
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = [data]
    else:
        print("JSON verisi uygun formatta değil!")
        sys.exit(1)

    for entry in entries:
        manufacturer = entry.get("manufacturer")
        new_ip = entry.get("ip")
        if not manufacturer or not new_ip:
            print("JSON, 'manufacturer' ve 'ip' anahtarlarını içermelidir!")
            continue
        config = update_configuration(config, manufacturer, new_ip)

    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Konfigürasyon dosyasına yazılırken hata: {e}")
        sys.exit(1)

    print("Konfigürasyon başarıyla güncellendi.")

if __name__ == "__main__":
    main()
