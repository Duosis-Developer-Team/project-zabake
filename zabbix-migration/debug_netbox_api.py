#!/usr/bin/env python3
"""
Debug script to analyze raw Netbox API response
This will help us understand the actual structure of custom_fields and other data
"""

import json
import sys
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
NETBOX_URL = "https://loki.bulutistan.com"
NETBOX_TOKEN = "13201880f324d54b1edb7351175a6fe2d4d833e9"
LOCATION_FILTER = "ICT11"

def fetch_devices():
    """Fetch devices from Netbox API"""
    headers = {
        'Authorization': f'Token {NETBOX_TOKEN}',
        'Accept': 'application/json'
    }
    
    # First, resolve location ID
    print("=" * 80)
    print("STEP 1: Resolving location ID for:", LOCATION_FILTER)
    print("=" * 80)
    
    try:
        location_response = requests.get(
            f"{NETBOX_URL}/api/dcim/locations/",
            headers=headers,
            params={'name': LOCATION_FILTER, 'limit': 1000},
            verify=False,
            timeout=30
        )
        location_response.raise_for_status()
        location_data = location_response.json()
        
        print(f"Location API Response Count: {location_data.get('count', 0)}")
        
        location_id = None
        for loc in location_data.get('results', []):
            if loc.get('name', '').upper() == LOCATION_FILTER.upper():
                location_id = loc.get('id')
                print(f"✓ Found location: {loc.get('name')} (ID: {location_id})")
                print(f"  Full location object:")
                print(json.dumps(loc, indent=2))
                break
        
        if not location_id:
            print(f"✗ Location '{LOCATION_FILTER}' not found!")
            return
            
    except Exception as e:
        print(f"✗ Error resolving location: {e}")
        return
    
    # Fetch devices
    print("\n" + "=" * 80)
    print(f"STEP 2: Fetching devices for location_id={location_id}")
    print("=" * 80)
    
    try:
        devices_response = requests.get(
            f"{NETBOX_URL}/api/dcim/devices/",
            headers=headers,
            params={'location_id': location_id, 'limit': 5},  # Limit to 5 for debugging
            verify=False,
            timeout=30
        )
        devices_response.raise_for_status()
        devices_data = devices_response.json()
        
        print(f"\nTotal devices found: {devices_data.get('count', 0)}")
        print(f"Showing first {len(devices_data.get('results', []))} devices\n")
        
        for idx, device in enumerate(devices_data.get('results', []), 1):
            print("=" * 80)
            print(f"DEVICE #{idx}: {device.get('name', 'N/A')}")
            print("=" * 80)
            
            # Basic info
            print("\n📌 BASIC INFO:")
            print(f"  ID: {device.get('id')}")
            print(f"  Name: {device.get('name')}")
            print(f"  URL: {device.get('url')}")
            
            # Device type
            print("\n🔧 DEVICE TYPE:")
            device_type = device.get('device_type', {})
            if device_type:
                print(f"  Model: {device_type.get('model', 'N/A')}")
                print(f"  Manufacturer: {device_type.get('manufacturer', {}).get('name', 'N/A')}")
            
            # Role
            print("\n👤 ROLE:")
            role = device.get('role') or device.get('device_role', {})
            print(f"  Role Name: {role.get('name', 'N/A')}")
            
            # Site
            print("\n🌍 SITE:")
            site = device.get('site', {})
            print(f"  Site Name: {site.get('name', 'N/A')}")
            
            # Location
            print("\n📍 LOCATION:")
            location = device.get('location', {})
            if location:
                print(f"  Location ID: {location.get('id', 'N/A')}")
                print(f"  Location Name: {location.get('name', 'N/A')}")
                print(f"  Location Description: {location.get('description', 'N/A')}")
            
            # Tenant
            print("\n🏢 TENANT:")
            tenant = device.get('tenant', {})
            if tenant:
                print(f"  Tenant Name: {tenant.get('name', 'N/A')}")
                print(f"  Tenant ID: {tenant.get('id', 'N/A')}")
            else:
                print("  ✗ No tenant assigned")
            
            # Primary IP
            print("\n🌐 PRIMARY IP:")
            primary_ip4 = device.get('primary_ip4', {})
            if primary_ip4:
                print(f"  IP Address: {primary_ip4.get('address', 'N/A')}")
            else:
                print("  ✗ No primary IP")
            
            # Cluster
            print("\n☁️  CLUSTER:")
            cluster = device.get('cluster', {})
            if cluster:
                print(f"  Cluster Name: {cluster.get('name', 'N/A')}")
            else:
                print("  ✗ No cluster assigned")
            
            # Rack
            print("\n🗄️  RACK:")
            rack = device.get('rack', {})
            if rack:
                print(f"  Rack Name: {rack.get('name', 'N/A')}")
                rack_role = rack.get('role', {})
                if rack_role:
                    print(f"  Rack Role: {rack_role.get('name', 'N/A')}")
            else:
                print("  ✗ No rack assigned")
            
            # CUSTOM FIELDS - THE MOST IMPORTANT PART!
            print("\n⚙️  CUSTOM FIELDS (RAW):")
            custom_fields = device.get('custom_fields', {})
            if custom_fields:
                print(json.dumps(custom_fields, indent=4))
                
                # Specific checks
                print("\n  🔍 Checking for Contacts field:")
                if 'Contacts' in custom_fields:
                    print(f"    ✓ 'Contacts' found: {custom_fields['Contacts']}")
                elif 'contacts' in custom_fields:
                    print(f"    ✓ 'contacts' (lowercase) found: {custom_fields['contacts']}")
                else:
                    print("    ✗ 'Contacts' field NOT found")
                    print(f"    Available fields: {list(custom_fields.keys())}")
                
                print("\n  🔍 Checking for other ownership/contact fields:")
                for key in custom_fields.keys():
                    if any(keyword in key.lower() for keyword in ['contact', 'owner', 'sahip', 'sorumlu']):
                        print(f"    • {key}: {custom_fields[key]}")
            else:
                print("  ✗ No custom fields found")
            
            # Tags
            print("\n🏷️  TAGS:")
            tags = device.get('tags', [])
            if tags:
                for tag in tags:
                    print(f"  • {tag.get('name', 'N/A')} (slug: {tag.get('slug', 'N/A')})")
            else:
                print("  ✗ No tags")
            
            # Full raw JSON for this device
            print("\n📄 FULL RAW JSON:")
            print(json.dumps(device, indent=2))
            print("\n" + "=" * 80 + "\n")
            
    except Exception as e:
        print(f"✗ Error fetching devices: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 NETBOX API DEBUG SCRIPT")
    print("This script will fetch and analyze raw Netbox API responses\n")
    
    fetch_devices()
    
    print("\n✅ Debug script completed!")

