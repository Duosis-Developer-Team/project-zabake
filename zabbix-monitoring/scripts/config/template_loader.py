"""
Template and Item Configuration Loader
Loads template and item definitions from YAML files
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConnectionCheckItem:
    """Connection check item definition"""
    key: str
    name: str
    required: bool
    priority: str
    is_discovery: bool = False
    discovery_rule_note: Optional[str] = None


@dataclass
class MasterItem:
    """Master item definition"""
    key: str
    name: str
    required: bool
    priority: str


@dataclass
class TemplateConfig:
    """Template configuration"""
    name: str
    vendor: str
    type: str
    conditions: Dict[str, Any]
    connection_check_items: List[ConnectionCheckItem]
    master_items: List[MasterItem]
    notes: str


@dataclass
class GlobalPattern:
    """Global connection check pattern"""
    pattern: str
    name_pattern: str
    priority: str


class TemplateConfigLoader:
    """Load and manage template configurations"""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize template config loader
        
        Args:
            mapping_file: Path to templates.yml file
        """
        if mapping_file is None:
            base_dir = Path(__file__).parent.parent.parent
            mapping_file = base_dir / "mappings" / "templates.yml"
        
        self.mapping_file = Path(mapping_file)
        self.templates: List[TemplateConfig] = []
        self.global_patterns: List[GlobalPattern] = []
        self.thresholds: Dict[str, Any] = {}
        self.priority_levels: Dict[str, int] = {}
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Template mapping file not found: {self.mapping_file}")
        
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Load templates
        self.templates = []
        for template_data in config.get("templates", []):
            template = TemplateConfig(
                name=template_data["name"],
                vendor=template_data["vendor"],
                type=template_data["type"],
                conditions=template_data.get("conditions", {}),
                connection_check_items=[
                    ConnectionCheckItem(
                        key=item.get("key", ""),
                        name=item.get("name", ""),
                        required=item.get("required", False),
                        priority=item.get("priority", "medium"),
                        is_discovery=item.get("is_discovery", False),
                        discovery_rule_note=item.get("discovery_rule_note")
                    )
                    for item in template_data.get("connection_check_items", [])
                ],
                master_items=[
                    MasterItem(
                        key=item.get("key", ""),
                        name=item.get("name", ""),
                        required=item.get("required", False),
                        priority=item.get("priority", "medium")
                    )
                    for item in template_data.get("master_items", [])
                ],
                notes=template_data.get("notes", "")
            )
            self.templates.append(template)
        
        # Load global patterns
        self.global_patterns = [
            GlobalPattern(
                pattern=pattern.get("pattern", ""),
                name_pattern=pattern.get("name_pattern", ""),
                priority=pattern.get("priority", "medium")
            )
            for pattern in config.get("global_connection_patterns", [])
        ]
        
        # Load thresholds
        self.thresholds = config.get("thresholds", {})
        
        # Load priority levels
        self.priority_levels = config.get("priority_levels", {
            "high": 1,
            "medium": 2,
            "low": 3
        })
    
    def get_template_by_name(self, template_name: str) -> Optional[TemplateConfig]:
        """
        Get template configuration by name
        
        Args:
            template_name: Template name
            
        Returns:
            TemplateConfig or None
        """
        for template in self.templates:
            if template.name == template_name:
                return template
        return None
    
    def get_templates_by_vendor(self, vendor: str) -> List[TemplateConfig]:
        """
        Get templates by vendor
        
        Args:
            vendor: Vendor name
            
        Returns:
            List of TemplateConfig
        """
        return [t for t in self.templates if t.vendor == vendor]
    
    def get_connection_check_items(self, template_name: str) -> List[ConnectionCheckItem]:
        """
        Get connection check items for a template
        
        Args:
            template_name: Template name
            
        Returns:
            List of ConnectionCheckItem
        """
        template = self.get_template_by_name(template_name)
        if template:
            return template.connection_check_items
        return []
    
    def get_master_items(self, template_name: str) -> List[MasterItem]:
        """
        Get master items for a template
        
        Args:
            template_name: Template name
            
        Returns:
            List of MasterItem
        """
        template = self.get_template_by_name(template_name)
        if template:
            return template.master_items
        return []
    
    def get_all_connection_check_items(self) -> List[ConnectionCheckItem]:
        """
        Get all connection check items from all templates
        
        Returns:
            List of ConnectionCheckItem
        """
        items = []
        for template in self.templates:
            items.extend(template.connection_check_items)
        return items
    
    def get_all_master_items(self) -> List[MasterItem]:
        """
        Get all master items from all templates
        
        Returns:
            List of MasterItem
        """
        items = []
        for template in self.templates:
            items.extend(template.master_items)
        return items
    
    def match_template_conditions(self, template: TemplateConfig, host_data: Dict[str, Any]) -> bool:
        """
        Check if template conditions match host data
        
        Args:
            template: Template configuration
            host_data: Host data dictionary
            
        Returns:
            True if conditions match
        """
        conditions = template.conditions
        
        # Check device_role
        if "device_role" in conditions:
            if host_data.get("device_role") != conditions["device_role"]:
                return False
        
        # Check manufacturer
        if "manufacturer" in conditions:
            manufacturer = conditions["manufacturer"]
            if manufacturer != "-":  # Skip if manufacturer is "-"
                if host_data.get("manufacturer", "").upper() != manufacturer.upper():
                    return False
        
        # Check type_suffix (for Inspur M5/M6)
        if "type_suffix" in conditions:
            host_type = host_data.get("type", "")
            if conditions["type_suffix"] not in host_type:
                return False
        
        return True
    
    def get_threshold(self, key: str, default: Any = None) -> Any:
        """
        Get threshold value
        
        Args:
            key: Threshold key
            default: Default value if not found
            
        Returns:
            Threshold value
        """
        return self.thresholds.get(key, default)
    
    def get_priority_level(self, priority: str) -> int:
        """
        Get priority level number
        
        Args:
            priority: Priority string (high, medium, low)
            
        Returns:
            Priority level number
        """
        return self.priority_levels.get(priority.lower(), 2)
