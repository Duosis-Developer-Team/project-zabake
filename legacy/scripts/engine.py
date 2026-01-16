import json
import sys
import os

def parse_check_new_platform(input_data):
    """
    Check_new_platform çıktısını alır ve iki farklı JSON çıktısı üretir:
    
    1. datalake_output: Her kayıt için 'manufacturer' (manufacturer.name) ve 'ip' (custom_fields.ip_addresses)
    2. zabbix_output: 'hosts' anahtarı altında her host için 'host' (name), 'name' (name) ve 'ip' (custom_fields.ip_addresses)
    """
    datalake_output = []
    zabbix_output = {"hosts": []}

    for record in input_data:
        # Datalake entegrasyonu için veriler:
        manufacturer = record.get("manufacturer", {}).get("name")
        ip = record.get("custom_fields", {}).get("ip_addresses")
        if manufacturer and ip:
            datalake_output.append({
                "manufacturer": manufacturer,
                "ip": ip
            })

        # Zabbix entegrasyonu için veriler:
        host_slug = record.get("slug")
        name = record.get("name")
        if host_slug and name and ip:
            zabbix_output["hosts"].append({
                "host": name,
                "name": name,
                "ip": ip
            })

    return datalake_output, zabbix_output

def main():
    # Input dosya yolu
    input_file = "/tmp/new_platform.json"
    
    # Output dosya yolları
    datalake_filename = "/tmp/datalake_integration.json"
    zabbix_filename = "/tmp/zabbix_integration.json"

    # Input dosyasını kontrol et
    if not os.path.exists(input_file):
        print(f"Hata: Input dosyası bulunamadı: {input_file}")
        sys.exit(1)

    try:
        # Input dosyasını oku
        with open(input_file, 'r') as f:
            input_data = json.load(f)
        
        # Verileri işle
        datalake_output, zabbix_output = parse_check_new_platform(input_data)

        # Çıktıları dosyalara yaz
        with open(datalake_filename, "w") as f:
            json.dump(datalake_output, f, indent=2)
        with open(zabbix_filename, "w") as f:
            json.dump(zabbix_output, f, indent=2)

        # Başarı mesajı
        print(f"Başarılı: Çıktılar oluşturuldu:")
        print(f"- {datalake_filename}")
        print(f"- {zabbix_filename}")

    except json.JSONDecodeError as e:
        print(f"Hata: Geçersiz JSON formatı: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Hata: Dosya işleme sırasında beklenmeyen hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()