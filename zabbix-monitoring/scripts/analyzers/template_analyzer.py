"""
Template Analyzer
Analyzes templates and extracts template structure
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger
from ..config.template_loader import TemplateConfigLoader, TemplateConfig

logger = get_logger(__name__)


class TemplateAnalyzer:
    """Template analyzer"""
    
    def __init__(self, template_mapping_file: str):
        """
        Initialize template analyzer
        
        Args:
            template_mapping_file: Path to template mapping YAML file
        """
        self.template_loader = TemplateConfigLoader(template_mapping_file)
        logger.info(f"Template analyzer initialized with mapping file: {template_mapping_file}")
    
    def analyze_templates(self, templates_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze templates and match with configuration
        
        Args:
            templates_data: List of template dictionaries from Zabbix
            
        Returns:
            Analysis results dictionary
        """
        logger.info(f"Analyzing {len(templates_data)} templates")
        
        # Build template map by name
        template_map = {t["name"]: t for t in templates_data}
        
        # Match templates with configuration
        matched_templates = []
        unmatched_templates = []
        
        for template_data in templates_data:
            template_name = template_data.get("name", "")
            config = self.template_loader.get_template_by_name(template_name)
            
            if config:
                matched_templates.append({
                    "template": template_data,
                    "config": {
                        "name": config.name,
                        "connection_check_items_count": len(config.connection_check_items),
                        "master_items_count": len(config.master_items)
                    }
                })
            else:
                unmatched_templates.append(template_name)
        
        result = {
            "total_templates": len(templates_data),
            "matched_templates": len(matched_templates),
            "unmatched_templates": len(unmatched_templates),
            "matched_template_details": matched_templates,
            "unmatched_template_names": unmatched_templates
        }
        
        logger.info(f"Matched {len(matched_templates)} templates, {len(unmatched_templates)} unmatched")
        
        return result
    
    def get_template_for_host(
        self,
        host_data: Dict[str, Any],
        templates_data: List[Dict[str, Any]]
    ) -> List[TemplateConfig]:
        """
        Get template configurations for a host
        
        Args:
            host_data: Host data dictionary
            templates_data: List of template dictionaries from Zabbix
            
        Returns:
            List of matching TemplateConfig objects
        """
        # Get templates linked to host
        host_templates = host_data.get("parentTemplates", [])
        template_names = [t.get("name") for t in host_templates]
        
        # Find matching configurations
        matching_configs = []
        for template_name in template_names:
            config = self.template_loader.get_template_by_name(template_name)
            if config:
                matching_configs.append(config)
        
        return matching_configs
    
    def save_analysis(self, analysis_result: Dict[str, Any], output_dir: str):
        """
        Save analysis results to file
        
        Args:
            analysis_result: Analysis results dictionary
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "template_analysis.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved template analysis to {file_path}")
