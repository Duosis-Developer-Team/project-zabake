#!/usr/bin/env python3
"""
Simple YAML syntax validator for templates configuration
"""
import sys
import yaml
from pathlib import Path


def validate_yaml_file(file_path):
    """Validate YAML file syntax"""
    print(f"Validating: {file_path}")
    
    if not file_path.exists():
        print(f"  ❌ ERROR: File not found")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if data is None:
            print(f"  ⚠️  WARNING: File is empty")
            return True
        
        print(f"  ✅ Valid YAML syntax")
        return True
        
    except yaml.YAMLError as e:
        print(f"  ❌ Invalid YAML syntax:")
        print(f"     {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading file:")
        print(f"     {e}")
        return False


def validate_templates_structure(templates_file):
    """Validate templates.yml structure"""
    print(f"\nValidating template structure: {templates_file.name}")
    
    with open(templates_file, 'r', encoding='utf-8') as f:
        templates = yaml.safe_load(f)
    
    if not isinstance(templates, dict):
        print("  ❌ ERROR: Templates should be a dictionary")
        return False
    
    errors = []
    warnings = []
    
    for device_type, template_list in templates.items():
        if not isinstance(template_list, list):
            errors.append(f"{device_type}: templates should be a list")
            continue
        
        for idx, template in enumerate(template_list):
            if not isinstance(template, dict):
                errors.append(f"{device_type}[{idx}]: template should be a dict")
                continue
            
            # Check required fields
            if 'name' not in template:
                errors.append(f"{device_type}[{idx}]: missing 'name' field")
            if 'type' not in template:
                errors.append(f"{device_type}[{idx}]: missing 'type' field")
            
            # Validate macros if present
            if 'macros' in template:
                macros = template['macros']
                if not isinstance(macros, dict):
                    errors.append(f"{device_type}[{idx}]: macros should be a dict")
                else:
                    for macro_key, macro_value in macros.items():
                        if not macro_key.startswith('{'):
                            warnings.append(f"{device_type}[{idx}]: macro key '{macro_key}' should start with '{{' (found: '{macro_key[0]}')")
                        if not macro_key.endswith('}'):
                            warnings.append(f"{device_type}[{idx}]: macro key '{macro_key}' should end with '}}' (found: '{macro_key[-1]}')")
            
            # Validate host_groups if present
            if 'host_groups' in template:
                host_groups = template['host_groups']
                if not isinstance(host_groups, list):
                    errors.append(f"{device_type}[{idx}]: host_groups should be a list")
    
    # Print results
    if errors:
        print(f"  ❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"     - {error}")
    else:
        print(f"  ✅ Structure validation passed")
    
    if warnings:
        print(f"  ⚠️  Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"     - {warning}")
    
    return len(errors) == 0


def validate_hpe_primera_macros(templates_file):
    """Specific validation for HPE Primera macros (regression test)"""
    print(f"\nValidating HPE Primera macros: {templates_file.name}")
    
    with open(templates_file, 'r', encoding='utf-8') as f:
        templates = yaml.safe_load(f)
    
    if 'HPE Primera' not in templates:
        print("  ❌ ERROR: HPE Primera template not found")
        return False
    
    hpe_template = templates['HPE Primera'][0]
    
    if 'macros' not in hpe_template:
        print("  ❌ ERROR: HPE Primera should have macros")
        return False
    
    macros = hpe_template['macros']
    
    # Check all required macros
    required_macros = [
        '{$HPE.PRIMERA.API.HOST}',
        '{$HPE.PRIMERA.API.PASSWORD}',  # This was the problematic one
        '{$HPE.PRIMERA.API.USERNAME}'
    ]
    
    errors = []
    for macro in required_macros:
        if macro not in macros:
            errors.append(f"Missing macro: {macro}")
        else:
            if not macros[macro]:
                errors.append(f"Macro {macro} should have a value")
            
            # Check format
            if not macro.startswith('{$'):
                errors.append(f"Macro {macro} should start with '{{$'")
            if not macro.endswith('}'):
                errors.append(f"Macro {macro} should end with '}}'")
    
    if errors:
        print(f"  ❌ Found {len(errors)} error(s):")
        for error in errors:
            print(f"     - {error}")
        return False
    else:
        print(f"  ✅ HPE Primera macros validation passed")
        print(f"     Found {len(macros)} macros:")
        for macro_key, macro_value in macros.items():
            # Mask password
            display_value = "***MASKED***" if 'PASSWORD' in macro_key else macro_value
            print(f"       • {macro_key}: {display_value}")
        return True


def main():
    """Main validation function"""
    project_root = Path(__file__).parent.parent
    templates_file = project_root / "mappings" / "templates.yml"
    template_types_file = project_root / "mappings" / "template_types.yml"
    
    print("=" * 60)
    print("YAML SYNTAX VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    # Validate YAML syntax
    all_passed &= validate_yaml_file(templates_file)
    all_passed &= validate_yaml_file(template_types_file)
    
    # Validate structure
    all_passed &= validate_templates_structure(templates_file)
    
    # Validate HPE Primera macros (regression test for the bug fix)
    all_passed &= validate_hpe_primera_macros(templates_file)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
