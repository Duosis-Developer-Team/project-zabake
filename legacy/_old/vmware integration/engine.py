import json
import sys

def parse_check_new_platform(input_data):
    """
    Check_new_platform çıktısını alır ve iki farklı JSON çıktısı üretir:
    
    1. datalake_output: Her kayıt için 'manufacturer' (manufacturer.name) ve 'ip' (custom_fields.ip_addresses)
    2. zabbix_output: 'hosts' anahtarı altında her host için 'host' (slug), 'name' (name) ve 'ip' (custom_fields.ip_addresses)
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
                "host": host_slug,
                "name": name,
                "ip": ip
            })

    return datalake_output, zabbix_output

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 check_new_platform_parser.py '<json_input>'")
        sys.exit(1)

    input_json = sys.argv[1]
    try:
        input_data = json.loads(input_json)
    except json.JSONDecodeError as e:
        print(f"Geçersiz JSON formatı: {e}")
        sys.exit(1)

    datalake_output, zabbix_output = parse_check_new_platform(input_data)

    # Çıktıları ayrı dosyalara yazalım:
    datalake_filename = "datalake_integration_output.json"
    zabbix_filename = "zabbix_integration_output.json"

    try:
        with open(datalake_filename, "w") as f:
            json.dump(datalake_output, f, indent=2)
        with open(zabbix_filename, "w") as f:
            json.dump(zabbix_output, f, indent=2)
    except Exception as e:
        print(f"Çıktı dosyasına yazılırken hata: {e}")
        sys.exit(1)

    # Konsola çıktıları yazdırma:
    print("Datalake Entegrasyonu için JSON Çıktısı:")
    print(json.dumps(datalake_output, indent=2))
    print("\nZabbix Entegrasyonu için JSON Çıktısı:")
    print(json.dumps(zabbix_output, indent=2))

if __name__ == "__main__":
    main()
