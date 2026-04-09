#!/usr/bin/env python3
"""
Unit tests for device type mapping (find_matching_mapping, hostname_prefix/suffix).
Logic copied from process_device.yml — keep in sync when changing matching rules.
"""

import unittest


def check_condition(device, condition_key, condition_value):
    """Check if device matches a condition"""
    if condition_key == 'device_role':
        role_obj = device.get('role') or device.get('device_role')
        role = role_obj.get('name', '') if role_obj and isinstance(role_obj, dict) else ''
        if isinstance(condition_value, list):
            return role.upper() in [v.upper() for v in condition_value]
        return role.upper() == condition_value.upper()

    elif condition_key == 'manufacturer':
        device_type = device.get('device_type') or {}
        manufacturer_obj = device_type.get('manufacturer') or {}
        manufacturer = manufacturer_obj.get('name', '').upper()
        if isinstance(condition_value, list):
            return manufacturer in [v.upper() for v in condition_value]
        return manufacturer == condition_value.upper()

    elif condition_key == 'model_contains':
        device_type = device.get('device_type') or {}
        model = device_type.get('model', '').upper()
        if isinstance(condition_value, list):
            return any(item.upper() in model for item in condition_value)
        return condition_value.upper() in model

    elif condition_key == 'model_suffix':
        device_type = device.get('device_type') or {}
        model = device_type.get('model', '').upper()
        if isinstance(condition_value, list):
            return any(model.endswith(item.upper()) for item in condition_value)
        return model.endswith(condition_value.upper())

    elif condition_key == 'name_contains':
        device_name = device.get('name', '').upper()
        if isinstance(condition_value, list):
            return any(item.upper() in device_name for item in condition_value)
        return condition_value.upper() in device_name

    return False


def find_matching_mapping(device, device_type_mapping):
    """Return the first matching mapping dict from YAML, or None."""
    mappings = device_type_mapping.get('mappings', [])
    sorted_mappings = sorted(mappings, key=lambda x: x.get('priority', 999))
    for mapping in sorted_mappings:
        conditions = mapping.get('conditions', {})
        all_match = True
        for condition_key, condition_value in conditions.items():
            if not check_condition(device, condition_key, condition_value):
                all_match = False
                break
        if all_match:
            return mapping
    return None


def determine_device_type(device, device_type_mapping):
    """Determine device type from YAML mapping"""
    m = find_matching_mapping(device, device_type_mapping)
    return m.get('device_type') if m else None


class TestFindMatchingMapping(unittest.TestCase):
    """Tests for mapping match and hostname customization fields."""

    def _inspur_m6_device(self):
        return {
            'name': 'srv-bmc-01',
            'role': {'name': 'HOST'},
            'device_type': {
                'manufacturer': {'name': 'INSPUR'},
                'model': 'NF5280M6',
            },
        }

    def test_inspur_m6_returns_hostname_suffix(self):
        mapping = {
            'mappings': [
                {
                    'device_type': 'Inspur M6',
                    'conditions': {
                        'device_role': 'HOST',
                        'manufacturer': ['INSPUR', 'Inspur'],
                        'model_contains': ['M6'],
                        'model_suffix': 'M6',
                    },
                    'hostname_suffix': ' - BMC',
                    'priority': 1,
                },
            ]
        }
        m = find_matching_mapping(self._inspur_m6_device(), mapping)
        self.assertIsNotNone(m)
        self.assertEqual(m.get('device_type'), 'Inspur M6')
        self.assertEqual(m.get('hostname_suffix'), ' - BMC')
        self.assertEqual(m.get('hostname_prefix', ''), '')

    def test_determine_device_type_inspur_m6(self):
        mapping = {
            'mappings': [
                {
                    'device_type': 'Inspur M6',
                    'conditions': {
                        'device_role': 'HOST',
                        'manufacturer': 'INSPUR',
                        'model_contains': ['M6'],
                        'model_suffix': 'M6',
                    },
                    'priority': 1,
                },
            ]
        }
        dt = determine_device_type(self._inspur_m6_device(), mapping)
        self.assertEqual(dt, 'Inspur M6')

    def test_no_match_returns_none(self):
        mapping = {
            'mappings': [
                {
                    'device_type': 'Other',
                    'conditions': {'device_role': 'NETWORK'},
                    'priority': 1,
                },
            ]
        }
        self.assertIsNone(find_matching_mapping(self._inspur_m6_device(), mapping))
        self.assertIsNone(determine_device_type(self._inspur_m6_device(), mapping))

    def test_priority_lower_number_wins(self):
        device = {
            'role': {'name': 'HOST'},
            'device_type': {'manufacturer': {'name': 'LENOVO'}, 'model': 'XCC'},
        }
        mapping = {
            'mappings': [
                {
                    'device_type': 'Generic HOST',
                    'conditions': {'device_role': 'HOST'},
                    'hostname_prefix': 'GEN-',
                    'priority': 10,
                },
                {
                    'device_type': 'Lenovo specific',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'LENOVO'},
                    'hostname_prefix': 'LV-',
                    'priority': 1,
                },
            ]
        }
        m = find_matching_mapping(device, mapping)
        self.assertEqual(m.get('device_type'), 'Lenovo specific')
        self.assertEqual(m.get('hostname_prefix'), 'LV-')


if __name__ == '__main__':
    unittest.main()
