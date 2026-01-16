import requests
import json
import sys

# Zabbix API bağlantı bilgileri
zabbix_url = "http://****/zabbix/api_jsonrpc.php"
zabbix_user = "****"
zabbix_password = "****"

# 1) Zabbix'e login olup auth token alma
login_payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "username": zabbix_user,
        "password": zabbix_password
    },
    "id": 1
}

response = requests.post(zabbix_url, json=login_payload, verify=False)
result = response.json()

if "result" not in result:
    raise Exception("Giriş başarısız! Cevap: {}".format(result))

auth_token = result["result"]
print(f"Alınan auth token: {auth_token}")

# 2) Input JSON verisini doğrudan komut satırından alıyoruz.
if len(sys.argv) < 2:
    raise Exception("Lütfen JSON input verisini belirtin (dosya adı değil).")

input_json = sys.argv[1]
try:
    data = json.loads(input_json)
except json.JSONDecodeError as e:
    raise Exception(f"Geçersiz JSON formatı: {e}")

# 3) Her bir host için Zabbix API'ye create işlemi gönderme
for host_info in data.get("hosts", []):
    # JSON verisindeki bilgileri atama
    host_name = host_info.get("host")
    display_name = host_info.get("name")
    host_ip = host_info.get("ip")
    
    # Gerekli alanlar kontrol ediliyor.
    if not host_name or not display_name or not host_ip:
        print(f"Host bilgileri eksik: {host_info}")
        continue

    create_host_payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": host_name,         # JSON'dan gelen host adı
            "name": display_name,      # JSON'dan gelen görünür ad
            "interfaces": [
                {
                    "type": 2,         # 2 => SNMP
                    "main": 1,
                    "useip": 1,        # 1 => IP kullan
                    "ip": host_ip,     # JSON'dan gelen IP
                    "dns": "",
                    "port": "161",
                    "details": {
                        "version": 3,
                        "bulk": 1,
                        "securityname": "zabbix",
                        "securitylevel": 2,
                        "authprotocol": 1,
                        "authpassphrase": "44446749c76fb49994bce606f384028bc1bde1a3d4c679811ed408f5c60cb439",
                        "privprotocol": 1,
                        "privpassphrase": "44446749c76fb49994bce606f384028bc1bde1a3d4c679811ed408f5c60cb439",
                        "max_repetitions": 10
                    }
                }
            ],
            "groups": [
                {"groupid": "1505"},
                {"groupid": "1506"},
                {"groupid": "1507"}
            ],
            "templates": [
                {"templateid": "10713"}
            ],
            "macros": [
                {
                    "macro": "{$SNMP_COMMUNITY}",
                    "value": "zabbix"
                }
            ],
            "monitored_by": 2,   # 0 => Server, 1 => Proxy
            "proxy_groupid": 3
        },
        "auth": auth_token,
        "id": 2
    }

    create_host_response = requests.post(zabbix_url, json=create_host_payload, verify=False).json()
    print("Host oluşturma yanıtı:")
    print(json.dumps(create_host_response, indent=4))

    if "result" in create_host_response:
        print("Host başarıyla oluşturuldu! Host ID:",
              create_host_response["result"]["hostids"])
    else:
        print("Host oluşturma hatası:", create_host_response)
