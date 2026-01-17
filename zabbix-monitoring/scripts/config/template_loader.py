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
    connection_check_items: List[ConnectionCheckItem]
    master_items: List[MasterItem]


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
                    if item.get("key")  # Skip empty keys
                ]
            )
            self.templates.append(template)
        
        # Default priority levels (hardcoded, no longer from YAML)
        self.priority_levels = {
            "high": 1,
            "medium": 2,
            "low": 3
        }
        
        # Default thresholds (hardcoded, no longer from YAML)
        self.thresholds = {
            "max_data_age": 3600,
            "min_connectivity_score": 0.8,
            "inactive_threshold": 7200,
            "master_item_threshold": 1800
        }
        
        # Global patterns removed - not needed for monitoring
        self.global_patterns = []
    
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
