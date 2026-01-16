import requests
import psycopg2
import json
import os

# API bilgileri
api_url = "https://****/api/dcim/platforms/?limit=1000"
api_token = "*****"  # Buraya API token'ınızı girin

headers = {
    "Authorization": f"Token {api_token}"  # Veya eğer Bearer kullanılıyorsa: "Bearer {api_token}"
}

# API'den GET isteğiyle veriyi çekiyoruz.
response = requests.get(api_url, headers=headers)
if response.status_code != 200:
    raise Exception(f"API isteğinde hata oluştu: {response.status_code} - {response.text}")

data = response.json()

# PostgreSQL bağlantı parametrelerinizi buraya girin.
conn = psycopg2.connect(
    host="10.134.16.6",
    database="bulutlake",
    user="bulutlake",
    password="BulutLakePas24",
    port="5000"
)
cursor = conn.cursor()

# Mevcut kayıtların id'lerini veritabanından çekiyoruz.
cursor.execute("SELECT id FROM loki_platforms")
existing_ids = {row[0] for row in cursor.fetchall()}

new_records = []  # Tabloda olmayan yeni kayıtları tutmak için

for record in data.get("results", []):
    record_id = record.get("id")
    if record_id not in existing_ids:
        new_records.append(record)

        # Nested verileri ayrıştırma:
        manufacturer = record.get("manufacturer", {}) or {}
        custom_fields = record.get("custom_fields", {}) or {}

        insert_query = """
        INSERT INTO loki_platforms (
            id, url, display_url, display, name, slug,
            manufacturer_id, manufacturer_url, manufacturer_display, manufacturer_name, manufacturer_slug, manufacturer_description,
            config_template, description, tags, custom_fields_dc, custom_fields_ip_addresses, custom_fields_port, custom_fields_site, custom_fields_url,
            created, last_updated, device_count, virtualmachine_count
        ) VALUES (
            %(id)s, %(url)s, %(display_url)s, %(display)s, %(name)s, %(slug)s,
            %(manufacturer_id)s, %(manufacturer_url)s, %(manufacturer_display)s, %(manufacturer_name)s, %(manufacturer_slug)s, %(manufacturer_description)s,
            %(config_template)s, %(description)s, %(tags)s, %(custom_fields_dc)s, %(custom_fields_ip_addresses)s, %(custom_fields_port)s, %(custom_fields_site)s, %(custom_fields_url)s,
            %(created)s, %(last_updated)s, %(device_count)s, %(virtualmachine_count)s
        )
        """
        params = {
            "id": record.get("id"),
            "url": record.get("url"),
            "display_url": record.get("display_url"),
            "display": record.get("display"),
            "name": record.get("name"),
            "slug": record.get("slug"),
            "manufacturer_id": manufacturer.get("id"),
            "manufacturer_url": manufacturer.get("url"),
            "manufacturer_display": manufacturer.get("display"),
            "manufacturer_name": manufacturer.get("name"),
            "manufacturer_slug": manufacturer.get("slug"),
            "manufacturer_description": manufacturer.get("description"),
            "config_template": record.get("config_template"),
            "description": record.get("description"),
            "tags": json.dumps(record.get("tags")),
            "custom_fields_dc": custom_fields.get("DC"),
            "custom_fields_ip_addresses": custom_fields.get("ip_addresses"),
            "custom_fields_port": custom_fields.get("Port"),
            "custom_fields_site": custom_fields.get("Site"),
            "custom_fields_url": custom_fields.get("URL"),
            "created": record.get("created"),
            "last_updated": record.get("last_updated"),
            "device_count": record.get("device_count"),
            "virtualmachine_count": record.get("virtualmachine_count"),
        }

        cursor.execute(insert_query, params)
        conn.commit()

# JSON dosyasını /tmp dizinine yaz
output_file = "/tmp/new_platform.json"
try:
    with open(output_file, 'w') as f:
        json.dump(new_records, f, separators=(',', ':'))
    print(f"Yeni kayıtlar başarıyla {output_file} dosyasına yazıldı")
except Exception as e:
    print(f"Dosya yazma hatası: {str(e)}")

cursor.close()
conn.close()

# Konsola da çıktı ver (opsiyonel)
print(json.dumps(new_records, separators=(',', ':')))