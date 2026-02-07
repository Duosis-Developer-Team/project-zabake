#!/usr/bin/env python3
"""
Integration test for YAML configuration-driven extraction
Compares results between config-driven and hardcoded logic
"""

import json
import sys
import os

# Add parent directory to path to import the functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml


# Sample Netbox device data (realistic structure)
SAMPLE_DEVICE = {
    'id': 456,
    'name': 'test-lenovo-01.example.com',
    'device_type': {
        'manufacturer': {'name': 'LENOVO'},
        'model': 'ThinkSystem SR650',
        'display': 'Lenovo ThinkSystem SR650'
    },
    'role': {'name': 'HOST'},
    'site': {'name': 'DC11'},
    'location': {
        'id': 10,
        'name': 'ICT11',
        'description': 'DATA HALL 1',
        'parent': None
    },
    'rack': {
        'name': 'R-101',
        'role': {'name': 'Production'}
    },
    'cluster': {'name': 'PROD-CLUSTER-01'},
    'tenant': {'name': 'Infrastructure'},
    'custom_fields': {
        'Sahiplik': 'TEAM VIRTUALIZATION',
        'Sorumlu_Ekip': 'Infrastructure Team',
        'Kurulum_Tarihi': '2024-01-15'
    },
    'tags': [
        {'name': 'production'},
        {'name': 'critical'}
    ],
    'primary_ip4': {
        'address': '10.0.1.100/24'
    }
}


# ============= ORIGINAL HARDCODED FUNCTIONS =============

def extract_tags_hardcoded(device):
    """Original hardcoded tags extraction"""
    tags = {}
    
    device_type = device.get('device_type') or {}
    manufacturer = device_type.get('manufacturer') or {}
    if manufacturer.get('name'):
        tags['Manufacturer'] = manufacturer['name']
    if device_type.get('model'):
        tags['Device_Type'] = device_type['model']
    elif device_type.get('display'):
        tags['Device_Type'] = device_type['display']
    
    location = device.get('location') or {}
    site = device.get('site') or {}
    if location.get('name'):
        tags['Location_Detail'] = location['name']
    elif site.get('name'):
        tags['Location_Detail'] = site['name']
    if site.get('name'):
        tags['City'] = site['name']
    
    tenant = device.get('tenant') or {}
    if tenant.get('name'):
        tags['Tenant'] = tenant['name']
    
    custom_fields = device.get('custom_fields') or {}
    if custom_fields.get('Sahiplik'):
        tags['Contact'] = custom_fields['Sahiplik']
    
    if custom_fields.get('Sorumlu_Ekip'):
        tags['Sorumlu_Ekip'] = custom_fields['Sorumlu_Ekip']
    if device.get('id'):
        tags['Loki_ID'] = str(device['id'])
    
    rack = device.get('rack')
    if rack:
        if isinstance(rack, dict):
            if rack.get('name'):
                tags['Rack_Name'] = rack['name']
            rack_role = rack.get('role') or {}
            if rack_role.get('name'):
                tags['Rack_Type'] = rack_role['name']
    
    cluster = device.get('cluster')
    if cluster:
        if isinstance(cluster, dict) and cluster.get('name'):
            tags['Cluster'] = cluster['name']
    
    location = device.get('location')
    if location:
        if isinstance(location, dict):
            if location.get('description'):
                tags['Hall'] = location['description']
            elif location.get('name'):
                tags['Hall'] = location['name']
    
    if custom_fields.get('Kurulum_Tarihi'):
        tags['Kurulum_Tarihi'] = custom_fields['Kurulum_Tarihi']
    
    loki_tags = []
    device_tags = device.get('tags', [])
    for tag in device_tags:
        if isinstance(tag, dict):
            tag_name = tag.get('name')
            if tag_name:
                loki_tags.append(tag_name)
        elif isinstance(tag, str):
            loki_tags.append(tag)
    
    tags = {k: v for k, v in tags.items() if v is not None and v != ''}
    
    return tags, loki_tags


def extract_host_groups_hardcoded(device, device_type):
    """Original hardcoded host groups extraction"""
    groups = []
    
    # 1. Device type (from mapping)
    if device_type:
        groups.append(device_type)
    
    # 2. Location (simplified - just use location name or site name)
    location = device.get('location') or {}
    if location.get('name'):
        groups.append(location['name'])
    else:
        site = device.get('site') or {}
        if site.get('name'):
            groups.append(site['name'])
    
    # 3. Contact (Ownership from custom_fields.Sahiplik)
    custom_fields = device.get('custom_fields') or {}
    if custom_fields.get('Sahiplik'):
        groups.append(custom_fields['Sahiplik'])
    
    return ','.join(groups) if groups else ''


# ============= CONFIG-DRIVEN FUNCTIONS (simplified for testing) =============

def extract_by_path(obj, path):
    """Extract value from nested object using dot notation"""
    if not obj or not path:
        return None
    
    keys = path.split('.')
    current = obj
    
    for key in keys:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    
    return current


def extract_by_path_with_fallback(obj, path, fallback_paths=None):
    """Extract value with fallback paths"""
    value = extract_by_path(obj, path)
    if value is not None and value != '':
        return value
    
    if fallback_paths:
        if isinstance(fallback_paths, str):
            fallback_paths = [fallback_paths]
        for fallback_path in fallback_paths:
            value = extract_by_path(obj, fallback_path)
            if value is not None and value != '':
                return value
    
    return None


def extract_hall(device):
    """Computed function to extract Hall information"""
    location = device.get('location')
    if location and isinstance(location, dict):
        if location.get('description'):
            return location['description']
        elif location.get('name'):
            return location['name']
    return None


def extract_tags_from_config(device, config):
    """Extract tags using YAML configuration"""
    tags = {}
    loki_tags = []
    
    definitions = config.get('tags', {}).get('definitions', [])
    settings = config.get('tags', {}).get('settings', {})
    
    for tag_def in definitions:
        if not tag_def.get('enabled', True):
            continue
        
        tag_name = tag_def.get('tag_name')
        source_type = tag_def.get('source_type')
        value = None
        
        if source_type == 'netbox_attribute':
            path = tag_def.get('path')
            fallback = tag_def.get('fallback')
            value = extract_by_path_with_fallback(device, path, fallback)
            
            transform = tag_def.get('transform')
            if transform == 'to_string' and value is not None:
                value = str(value)
        
        elif source_type == 'custom_field':
            field_name = tag_def.get('field_name')
            custom_fields = device.get('custom_fields') or {}
            value = custom_fields.get(field_name)
        
        elif source_type == 'computed':
            compute_func = tag_def.get('compute_function')
            if compute_func == 'extract_hall':
                value = extract_hall(device)
        
        elif source_type == 'array_expansion':
            path = tag_def.get('path')
            prefix = tag_def.get('prefix', '')
            array_data = extract_by_path(device, path)
            
            if array_data and isinstance(array_data, list):
                for item in array_data:
                    item_name = None
                    if isinstance(item, dict):
                        item_name = item.get('name')
                    elif isinstance(item, str):
                        item_name = item
                    
                    if item_name:
                        loki_tags.append(item_name)
                        tags[f'{prefix}{item_name}'] = item_name
            continue
        
        if value is not None and value != '':
            if settings.get('trim', True) and isinstance(value, str):
                value = value.strip()
            
            if settings.get('treat_empty_as_none', True) and value == '':
                continue
            
            tags[tag_name] = value
    
    if settings.get('skip_none', True):
        tags = {k: v for k, v in tags.items() if v is not None}
    
    if settings.get('skip_empty', True):
        tags = {k: v for k, v in tags.items() if v != ''}
    
    return tags, loki_tags


def get_location_name_simplified(device):
    """Simplified location extraction for testing"""
    location = device.get('location') or {}
    if location.get('name'):
        return location['name']
    site = device.get('site') or {}
    if site.get('name'):
        return site['name']
    return None


def extract_host_groups_from_config(device, config, device_type):
    """Extract host groups using YAML configuration"""
    groups = []
    
    sources = config.get('host_groups', {}).get('sources', [])
    settings = config.get('host_groups', {}).get('settings', {})
    
    sorted_sources = sorted(sources, key=lambda x: x.get('priority', 999))
    
    for source in sorted_sources:
        if not source.get('enabled', True):
            continue
        
        source_type = source.get('type')
        value = None
        
        if source_type == 'mapping_result':
            value = device_type
        
        elif source_type == 'netbox_attribute':
            path = source.get('path')
            fallback = source.get('fallback')
            value = extract_by_path_with_fallback(device, path, fallback)
        
        elif source_type == 'custom_field':
            field_name = source.get('field_name')
            custom_fields = device.get('custom_fields') or {}
            value = custom_fields.get(field_name)
        
        elif source_type == 'computed':
            # Handle computed functions
            compute_func = source.get('compute_function')
            if compute_func == 'get_location_name':
                value = get_location_name_simplified(device)
        
        if value and value != '':
            if settings.get('trim', True) and isinstance(value, str):
                value = value.strip()
            groups.append(value)
    
    if settings.get('unique', True):
        seen = set()
        unique_groups = []
        for g in groups:
            if g not in seen:
                seen.add(g)
                unique_groups.append(g)
        groups = unique_groups
    
    if settings.get('skip_empty', True):
        groups = [g for g in groups if g and g != '']
    
    separator = settings.get('separator', ',')
    return separator.join(groups) if groups else ''


# ============= INTEGRATION TEST =============

def compare_results(hardcoded, config_driven, label):
    """Compare and display results"""
    print(f"\n{'=' * 70}")
    print(f"{label}")
    print(f"{'=' * 70}")
    
    print("\nHardcoded Result:")
    print(json.dumps(hardcoded, indent=2, sort_keys=True))
    
    print("\nConfig-Driven Result:")
    print(json.dumps(config_driven, indent=2, sort_keys=True))
    
    if hardcoded == config_driven:
        print("\n[PASS] Results match!")
        return True
    else:
        print("\n[FAIL] Results differ!")
        
        # Show differences
        if isinstance(hardcoded, dict) and isinstance(config_driven, dict):
            all_keys = set(hardcoded.keys()) | set(config_driven.keys())
            for key in sorted(all_keys):
                h_val = hardcoded.get(key)
                c_val = config_driven.get(key)
                if h_val != c_val:
                    print(f"  • {key}:")
                    print(f"      Hardcoded: {h_val}")
                    print(f"      Config:    {c_val}")
        
        return False


def run_integration_test():
    """Run complete integration test"""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: YAML Config vs Hardcoded Logic")
    print("=" * 70)
    
    # Load YAML configs
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mappings')
    
    with open(os.path.join(config_dir, 'host_groups_config.yml'), 'r') as f:
        host_groups_config = yaml.safe_load(f)
    
    with open(os.path.join(config_dir, 'tags_config.yml'), 'r') as f:
        tags_config = yaml.safe_load(f)
    
    device_type = 'Lenovo IPMI'  # Simulated device type from mapping
    
    # Test 1: Tags Extraction
    tags_hardcoded, loki_tags_hardcoded = extract_tags_hardcoded(SAMPLE_DEVICE)
    
    # Add Loki tags with prefix (hardcoded logic)
    for loki_tag in loki_tags_hardcoded:
        if loki_tag:
            tags_hardcoded[f'Loki_Tag_{loki_tag}'] = loki_tag
    
    tags_config_driven, loki_tags_config = extract_tags_from_config(SAMPLE_DEVICE, tags_config)
    
    test1_pass = compare_results(tags_hardcoded, tags_config_driven, "TEST 1: Tags Extraction")
    
    # Test 2: Host Groups Extraction
    host_groups_hardcoded = extract_host_groups_hardcoded(SAMPLE_DEVICE, device_type)
    host_groups_config_driven = extract_host_groups_from_config(SAMPLE_DEVICE, host_groups_config, device_type)
    
    test2_pass = compare_results(
        {'host_groups': host_groups_hardcoded},
        {'host_groups': host_groups_config_driven},
        "TEST 2: Host Groups Extraction"
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Tags):         {'[PASS]' if test1_pass else '[FAIL]'}")
    print(f"Test 2 (Host Groups):  {'[PASS]' if test2_pass else '[FAIL]'}")
    
    all_pass = test1_pass and test2_pass
    print(f"\nOverall Result:        {'[ALL TESTS PASSED]' if all_pass else '[SOME TESTS FAILED]'}")
    print("=" * 70)
    
    return all_pass


if __name__ == '__main__':
    success = run_integration_test()
    sys.exit(0 if success else 1)
