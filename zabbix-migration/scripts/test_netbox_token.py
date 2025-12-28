#!/usr/bin/env python3
"""
Quick test script to verify Netbox API token
"""
import requests
import sys
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

if len(sys.argv) < 3:
    print("Usage: python test_netbox_token.py <url> <token>")
    sys.exit(1)

url = sys.argv[1].rstrip('/')
token = sys.argv[2]

print(f"Testing Netbox API connection...")
print(f"URL: {url}")
print(f"Token: {token[:10]}...{token[-5:] if len(token) > 15 else '***'}")

headers = {
    'Authorization': f'Token {token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Test 1: Status endpoint
print("\n[TEST 1] Testing /api/status/ endpoint...")
try:
    response = requests.get(f"{url}/api/status/", headers=headers, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("[OK] Status endpoint works!")
        print(f"Response: {response.json()}")
    else:
        print(f"[ERROR] Status endpoint failed: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

# Test 2: Devices endpoint
print("\n[TEST 2] Testing /api/dcim/devices/ endpoint...")
try:
    response = requests.get(f"{url}/api/dcim/devices/", headers=headers, params={'limit': 1}, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("[OK] Devices endpoint works!")
        data = response.json()
        print(f"Total devices: {data.get('count', 0)}")
    else:
        print(f"[ERROR] Devices endpoint failed: {response.text[:200]}")
        try:
            error = response.json()
            print(f"Error detail: {error}")
        except:
            pass
except Exception as e:
    print(f"[ERROR] Exception: {e}")

# Test 3: User info
print("\n[TEST 3] Testing /api/users/users/ endpoint...")
try:
    response = requests.get(f"{url}/api/users/users/", headers=headers, params={'limit': 1}, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("[OK] Users endpoint works!")
    else:
        print(f"[ERROR] Users endpoint failed: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

