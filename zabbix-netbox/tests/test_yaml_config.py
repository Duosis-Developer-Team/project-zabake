#!/usr/bin/env python3
"""
Unit tests for YAML configuration-driven host groups and tags extraction
Tests the Python functions in process_device.yml without Ansible
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, mock_open
import yaml
import tempfile


# ============= HELPER FUNCTIONS (copied from process_device.yml) =============

def extract_by_path(obj, path):
    """
    Extract value from nested object using dot notation path
    Example: extract_by_path(device, "device_type.manufacturer.name")
    Returns None if path doesn't exist
    """
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
    """
    Extract value with fallback paths
    Returns first non-None value found
    """
    # Try primary path
    value = extract_by_path(obj, path)
    if value is not None and value != '':
        return value
    
    # Try fallback paths
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
        # Try description first (e.g., "DATA HALL X")
        if location.get('description'):
            return location['description']
        elif location.get('name'):
            return location['name']
    return None


# ============= TEST CLASSES =============

class TestExtractByPath(unittest.TestCase):
    """Test the extract_by_path function"""
    
    def test_simple_path(self):
        """Test extraction of simple path"""
        obj = {'name': 'test-device'}
        result = extract_by_path(obj, 'name')
        self.assertEqual(result, 'test-device')
    
    def test_nested_path(self):
        """Test extraction of nested path"""
        obj = {
            'device_type': {
                'manufacturer': {
                    'name': 'LENOVO'
                }
            }
        }
        result = extract_by_path(obj, 'device_type.manufacturer.name')
        self.assertEqual(result, 'LENOVO')
    
    def test_missing_path(self):
        """Test extraction of non-existent path"""
        obj = {'name': 'test-device'}
        result = extract_by_path(obj, 'device_type.manufacturer.name')
        self.assertIsNone(result)
    
    def test_none_object(self):
        """Test with None object"""
        result = extract_by_path(None, 'name')
        self.assertIsNone(result)
    
    def test_empty_path(self):
        """Test with empty path"""
        obj = {'name': 'test-device'}
        result = extract_by_path(obj, '')
        self.assertIsNone(result)


class TestExtractByPathWithFallback(unittest.TestCase):
    """Test the extract_by_path_with_fallback function"""
    
    def test_primary_path_exists(self):
        """Test when primary path exists"""
        obj = {
            'device_type': {'model': 'NF5280M6'},
            'site': {'name': 'DC11'}
        }
        result = extract_by_path_with_fallback(obj, 'device_type.model', 'site.name')
        self.assertEqual(result, 'NF5280M6')
    
    def test_fallback_to_second_path(self):
        """Test fallback to secondary path"""
        obj = {
            'site': {'name': 'DC11'}
        }
        result = extract_by_path_with_fallback(obj, 'device_type.model', 'site.name')
        self.assertEqual(result, 'DC11')
    
    def test_fallback_list(self):
        """Test with multiple fallback paths"""
        obj = {
            'site': {'name': 'DC11'}
        }
        result = extract_by_path_with_fallback(
            obj, 
            'device_type.model', 
            ['device_type.display', 'site.name']
        )
        self.assertEqual(result, 'DC11')
    
    def test_no_value_found(self):
        """Test when no path has a value"""
        obj = {}
        result = extract_by_path_with_fallback(obj, 'primary', 'fallback')
        self.assertIsNone(result)


class TestExtractHall(unittest.TestCase):
    """Test the extract_hall computed function"""
    
    def test_hall_from_description(self):
        """Test Hall extraction from location description"""
        device = {
            'location': {
                'name': 'ICT11',
                'description': 'DATA HALL 1'
            }
        }
        result = extract_hall(device)
        self.assertEqual(result, 'DATA HALL 1')
    
    def test_hall_from_name(self):
        """Test Hall extraction from location name when description is empty"""
        device = {
            'location': {
                'name': 'ICT11'
            }
        }
        result = extract_hall(device)
        self.assertEqual(result, 'ICT11')
    
    def test_no_location(self):
        """Test when device has no location"""
        device = {}
        result = extract_hall(device)
        self.assertIsNone(result)


class TestTagsConfigExtraction(unittest.TestCase):
    """Test tags extraction using YAML config"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.device = {
            'id': 123,
            'name': 'test-server-01',
            'device_type': {
                'manufacturer': {'name': 'LENOVO'},
                'model': 'ThinkSystem SR650'
            },
            'site': {'name': 'DC11'},
            'location': {
                'name': 'ICT11',
                'description': 'DATA HALL 1'
            },
            'rack': {
                'name': 'R01',
                'role': {'name': 'Production'}
            },
            'cluster': {'name': 'PROD-CLUSTER-01'},
            'tenant': {'name': 'ACME Corp'},
            'custom_fields': {
                'Sahiplik': 'TEAM VIRTUALIZATION',
                'Sorumlu_Ekip': 'Infrastructure Team',
                'Kurulum_Tarihi': '2024-01-15'
            },
            'tags': [
                {'name': 'production'},
                {'name': 'critical'}
            ]
        }
        
        self.tags_config = {
            'tags': {
                'definitions': [
                    {
                        'tag_name': 'Manufacturer',
                        'source_type': 'netbox_attribute',
                        'path': 'device_type.manufacturer.name',
                        'enabled': True
                    },
                    {
                        'tag_name': 'Device_Type',
                        'source_type': 'netbox_attribute',
                        'path': 'device_type.model',
                        'fallback': 'device_type.display',
                        'enabled': True
                    },
                    {
                        'tag_name': 'Contact',
                        'source_type': 'custom_field',
                        'field_name': 'Sahiplik',
                        'enabled': True
                    },
                    {
                        'tag_name': 'Hall',
                        'source_type': 'computed',
                        'compute_function': 'extract_hall',
                        'enabled': True
                    },
                    {
                        'tag_name': 'Loki_ID',
                        'source_type': 'netbox_attribute',
                        'path': 'id',
                        'transform': 'to_string',
                        'enabled': True
                    }
                ],
                'settings': {
                    'skip_empty': True,
                    'skip_none': True,
                    'trim': True
                }
            }
        }
    
    def test_netbox_attribute_extraction(self):
        """Test extraction of Netbox attributes"""
        result = extract_by_path(self.device, 'device_type.manufacturer.name')
        self.assertEqual(result, 'LENOVO')
    
    def test_custom_field_extraction(self):
        """Test extraction of custom fields"""
        custom_fields = self.device.get('custom_fields', {})
        result = custom_fields.get('Sahiplik')
        self.assertEqual(result, 'TEAM VIRTUALIZATION')
    
    def test_computed_hall_extraction(self):
        """Test computed Hall extraction"""
        result = extract_hall(self.device)
        self.assertEqual(result, 'DATA HALL 1')
    
    def test_to_string_transform(self):
        """Test to_string transformation"""
        value = self.device.get('id')
        transformed = str(value)
        self.assertEqual(transformed, '123')
        self.assertIsInstance(transformed, str)


class TestHostGroupsConfigExtraction(unittest.TestCase):
    """Test host groups extraction using YAML config"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.device = {
            'name': 'test-server-01',
            'device_type': {
                'manufacturer': {'name': 'LENOVO'}
            },
            'site': {'name': 'DC11'},
            'location': {
                'name': 'ICT11'
            },
            'custom_fields': {
                'Sahiplik': 'TEAM VIRTUALIZATION'
            }
        }
        
        self.host_groups_config = {
            'host_groups': {
                'sources': [
                    {
                        'name': 'device_type_mapping',
                        'type': 'mapping_result',
                        'enabled': True,
                        'priority': 1
                    },
                    {
                        'name': 'location',
                        'type': 'netbox_attribute',
                        'enabled': True,
                        'priority': 2,
                        'path': 'location.name',
                        'fallback': 'site.name'
                    },
                    {
                        'name': 'ownership',
                        'type': 'custom_field',
                        'enabled': True,
                        'priority': 3,
                        'field_name': 'Sahiplik'
                    }
                ],
                'settings': {
                    'separator': ',',
                    'skip_empty': True,
                    'unique': True,
                    'trim': True
                }
            }
        }
    
    def test_priority_sorting(self):
        """Test that sources are sorted by priority"""
        sources = self.host_groups_config['host_groups']['sources']
        sorted_sources = sorted(sources, key=lambda x: x.get('priority', 999))
        
        self.assertEqual(sorted_sources[0]['name'], 'device_type_mapping')
        self.assertEqual(sorted_sources[1]['name'], 'location')
        self.assertEqual(sorted_sources[2]['name'], 'ownership')
    
    def test_custom_field_source(self):
        """Test custom field source extraction"""
        source = self.host_groups_config['host_groups']['sources'][2]
        field_name = source['field_name']
        custom_fields = self.device.get('custom_fields', {})
        value = custom_fields.get(field_name)
        
        self.assertEqual(value, 'TEAM VIRTUALIZATION')
    
    def test_unique_groups(self):
        """Test duplicate removal"""
        groups = ['Lenovo IPMI', 'DC11', 'DC11', 'TEAM VIRTUALIZATION']
        
        # Apply unique logic
        seen = set()
        unique_groups = []
        for g in groups:
            if g not in seen:
                seen.add(g)
                unique_groups.append(g)
        
        self.assertEqual(len(unique_groups), 3)
        self.assertEqual(unique_groups, ['Lenovo IPMI', 'DC11', 'TEAM VIRTUALIZATION'])


class TestYAMLConfigLoading(unittest.TestCase):
    """Test YAML configuration file loading"""
    
    def test_load_valid_yaml(self):
        """Test loading a valid YAML file"""
        yaml_content = """
host_groups:
  sources:
    - name: "test_source"
      type: "mapping_result"
      enabled: true
      priority: 1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            with open(temp_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.assertIsNotNone(config)
            self.assertIn('host_groups', config)
            self.assertIn('sources', config['host_groups'])
        finally:
            os.unlink(temp_file)
    
    def test_load_missing_file(self):
        """Test loading a non-existent file"""
        result = os.path.exists('/tmp/nonexistent_config.yml')
        self.assertFalse(result)


class TestArrayExpansion(unittest.TestCase):
    """Test array expansion for Loki tags"""
    
    def test_loki_tags_expansion(self):
        """Test expansion of Netbox tags array"""
        device = {
            'tags': [
                {'name': 'production'},
                {'name': 'critical'},
                'monitoring'  # Test both dict and string formats
            ]
        }
        
        # Simulate array expansion
        tags_dict = {}
        loki_tags = []
        prefix = 'Loki_Tag_'
        
        device_tags = device.get('tags', [])
        for tag in device_tags:
            item_name = None
            if isinstance(tag, dict):
                item_name = tag.get('name')
            elif isinstance(tag, str):
                item_name = tag
            
            if item_name:
                loki_tags.append(item_name)
                tags_dict[f'{prefix}{item_name}'] = item_name
        
        self.assertEqual(len(loki_tags), 3)
        self.assertIn('production', loki_tags)
        self.assertIn('Loki_Tag_production', tags_dict)
        self.assertEqual(tags_dict['Loki_Tag_production'], 'production')


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("=" * 70)
    print("Running YAML Configuration Tests")
    print("=" * 70)
    run_tests()
