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


def mapping_tenant_allowlist(mapping):
    """
    Optional tenant restriction on a mapping row (same level as conditions).
    If 'tenants' key is present, only that list is used; otherwise 'tenant' if set.
    Returns None when there is no restriction.
    """
    if 'tenants' in mapping and mapping.get('tenants') is not None:
        raw = mapping.get('tenants')
        if isinstance(raw, list):
            names = [str(x).strip() for x in raw if x is not None and str(x).strip()]
        else:
            names = [str(raw).strip()] if str(raw).strip() else []
        return names if names else None
    t1 = mapping.get('tenant')
    if t1 is not None and str(t1).strip():
        return [str(t1).strip()]
    return None


def mapping_applies_for_tenant(device, mapping):
    """If mapping has tenant/tenants, device must have tenant.name in allowlist."""
    allow = mapping_tenant_allowlist(mapping)
    if not allow:
        return True
    tenant_obj = device.get('tenant') or {}
    if not isinstance(tenant_obj, dict):
        return False
    dev_name = (tenant_obj.get('name') or '').strip()
    if not dev_name:
        return False
    dev_u = dev_name.upper()
    return any(n.strip().upper() == dev_u for n in allow)


def find_matching_mapping(device, device_type_mapping):
    """Return the first matching mapping dict from YAML, or None."""
    mappings = device_type_mapping.get('mappings', [])
    sorted_mappings = sorted(mappings, key=lambda x: x.get('priority', 999))
    for mapping in sorted_mappings:
        if not mapping_applies_for_tenant(device, mapping):
            continue
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

    def test_tenant_restricted_row_skipped_when_device_has_no_tenant(self):
        device = {
            'name': 'srv-01',
            'role': {'name': 'HOST'},
            'device_type': {'manufacturer': {'name': 'DELL'}, 'model': 'R740'},
        }
        mapping = {
            'mappings': [
                {
                    'device_type': 'Dell Customer',
                    'tenant': 'ACME',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 1,
                },
                {
                    'device_type': 'Dell Generic',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 2,
                },
            ]
        }
        m = find_matching_mapping(device, mapping)
        self.assertIsNotNone(m)
        self.assertEqual(m.get('device_type'), 'Dell Generic')

    def test_tenant_restricted_row_matches_when_tenant_matches_case_insensitive(self):
        device = {
            'name': 'srv-01',
            'role': {'name': 'HOST'},
            'tenant': {'name': 'acme corp'},
            'device_type': {'manufacturer': {'name': 'DELL'}, 'model': 'R740'},
        }
        mapping = {
            'mappings': [
                {
                    'device_type': 'Dell Customer',
                    'tenants': ['ACME Corp', 'OtherCo'],
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 1,
                },
                {
                    'device_type': 'Dell Generic',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 2,
                },
            ]
        }
        m = find_matching_mapping(device, mapping)
        self.assertIsNotNone(m)
        self.assertEqual(m.get('device_type'), 'Dell Customer')

    def test_wrong_tenant_skips_row_then_matches_generic(self):
        device = {
            'name': 'srv-01',
            'role': {'name': 'HOST'},
            'tenant': {'name': 'InfraTeam'},
            'device_type': {'manufacturer': {'name': 'DELL'}, 'model': 'R740'},
        }
        mapping = {
            'mappings': [
                {
                    'device_type': 'Dell Customer',
                    'tenant': 'ACME',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 1,
                },
                {
                    'device_type': 'Dell Generic',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 2,
                },
            ]
        }
        m = find_matching_mapping(device, mapping)
        self.assertEqual(m.get('device_type'), 'Dell Generic')

    def test_tenants_key_takes_precedence_over_tenant_field(self):
        device = {
            'role': {'name': 'HOST'},
            'tenant': {'name': 'FromTenants'},
            'device_type': {'manufacturer': {'name': 'DELL'}, 'model': 'X'},
        }
        mapping = {
            'mappings': [
                {
                    'device_type': 'Dell TenantsList',
                    'tenants': ['FromTenants'],
                    'tenant': 'IgnoredSingle',
                    'conditions': {'device_role': 'HOST', 'manufacturer': 'DELL'},
                    'priority': 1,
                },
            ]
        }
        m = find_matching_mapping(device, mapping)
        self.assertIsNotNone(m)
        self.assertEqual(m.get('device_type'), 'Dell TenantsList')


def merge_proxy_group_by_dc_from_templates(zbx_templates):
    """
    Mirror Ansible: _zbx_merged_pg_by_dc initialized to {} then combine each template's proxy_group_by_dc.
    """
    merged = {}
    for item in zbx_templates or []:
        if isinstance(item, dict) and item.get('proxy_group_by_dc'):
            sub = item['proxy_group_by_dc']
            if isinstance(sub, dict):
                merged = {**merged, **sub}
    return merged


class TestProxyGroupByDcMerge(unittest.TestCase):
    """Merge semantics for templates.yml proxy_group_by_dc (zabbix_host_operations.yml)."""

    def test_single_template_merge(self):
        zbx_templates = [
            {
                'name': 'T1',
                'proxy_group_by_dc': {'DC13': 'Moneygram-prod-proxy Group', 'DC16': 'Moneygram-dr-proxy Group'},
            }
        ]
        self.assertEqual(
            merge_proxy_group_by_dc_from_templates(zbx_templates)['DC13'],
            'Moneygram-prod-proxy Group',
        )

    def test_later_template_overwrites_same_dc_key(self):
        zbx_templates = [
            {'name': 'A', 'proxy_group_by_dc': {'DC13': 'First'}},
            {'name': 'B', 'proxy_group_by_dc': {'DC13': 'Second'}},
        ]
        self.assertEqual(merge_proxy_group_by_dc_from_templates(zbx_templates)['DC13'], 'Second')


if __name__ == '__main__':
    unittest.main()
