#!/usr/bin/env python3
"""
Netbox API Detailed Analysis Script
Analyzes specific fields: rack, cluster, location, custom fields, tags
"""

import json
import sys
import urllib.request
import urllib.error
import ssl
from urllib.parse import urlencode

class NetboxAPIAnalyzer:
    def __init__(self, netbox_url, netbox_token, verify_ssl=False):
        self.base_url = netbox_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.token = netbox_token
        self.verify_ssl = verify_ssl
        
    def make_request(self, endpoint, params=None):
        """Make API request"""
        url = f"{self.api_url}/{endpoint}/"
        if params:
            url += "?" + urlencode(params)
        
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Token {self.token}')
        req.add_header('Accept', 'application/json')
        
        # Create SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            print(f"[ERROR] HTTP {e.code}: {e.reason}")
            try:
                error_body = e.read().decode()
                print(f"[ERROR] Response: {error_body[:200]}")
            except:
                pass
            return None
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return None
    
    def analyze_device_structure(self):
        """Analyze device structure with expanded fields"""
        print("\n=== Analyzing Device Structure (with expanded fields) ===")
        
        # Get devices with expanded related objects
        params = {
            'limit': 10,
        }
        
        data = self.make_request('dcim/devices', params)
        if not data or not data.get('results'):
            print("[WARNING] No devices found")
            return {}
        
        devices_analysis = []
        for device in data['results']:
            device_info = {
                'id': device.get('id'),
                'name': device.get('name'),
                'device_type': device.get('device_type'),
                'device_role': device.get('role') or device.get('device_role'),
                'site': device.get('site'),
                'location': device.get('location'),
                'rack': device.get('rack'),
                'cluster': device.get('cluster'),
                'primary_ip4': device.get('primary_ip4'),
                'tags': device.get('tags', []),
                'custom_fields': device.get('custom_fields', {}),
                'all_keys': list(device.keys())
            }
            
            # If rack is just an ID, fetch it
            if device_info['rack'] and isinstance(device_info['rack'], int):
                rack_id = device_info['rack']
                rack_data = self.make_request(f'dcim/racks/{rack_id}')
                if rack_data:
                    device_info['rack'] = rack_data
                    print(f"[INFO] Fetched rack {rack_id} for device {device.get('name')}")
            
            # If cluster is just an ID, fetch it
            if device_info['cluster'] and isinstance(device_info['cluster'], int):
                cluster_id = device_info['cluster']
                cluster_data = self.make_request(f'virtualization/clusters/{cluster_id}')
                if cluster_data:
                    device_info['cluster'] = cluster_data
                    print(f"[INFO] Fetched cluster {cluster_id} for device {device.get('name')}")
            
            # If location is just an ID, fetch it
            if device_info['location'] and isinstance(device_info['location'], int):
                location_id = device_info['location']
                location_data = self.make_request(f'dcim/locations/{location_id}')
                if location_data:
                    device_info['location'] = location_data
                    print(f"[INFO] Fetched location {location_id} for device {device.get('name')}")
            
            devices_analysis.append(device_info)
            
            print(f"\n[DEVICE] {device.get('name')} (ID: {device.get('id')})")
            print(f"  - Rack: {device_info['rack']}")
            print(f"  - Cluster: {device_info['cluster']}")
            print(f"  - Location: {device_info['location']}")
            print(f"  - Tags: {len(device_info['tags'])} tags")
            print(f"  - Custom Fields: {list(device_info['custom_fields'].keys())}")
        
        return {
            'devices': devices_analysis,
            'sample_device': devices_analysis[0] if devices_analysis else {}
        }
    
    def analyze_custom_fields(self):
        """Analyze custom fields structure"""
        print("\n=== Analyzing Custom Fields ===")
        
        data = self.make_request('extras/custom-fields', {'content_types': 'dcim.device', 'limit': 100})
        if not data or not data.get('results'):
            print("[WARNING] No custom fields found")
            return []
        
        custom_fields = []
        for cf in data['results']:
            field_info = {
                'name': cf.get('name'),
                'label': cf.get('label'),
                'type': cf.get('type'),
                'description': cf.get('description')
            }
            custom_fields.append(field_info)
            print(f"  - {cf.get('name')} ({cf.get('type')}): {cf.get('label')}")
        
        return custom_fields
    
    def analyze_rack_structure(self):
        """Analyze rack structure"""
        print("\n=== Analyzing Rack Structure ===")
        
        data = self.make_request('dcim/racks', {'limit': 5})
        if not data or not data.get('results'):
            print("[WARNING] No racks found")
            return {}
        
        sample_rack = data['results'][0]
        print(f"[SAMPLE RACK] {sample_rack.get('name')} (ID: {sample_rack.get('id')})")
        print(f"  - All keys: {list(sample_rack.keys())}")
        
        return {
            'sample_rack': sample_rack,
            'rack_keys': list(sample_rack.keys())
        }
    
    def analyze_location_structure(self):
        """Analyze location structure"""
        print("\n=== Analyzing Location Structure ===")
        
        data = self.make_request('dcim/locations', {'limit': 5})
        if not data or not data.get('results'):
            print("[WARNING] No locations found")
            return {}
        
        sample_location = data['results'][0]
        print(f"[SAMPLE LOCATION] {sample_location.get('name')} (ID: {sample_location.get('id')})")
        print(f"  - All keys: {list(sample_location.keys())}")
        print(f"  - Parent: {sample_location.get('parent')}")
        print(f"  - Custom Fields: {list(sample_location.get('custom_fields', {}).keys())}")
        
        return {
            'sample_location': sample_location,
            'location_keys': list(sample_location.keys())
        }
    
    def generate_final_report(self):
        """Generate final analysis report"""
        print("\n" + "="*60)
        print("=== GENERATING FINAL ANALYSIS REPORT ===")
        print("="*60)
        
        report = {
            'device_structure': self.analyze_device_structure(),
            'custom_fields': self.analyze_custom_fields(),
            'rack_structure': self.analyze_rack_structure(),
            'location_structure': self.analyze_location_structure()
        }
        
        return report

def main():
    netbox_url = "https://loki.bulutistan.com/"
    netbox_token = "13201880f324d54b1edb7351175a6fe2d4d833e9"
    
    analyzer = NetboxAPIAnalyzer(netbox_url, netbox_token, verify_ssl=False)
    
    report = analyzer.generate_final_report()
    
    # Save report
    output_file = '/tmp/netbox_detailed_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Detailed analysis report saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("=== ANALYSIS SUMMARY ===")
    print("="*60)
    
    if report.get('device_structure', {}).get('sample_device'):
        sample = report['device_structure']['sample_device']
        print(f"\nSample Device: {sample.get('name')}")
        print(f"  - Rack structure: {type(sample.get('rack'))}")
        print(f"  - Cluster structure: {type(sample.get('cluster'))}")
        print(f"  - Location structure: {type(sample.get('location'))}")
        print(f"  - Tags count: {len(sample.get('tags', []))}")
        print(f"  - Custom fields: {list(sample.get('custom_fields', {}).keys())}")
    
    print(f"\nCustom Fields found: {len(report.get('custom_fields', []))}")
    for cf in report.get('custom_fields', [])[:10]:
        print(f"  - {cf.get('name')} ({cf.get('type')})")

if __name__ == '__main__':
    main()

