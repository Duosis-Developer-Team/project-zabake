#!/usr/bin/env python3
"""
Netbox helper functions for Ansible
"""
import json
import requests
from typing import Dict, Any, Optional, List


def determine_device_type(device: Dict[str, Any], templates_map: Dict[str, Any]) -> Optional[str]:
    """
    Determine device type from Netbox device based on template mappings
    
    Args:
        device: Netbox device object
        templates_map: Template mapping dictionary
        
    Returns:
        Device type string or None if no match
    """
    role = device.get('device_role', {}).get('name', '')
    manufacturer = device.get('device_type', {}).get('manufacturer', {}).get('name', '').upper()
    model = device.get('device_type', {}).get('model', '').upper()
    device_name = device.get('name', '').upper()
    
    # Device Role must be HOST
    if role != 'HOST':
        return None
    
    # Check templates map for matching device type
    for dev_type, templates in templates_map.items():
        # Lenovo IPMI or Lenovo ICT
        if 'LENOVO' in manufacturer and 'Lenovo' in dev_type:
            if 'ICT' in model or 'XCC' in model or 'ICT' in device_name:
                return 'Lenovo ICT'
            else:
                return 'Lenovo IPMI'
        
        # Inspur M6 or M5
        elif 'INSPUR' in manufacturer and 'Inspur' in dev_type:
            if 'M6' in model or model.endswith('M6'):
                return 'Inspur M6'
            elif 'M5' in model or model.endswith('M5'):
                return 'Inspur M5'
        
        # HPE IPMI or HP ILO
        elif 'HPE' in manufacturer or 'HP' in manufacturer:
            if 'ILO' in model or 'ILO' in device_name:
                return 'HP ILO'
            else:
                return 'HPE IPMI'
        
        # Dell IPMI
        elif 'DELL' in manufacturer and 'Dell' in dev_type:
            return 'Dell IPMI'
        
        # Other device types - check if manufacturer matches
        elif manufacturer and dev_type:
            # Check if manufacturer name is in device type or vice versa
            if manufacturer.replace(' ', '') in dev_type.replace(' ', '').upper() or \
               dev_type.replace(' ', '').upper() in manufacturer.replace(' ', ''):
                return dev_type
    
    return None


def get_primary_ip(device: Dict[str, Any], netbox_url: str, netbox_token: str, verify_ssl: bool = False) -> Optional[str]:
    """
    Get primary IP address from Netbox device
    
    Args:
        device: Netbox device object
        netbox_url: Netbox base URL
        netbox_token: Netbox API token
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        IP address string or None
    """
    primary_ip_id = device.get('primary_ip4')
    if not primary_ip_id:
        return None
    
    # If primary_ip4 is an ID, fetch the IP address
    if isinstance(primary_ip_id, int):
        try:
            response = requests.get(
                f"{netbox_url.rstrip('/')}/api/ipam/ip-addresses/{primary_ip_id}/",
                headers={'Authorization': f'Token {netbox_token}', 'Accept': 'application/json'},
                verify=verify_ssl,
                timeout=10
            )
            if response.status_code == 200:
                ip_data = response.json()
                address = ip_data.get('address', '')
                # Extract IP from CIDR (10.0.0.1/24 -> 10.0.0.1)
                return address.split('/')[0] if '/' in address else address
        except Exception as e:
            print(f"Error fetching IP address: {e}")
            return None
    
    # If it's already a string, extract IP
    if isinstance(primary_ip_id, str):
        return primary_ip_id.split('/')[0] if '/' in primary_ip_id else primary_ip_id
    
    return None


def extract_host_groups(device: Dict[str, Any]) -> str:
    """
    Extract host groups from Netbox device
    
    Args:
        device: Netbox device object
        
    Returns:
        Comma-separated host groups string
    """
    groups = []
    
    # Site (Location)
    if device.get('site', {}).get('name'):
        groups.append(device['site']['name'])
    
    # Device Type
    if device.get('device_type', {}).get('model'):
        groups.append(device['device_type']['model'])
    elif device.get('device_type', {}).get('display'):
        groups.append(device['device_type']['display'])
    
    return ','.join(groups) if groups else ''


def extract_tags(device: Dict[str, Any]) -> str:
    """
    Extract tags from Netbox device for Zabbix
    
    Args:
        device: Netbox device object
        
    Returns:
        JSON string of tags (CSV-escaped)
    """
    tags = {}
    
    # Manufacturer
    if device.get('device_type', {}).get('manufacturer', {}).get('name'):
        tags['Manufacturer'] = device['device_type']['manufacturer']['name']
    
    # Device Type
    if device.get('device_type', {}).get('model'):
        tags['Device_Type'] = device['device_type']['model']
    elif device.get('device_type', {}).get('display'):
        tags['Device_Type'] = device['device_type']['display']
    
    # Location Detail
    if device.get('location', {}).get('name'):
        tags['Location_Detail'] = device['location']['name']
    elif device.get('site', {}).get('name'):
        tags['Location_Detail'] = device['site']['name']
    
    # City
    if device.get('site', {}).get('name'):
        tags['City'] = device['site']['name']
    
    # Customer (if exists)
    if device.get('tenant', {}).get('name'):
        tags['Customer'] = device['tenant']['name']
    
    # Sorumlu Ekip (if exists)
    custom_fields = device.get('custom_fields', {})
    if custom_fields.get('Sorumlu_Ekip'):
        tags['Sorumlu_Ekip'] = custom_fields['Sorumlu_Ekip']
    
    # Loki ID
    if device.get('id'):
        tags['Loki_ID'] = str(device['id'])
    
    # Convert to JSON and escape for CSV
    return json.dumps(tags).replace('"', '""')


class FilterModule(object):
    """Ansible filter plugin for Netbox helpers"""
    
    def filters(self):
        return {
            'determine_device_type': determine_device_type,
            'get_primary_ip': get_primary_ip,
            'extract_host_groups': extract_host_groups,
            'extract_tags': extract_tags,
        }


