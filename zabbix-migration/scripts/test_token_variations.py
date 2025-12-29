#!/usr/bin/env python3
"""
Test different token formats
"""
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

url = "https://loki.bulutistan.com"
token = "Ds+7g19Hzp5L><?w!"

# Test different token formats
token_variations = [
    ("Original", token),
    ("Stripped", token.strip()),
    ("With spaces", f" {token} "),
    ("Base64 encoded?", token.encode('utf-8').hex()),
]

headers_base = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

for name, test_token in token_variations:
    print(f"\n[TEST] {name}: {test_token[:20]}...")
    headers = headers_base.copy()
    headers['Authorization'] = f'Token {test_token}'
    
    try:
        response = requests.get(
            f"{url}/api/dcim/devices/",
            headers=headers,
            params={'limit': 1},
            verify=False,
            timeout=10
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  [SUCCESS] Token format works!")
            break
        else:
            print(f"  Error: {response.text[:100]}")
    except Exception as e:
        print(f"  Exception: {e}")

print("\n[INFO] If all tests fail, please verify:")
print("  1. Token is correct in Netbox UI (User -> API Tokens)")
print("  2. Token has proper permissions")
print("  3. Token is not expired")
print("  4. Token format matches Netbox version requirements")


