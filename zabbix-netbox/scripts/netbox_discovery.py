#!/usr/bin/env python3
"""
Netbox API Discovery Script

This script analyzes Netbox API structure to discover where data fields
from the template mapping CSV can be retrieved.

Fields to map from CSV template conditions:
- Device Role (e.g., "HOST")
- Manufacturer/Üretici (e.g., "Lenovo", "HPE", "Dell", "Inspur")
- Device Type (e.g., "M6", "M5" suffix)
- Hostname
- IP Address
- Site/Location (for DC_ID)
- Tags
- Custom Fields (for Notes)
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class NetboxDiscovery:
    """Netbox API discovery and analysis class"""
    
    def __init__(self, netbox_url: str, netbox_token: str, verify_ssl: bool = False):
        """
        Initialize Netbox discovery client
        
        Args:
            netbox_url: Netbox API base URL (e.g., https://netbox.example.com)
            netbox_token: Netbox API token
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = netbox_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.token = netbox_token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        # Netbox API token format: Token <token>
        token_header = self.token.strip()
        if not token_header.startswith('Token '):
            token_header = f'Token {token_header}'
        self.session.headers.update({
            'Authorization': token_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Test connection to Netbox API"""
        try:
            # Try status endpoint first
            response = self.session.get(
                f"{self.api_url}/status/",
                verify=self.verify_ssl,
                timeout=10
            )
            
            # If status endpoint fails, try devices endpoint
            if response.status_code == 403 or response.status_code == 404:
                print(f"[INFO] Status endpoint returned {response.status_code}, trying devices endpoint...")
                response = self.session.get(
                    f"{self.api_url}/dcim/devices/",
                    params={'limit': 1},
                    verify=self.verify_ssl,
                    timeout=10
                )
            
            response.raise_for_status()
            print("[OK] Netbox API connection successful")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] Netbox API connection failed: HTTP {e.response.status_code}")
            if e.response.status_code == 403:
                print("[INFO] 403 Forbidden - Check API token permissions")
                try:
                    error_detail = e.response.json()
                    print(f"[INFO] Error detail: {error_detail}")
                except:
                    print(f"[INFO] Response text: {e.response.text[:200]}")
            return False
        except Exception as e:
            print(f"[ERROR] Netbox API connection failed: {e}")
            return False
    
    def discover_endpoints(self) -> Dict[str, Any]:
        """Discover available API endpoints"""
        print("\n=== Discovering API Endpoints ===")
        endpoints = {}
        
        # Common Netbox endpoints we need
        endpoint_list = [
            'dcim/devices',
            'dcim/device-roles',
            'dcim/manufacturers',
            'dcim/device-types',
            'dcim/sites',
            'dcim/interfaces',
            'ipam/ip-addresses',
            'ipam/prefixes',
            'extras/tags',
            'extras/custom-fields'
        ]
        
        for endpoint in endpoint_list:
            try:
                url = f"{self.api_url}/{endpoint}/"
                response = self.session.get(
                    url,
                    params={'limit': 1},
                    verify=self.verify_ssl,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    endpoints[endpoint] = {
                        'status': 'available',
                        'count': data.get('count', 0),
                        'sample_fields': list(data.get('results', [{}])[0].keys()) if data.get('results') else []
                    }
                    print(f"[OK] {endpoint}: {data.get('count', 0)} items")
                else:
                    endpoints[endpoint] = {'status': 'error', 'code': response.status_code}
                    print(f"[ERROR] {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                endpoints[endpoint] = {'status': 'error', 'message': str(e)}
                print(f"[ERROR] {endpoint}: {e}")
        
        return endpoints
    
    def analyze_device_structure(self) -> Dict[str, Any]:
        """Analyze device object structure to find relevant fields"""
        print("\n=== Analyzing Device Structure ===")
        
        try:
            # Get a sample device
            response = self.session.get(
                f"{self.api_url}/dcim/devices/",
                params={'limit': 1},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('results'):
                print("[WARNING] No devices found in Netbox")
                return {}
            
            device = data['results'][0]
            
            # Extract relevant fields
            device_structure = {
                'id': device.get('id'),
                'name': device.get('name'),
                'display': device.get('display'),
                'device_type': {
                    'id': device.get('device_type', {}).get('id'),
                    'display': device.get('device_type', {}).get('display'),
                    'model': device.get('device_type', {}).get('model'),
                    'manufacturer': device.get('device_type', {}).get('manufacturer', {})
                },
                'device_role': {
                    'id': device.get('device_role', {}).get('id'),
                    'name': device.get('device_role', {}).get('name'),
                    'display': device.get('device_role', {}).get('display'),
                    'slug': device.get('device_role', {}).get('slug')
                },
                'site': {
                    'id': device.get('site', {}).get('id'),
                    'name': device.get('site', {}).get('name'),
                    'slug': device.get('site', {}).get('slug')
                },
                'primary_ip': device.get('primary_ip'),
                'primary_ip4': device.get('primary_ip4'),
                'primary_ip6': device.get('primary_ip6'),
                'tags': device.get('tags', []),
                'custom_fields': device.get('custom_fields', {}),
                'all_fields': list(device.keys())
            }
            
            print(f"[OK] Device sample found: {device.get('name')}")
            print(f"  - Device Role: {device_structure['device_role'].get('name')}")
            print(f"  - Manufacturer: {device_structure['device_type'].get('manufacturer', {}).get('name')}")
            print(f"  - Device Type: {device_structure['device_type'].get('model')}")
            print(f"  - Site: {device_structure['site'].get('name')}")
            print(f"  - Primary IP: {device_structure.get('primary_ip')}")
            print(f"  - Tags: {len(device_structure['tags'])} tags")
            print(f"  - Custom Fields: {len(device_structure['custom_fields'])} fields")
            
            return device_structure
            
        except Exception as e:
            print(f"[ERROR] Error analyzing device structure: {e}")
            return {}
    
    def discover_device_roles(self) -> List[Dict[str, Any]]:
        """Discover available device roles"""
        print("\n=== Discovering Device Roles ===")
        
        try:
            response = self.session.get(
                f"{self.api_url}/dcim/device-roles/",
                params={'limit': 100},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            roles = []
            for role in data.get('results', []):
                roles.append({
                    'id': role.get('id'),
                    'name': role.get('name'),
                    'slug': role.get('slug'),
                    'display': role.get('display')
                })
                print(f"  - {role.get('name')} (slug: {role.get('slug')})")
            
            print(f"[OK] Found {len(roles)} device roles")
            return roles
            
        except Exception as e:
            print(f"[ERROR] Error discovering device roles: {e}")
            return []
    
    def discover_manufacturers(self) -> List[Dict[str, Any]]:
        """Discover available manufacturers"""
        print("\n=== Discovering Manufacturers ===")
        
        try:
            response = self.session.get(
                f"{self.api_url}/dcim/manufacturers/",
                params={'limit': 100},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            manufacturers = []
            for mfr in data.get('results', []):
                manufacturers.append({
                    'id': mfr.get('id'),
                    'name': mfr.get('name'),
                    'slug': mfr.get('slug'),
                    'display': mfr.get('display')
                })
                print(f"  - {mfr.get('name')} (slug: {mfr.get('slug')})")
            
            print(f"[OK] Found {len(manufacturers)} manufacturers")
            return manufacturers
            
        except Exception as e:
            print(f"[ERROR] Error discovering manufacturers: {e}")
            return []
    
    def discover_device_types(self, manufacturer_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover available device types"""
        print("\n=== Discovering Device Types ===")
        
        try:
            params = {'limit': 100}
            if manufacturer_filter:
                # First get manufacturer ID
                mfr_response = self.session.get(
                    f"{self.api_url}/dcim/manufacturers/",
                    params={'name': manufacturer_filter, 'limit': 1},
                    verify=self.verify_ssl,
                    timeout=10
                )
                if mfr_response.status_code == 200:
                    mfr_data = mfr_response.json()
                    if mfr_data.get('results'):
                        params['manufacturer_id'] = mfr_data['results'][0]['id']
            
            response = self.session.get(
                f"{self.api_url}/dcim/device-types/",
                params=params,
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            device_types = []
            for dt in data.get('results', []):
                device_types.append({
                    'id': dt.get('id'),
                    'model': dt.get('model'),
                    'slug': dt.get('slug'),
                    'display': dt.get('display'),
                    'manufacturer': dt.get('manufacturer', {}).get('name'),
                    'part_number': dt.get('part_number')
                })
                print(f"  - {dt.get('manufacturer', {}).get('name')} {dt.get('model')} (slug: {dt.get('slug')})")
            
            print(f"[OK] Found {len(device_types)} device types")
            return device_types
            
        except Exception as e:
            print(f"[ERROR] Error discovering device types: {e}")
            return []
    
    def discover_sites(self) -> List[Dict[str, Any]]:
        """Discover available sites (for DC_ID mapping)"""
        print("\n=== Discovering Sites ===")
        
        try:
            response = self.session.get(
                f"{self.api_url}/dcim/sites/",
                params={'limit': 100},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            sites = []
            for site in data.get('results', []):
                sites.append({
                    'id': site.get('id'),
                    'name': site.get('name'),
                    'slug': site.get('slug'),
                    'display': site.get('display'),
                    'region': site.get('region', {}).get('name') if site.get('region') else None
                })
                print(f"  - {site.get('name')} (slug: {site.get('slug')})")
            
            print(f"[OK] Found {len(sites)} sites")
            return sites
            
        except Exception as e:
            print(f"[ERROR] Error discovering sites: {e}")
            return []
    
    def discover_custom_fields(self) -> List[Dict[str, Any]]:
        """Discover custom fields (for Notes and additional metadata)"""
        print("\n=== Discovering Custom Fields ===")
        
        try:
            response = self.session.get(
                f"{self.api_url}/extras/custom-fields/",
                params={'limit': 100, 'content_types': 'dcim.device'},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            custom_fields = []
            for cf in data.get('results', []):
                custom_fields.append({
                    'id': cf.get('id'),
                    'name': cf.get('name'),
                    'type': cf.get('type'),
                    'label': cf.get('label'),
                    'description': cf.get('description')
                })
                print(f"  - {cf.get('name')} ({cf.get('type')}): {cf.get('label')}")
            
            print(f"[OK] Found {len(custom_fields)} custom fields for devices")
            return custom_fields
            
        except Exception as e:
            print(f"[ERROR] Error discovering custom fields: {e}")
            return []
    
    def discover_tags(self) -> List[Dict[str, Any]]:
        """Discover available tags"""
        print("\n=== Discovering Tags ===")
        
        try:
            response = self.session.get(
                f"{self.api_url}/extras/tags/",
                params={'limit': 100},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            tags = []
            for tag in data.get('results', []):
                tags.append({
                    'id': tag.get('id'),
                    'name': tag.get('name'),
                    'slug': tag.get('slug'),
                    'color': tag.get('color')
                })
                print(f"  - {tag.get('name')} (slug: {tag.get('slug')})")
            
            print(f"[OK] Found {len(tags)} tags")
            return tags
            
        except Exception as e:
            print(f"[ERROR] Error discovering tags: {e}")
            return []
    
    def analyze_ip_addresses(self) -> Dict[str, Any]:
        """Analyze IP address structure for devices"""
        print("\n=== Analyzing IP Address Structure ===")
        
        try:
            # Get devices with primary IP
            response = self.session.get(
                f"{self.api_url}/dcim/devices/",
                params={'limit': 10, 'has_primary_ip': True},
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            ip_analysis = {
                'devices_with_ip': len(data.get('results', [])),
                'ip_fields': []
            }
            
            for device in data.get('results', [])[:3]:  # Sample first 3
                ip_info = {
                    'device_name': device.get('name'),
                    'primary_ip': device.get('primary_ip'),
                    'primary_ip4': device.get('primary_ip4'),
                    'primary_ip6': device.get('primary_ip6')
                }
                ip_analysis['ip_fields'].append(ip_info)
                
                # Get full IP details if available
                if device.get('primary_ip4'):
                    ip_id = device.get('primary_ip4')
                    ip_response = self.session.get(
                        f"{self.api_url}/ipam/ip-addresses/{ip_id}/",
                        verify=self.verify_ssl,
                        timeout=10
                    )
                    if ip_response.status_code == 200:
                        ip_data = ip_response.json()
                        ip_info['ip_address'] = ip_data.get('address')
                        ip_info['interface'] = ip_data.get('assigned_object', {})
                        print(f"  - {device.get('name')}: {ip_data.get('address')}")
            
            print(f"[OK] Analyzed IP addresses for {ip_analysis['devices_with_ip']} devices")
            return ip_analysis
            
        except Exception as e:
            print(f"[ERROR] Error analyzing IP addresses: {e}")
            return {}
    
    def generate_mapping_report(self) -> Dict[str, Any]:
        """Generate comprehensive mapping report"""
        print("\n" + "="*60)
        print("=== GENERATING MAPPING REPORT ===")
        print("="*60)
        
        report = {
            'endpoints': self.discover_endpoints(),
            'device_structure': self.analyze_device_structure(),
            'device_roles': self.discover_device_roles(),
            'manufacturers': self.discover_manufacturers(),
            'device_types': self.discover_device_types(),
            'sites': self.discover_sites(),
            'custom_fields': self.discover_custom_fields(),
            'tags': self.discover_tags(),
            'ip_analysis': self.analyze_ip_addresses(),
            'csv_to_netbox_mapping': {
                'DEVICE_TYPE': {
                    'source': 'device_type.model + device_type.manufacturer.name',
                    'condition': 'Match manufacturer and device type model/suffix'
                },
                'HOSTNAME': {
                    'source': 'device.name',
                    'condition': 'Direct mapping'
                },
                'HOST_IP': {
                    'source': 'device.primary_ip4 (parsed from address)',
                    'condition': 'Extract IP from CIDR notation if needed'
                },
                'DC_ID': {
                    'source': 'device.site.name or device.site.slug',
                    'condition': 'Map site to datacenter ID'
                },
                'TEMPLATE': {
                    'source': 'Derived from device_type.manufacturer + device_type.model',
                    'condition': 'Match against templates.csv conditions'
                },
                'TYPE': {
                    'source': 'Derived from template mapping',
                    'condition': 'From templates.yml based on DEVICE_TYPE'
                },
                'TAGS': {
                    'source': 'device.tags[]',
                    'condition': 'Convert tag names to Zabbix macro format'
                },
                'NOTES': {
                    'source': 'device.custom_fields or device.comments',
                    'condition': 'Map custom field or comments field'
                },
                'CONDITIONS': {
                    'device_role': 'device.device_role.name',
                    'manufacturer': 'device.device_type.manufacturer.name',
                    'type_suffix': 'Extract suffix from device_type.model (e.g., M6, M5)'
                }
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_file: str):
        """Save discovery report to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Report saved to: {output_file}")
        except Exception as e:
            print(f"[ERROR] Error saving report: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Netbox API Discovery Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python3 netbox_discovery.py --url https://netbox.example.com --token YOUR_TOKEN
  python3 netbox_discovery.py --url https://netbox.example.com --token YOUR_TOKEN --output report.json
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='Netbox base URL (e.g., https://netbox.example.com)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Netbox API token'
    )
    parser.add_argument(
        '--output',
        default='netbox_discovery_report.json',
        help='Output file for discovery report (default: netbox_discovery_report.json)'
    )
    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        help='Verify SSL certificates (default: False)'
    )
    
    args = parser.parse_args()
    
    # Initialize discovery
    discovery = NetboxDiscovery(
        netbox_url=args.url,
        netbox_token=args.token,
        verify_ssl=args.verify_ssl
    )
    
    # Test connection
    if not discovery.test_connection():
        print("\n[ERROR] Cannot proceed without API connection")
        sys.exit(1)
    
    # Generate report
    report = discovery.generate_mapping_report()
    
    # Save report
    discovery.save_report(report, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("=== DISCOVERY SUMMARY ===")
    print("="*60)
    print(f"Device Roles: {len(report.get('device_roles', []))}")
    print(f"Manufacturers: {len(report.get('manufacturers', []))}")
    print(f"Device Types: {len(report.get('device_types', []))}")
    print(f"Sites: {len(report.get('sites', []))}")
    print(f"Custom Fields: {len(report.get('custom_fields', []))}")
    print(f"Tags: {len(report.get('tags', []))}")
    print("\n[OK] Discovery completed successfully!")
    print(f"  Full report saved to: {args.output}")


if __name__ == '__main__':
    main()

