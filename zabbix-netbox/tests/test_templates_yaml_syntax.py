"""
Test YAML syntax and structure for templates configuration
"""
import pytest
import yaml
from pathlib import Path


class TestTemplatesYAMLSyntax:
    """Test suite for templates.yml syntax validation"""
    
    @pytest.fixture
    def templates_file(self):
        """Get templates.yml file path"""
        project_root = Path(__file__).parent.parent
        return project_root / "mappings" / "templates.yml"
    
    @pytest.fixture
    def template_types_file(self):
        """Get template_types.yml file path"""
        project_root = Path(__file__).parent.parent
        return project_root / "mappings" / "template_types.yml"
    
    def test_templates_yaml_is_valid(self, templates_file):
        """Test that templates.yml is valid YAML"""
        assert templates_file.exists(), f"File not found: {templates_file}"
        
        with open(templates_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "YAML file is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")
    
    def test_template_types_yaml_is_valid(self, template_types_file):
        """Test that template_types.yml is valid YAML"""
        assert template_types_file.exists(), f"File not found: {template_types_file}"
        
        with open(template_types_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "YAML file is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")
    
    def test_templates_structure(self, templates_file):
        """Test that templates have required structure"""
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        assert isinstance(templates, dict), "Templates should be a dictionary"
        
        for device_type, template_list in templates.items():
            assert isinstance(template_list, list), f"{device_type}: templates should be a list"
            
            for idx, template in enumerate(template_list):
                assert isinstance(template, dict), f"{device_type}[{idx}]: template should be a dict"
                
                # Required fields
                assert 'name' in template, f"{device_type}[{idx}]: missing 'name' field"
                assert 'type' in template, f"{device_type}[{idx}]: missing 'type' field"
                
                # Validate macros if present
                if 'macros' in template:
                    macros = template['macros']
                    assert isinstance(macros, dict), f"{device_type}[{idx}]: macros should be a dict"
                    
                    for macro_key, macro_value in macros.items():
                        # Check macro key format (should start with { and end with })
                        assert macro_key.startswith('{'), f"{device_type}[{idx}]: macro key '{macro_key}' should start with '{{'"
                        assert macro_key.endswith('}'), f"{device_type}[{idx}]: macro key '{macro_key}' should end with '}}'"
                
                # Validate host_groups if present
                if 'host_groups' in template:
                    host_groups = template['host_groups']
                    assert isinstance(host_groups, list), f"{device_type}[{idx}]: host_groups should be a list"
    
    def test_hpe_primera_macros(self, templates_file):
        """Specific test for HPE Primera macros (regression test for syntax error)"""
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        assert 'HPE Primera' in templates, "HPE Primera template not found"
        
        hpe_template = templates['HPE Primera'][0]
        assert 'macros' in hpe_template, "HPE Primera should have macros"
        
        macros = hpe_template['macros']
        
        # Check all required macros exist and have proper format
        required_macros = [
            '{$HPE.PRIMERA.API.HOST}',
            '{$HPE.PRIMERA.API.PASSWORD}',  # This was the problematic one
            '{$HPE.PRIMERA.API.USERNAME}'
        ]
        
        for macro in required_macros:
            assert macro in macros, f"Missing macro: {macro}"
            assert macros[macro], f"Macro {macro} should have a value"
            
            # Ensure macro key is properly formatted
            assert macro.startswith('{$'), f"Macro {macro} should start with '{{$'"
            assert macro.endswith('}'), f"Macro {macro} should end with '}}'"
    
    def test_all_template_types_defined(self, templates_file, template_types_file):
        """Test that all template types used in templates.yml are defined in template_types.yml"""
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        with open(template_types_file, 'r', encoding='utf-8') as f:
            template_types = yaml.safe_load(f)
        
        # Collect all types used in templates
        used_types = set()
        for device_type, template_list in templates.items():
            for template in template_list:
                if 'type' in template:
                    used_types.add(template['type'])
        
        # Check all used types are defined
        defined_types = set(template_types.keys())
        undefined_types = used_types - defined_types
        
        assert not undefined_types, f"Undefined template types: {undefined_types}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
