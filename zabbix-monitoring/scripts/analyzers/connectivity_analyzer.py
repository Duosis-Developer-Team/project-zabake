"""
Connectivity Item Analyzer
Detects and analyzes connectivity items based on template configuration
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import fnmatch

from ..utils.logger import get_logger
from ..config.template_loader import TemplateConfigLoader, ConnectionCheckItem, MasterItem

logger = get_logger(__name__)


class ConnectivityItem:
    """Connectivity item representation"""
    
    def __init__(self, item_data: Dict[str, Any], config_item: ConnectionCheckItem, template_name: str):
        """
        Initialize connectivity item
        
        Args:
            item_data: Item data from Zabbix
            config_item: Connection check item configuration
            template_name: Template name
        """
        self.itemid = item_data.get("itemid")
        self.hostid = item_data.get("hostid")
        self.key = item_data.get("key_", "")
        self.name = item_data.get("name", "")
        self.template = template_name
        self.type = item_data.get("type", "")
        self.value_type = item_data.get("value_type", "")
        self.status = item_data.get("status", "")
        self.lastvalue = item_data.get("lastvalue", "")
        self.lastclock = item_data.get("lastclock", "")
        
        # From configuration
        self.required = config_item.required
        self.priority = config_item.priority
        self.is_discovery = config_item.is_discovery
        self.discovery_rule_note = config_item.discovery_rule_note


class ConnectivityAnalyzer:
    """Connectivity item analyzer"""
    
    def __init__(self, template_loader: TemplateConfigLoader):
        """
        Initialize connectivity analyzer
        
        Args:
            template_loader: Template configuration loader
        """
        self.template_loader = template_loader
        logger.info("Connectivity analyzer initialized")
    
    def detect_connectivity_items(
        self,
        hosts_data: List[Dict[str, Any]],
        items_data: List[Dict[str, Any]],
        templates_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect connectivity items for all hosts
        
        Args:
            hosts_data: List of host dictionaries
            items_data: List of item dictionaries
            templates_data: List of template dictionaries
            
        Returns:
            List of connectivity item dictionaries
        """
        logger.info(f"Detecting connectivity items for {len(hosts_data)} hosts")
        
        # Build maps for quick lookup
        template_map = {t["templateid"]: t for t in templates_data}
        items_by_host = self._group_items_by_host(items_data)
        items_by_template = self._group_items_by_template(items_data, templates_data)
        
        connectivity_items = []
        
        for host in hosts_data:
            host_id = host.get("hostid")
            host_templates = host.get("parentTemplates", [])
            
            # Get items for this host
            host_items = items_by_host.get(host_id, [])
            
            # Check each template linked to host
            for template_link in host_templates:
                template_id = template_link.get("templateid")
                template_name = template_link.get("name", "")
                
                # Get template configuration
                template_config = self.template_loader.get_template_by_name(template_name)
                if not template_config:
                    continue
                
                # Get connection check items from configuration
                for config_item in template_config.connection_check_items:
                    # Find matching item
                    matching_item = self._find_matching_item(
                        host_items,
                        items_by_template.get(template_id, []),
                        config_item
                    )
                    
                    if matching_item:
                        connectivity_item = ConnectivityItem(
                            matching_item,
                            config_item,
                            template_name
                        )
                        connectivity_items.append({
                            "itemid": connectivity_item.itemid,
                            "hostid": connectivity_item.hostid,
                            "hostname": host.get("host", ""),
                            "key": connectivity_item.key,
                            "name": connectivity_item.name,
                            "template": connectivity_item.template,
                            "type": connectivity_item.type,
                            "value_type": connectivity_item.value_type,
                            "status": connectivity_item.status,
                            "lastvalue": connectivity_item.lastvalue,
                            "lastclock": connectivity_item.lastclock,
                            "required": connectivity_item.required,
                            "priority": connectivity_item.priority,
                            "is_discovery": connectivity_item.is_discovery,
                            "discovery_rule_note": connectivity_item.discovery_rule_note
                        })
        
        logger.info(f"Detected {len(connectivity_items)} connectivity items")
        return connectivity_items
    
    def detect_master_items(
        self,
        hosts_data: List[Dict[str, Any]],
        items_data: List[Dict[str, Any]],
        templates_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect master items for all hosts
        
        Args:
            hosts_data: List of host dictionaries
            items_data: List of item dictionaries
            templates_data: List of template dictionaries
            
        Returns:
            List of master item dictionaries
        """
        logger.info(f"Detecting master items for {len(hosts_data)} hosts")
        
        # Build maps for quick lookup
        items_by_host = self._group_items_by_host(items_data)
        items_by_template = self._group_items_by_template(items_data, templates_data)
        
        master_items = []
        
        for host in hosts_data:
            host_id = host.get("hostid")
            host_templates = host.get("parentTemplates", [])
            
            # Get items for this host
            host_items = items_by_host.get(host_id, [])
            
            # Check each template linked to host
            for template_link in host_templates:
                template_name = template_link.get("name", "")
                
                # Get template configuration
                template_config = self.template_loader.get_template_by_name(template_name)
                if not template_config:
                    continue
                
                # Get master items from configuration
                for config_master in template_config.master_items:
                    if not config_master.key:  # Skip empty keys
                        continue
                    
                    # Find matching item
                    matching_item = self._find_matching_item(
                        host_items,
                        items_by_template.get(template_link.get("templateid"), []),
                        config_master,
                        is_master=True
                    )
                    
                    if matching_item:
                        master_items.append({
                            "itemid": matching_item.get("itemid"),
                            "hostid": matching_item.get("hostid"),
                            "hostname": host.get("host", ""),
                            "key": matching_item.get("key_", ""),
                            "name": matching_item.get("name", ""),
                            "template": template_name,
                            "type": matching_item.get("type", ""),
                            "value_type": matching_item.get("value_type", ""),
                            "status": matching_item.get("status", ""),
                            "lastvalue": matching_item.get("lastvalue", ""),
                            "lastclock": matching_item.get("lastclock", ""),
                            "required": config_master.required,
                            "priority": config_master.priority
                        })
        
        logger.info(f"Detected {len(master_items)} master items")
        return master_items
    
    def _group_items_by_host(self, items_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by host ID"""
        grouped = {}
        for item in items_data:
            host_id = item.get("hostid")
            if host_id not in grouped:
                grouped[host_id] = []
            grouped[host_id].append(item)
        return grouped
    
    def _group_items_by_template(self, items_data: List[Dict[str, Any]], templates_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by template ID"""
        grouped = {}
        template_ids = {t["templateid"] for t in templates_data}
        
        for item in items_data:
            template_id = item.get("templateid")
            if template_id and template_id in template_ids:
                if template_id not in grouped:
                    grouped[template_id] = []
                grouped[template_id].append(item)
        
        return grouped
    
    def _find_matching_item(
        self,
        host_items: List[Dict[str, Any]],
        template_items: List[Dict[str, Any]],
        config_item: Any,
        is_master: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Find item matching configuration
        
        Args:
            host_items: Items linked to host
            template_items: Items from template
            config_item: Configuration item (ConnectionCheckItem or MasterItem)
            is_master: Whether this is a master item
            
        Returns:
            Matching item dictionary or None
        """
        # Search in host items first, then template items
        search_items = host_items + template_items
        
        for item in search_items:
            item_key = item.get("key_", "").lower()
            item_name = item.get("name", "").lower()
            config_key = config_item.key.lower() if config_item.key else ""
            config_name = config_item.name.lower() if hasattr(config_item, 'name') and config_item.name else ""
            
            # Match by key (exact or pattern)
            if config_key:
                if item_key == config_key or fnmatch.fnmatch(item_key, config_key):
                    return item
            
            # Match by name pattern
            if config_name:
                if config_name in item_name or fnmatch.fnmatch(item_name, config_name):
                    return item
        
        return None
    
    def save_connectivity_items(self, connectivity_items: List[Dict[str, Any]], output_dir: str):
        """
        Save connectivity items to file
        
        Args:
            connectivity_items: List of connectivity item dictionaries
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "connectivity_items.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(connectivity_items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(connectivity_items)} connectivity items to {file_path}")
    
    def save_master_items(self, master_items: List[Dict[str, Any]], output_dir: str):
        """
        Save master items to file
        
        Args:
            master_items: List of master item dictionaries
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "master_items.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(master_items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(master_items)} master items to {file_path}")
