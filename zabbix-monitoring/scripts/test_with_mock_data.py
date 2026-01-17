#!/usr/bin/env python3
"""
Test Script with Mock Data
Tests the system using sample data without requiring Zabbix API access
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from config.template_loader import TemplateConfigLoader
from utils.logger import setup_logging, get_logger
from analyzers.template_analyzer import TemplateAnalyzer
from analyzers.connectivity_analyzer import ConnectivityAnalyzer
from analyzers.data_analyzer import DataAnalyzer

logger = get_logger(__name__)


def load_mock_data():
    """Load mock data from fixtures"""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    sample_data_file = fixtures_dir / "sample_data.json"
    
    if not sample_data_file.exists():
        logger.error(f"Mock data file not found: {sample_data_file}")
        return None
    
    with open(sample_data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_with_mock_data():
    """Test with mock data"""
    logger.info("Testing with mock data...")
    
    try:
        # Load mock data
        mock_data = load_mock_data()
        if not mock_data:
            return 1
        
        # Load template mapping
        template_mapping = Path(__file__).parent.parent / "mappings" / "templates.yml"
        loader = TemplateConfigLoader(str(template_mapping))
        
        # Test template analyzer
        logger.info("Testing template analyzer...")
        analyzer = TemplateAnalyzer(str(template_mapping))
        analysis_result = analyzer.analyze_templates(mock_data["templates"])
        logger.info(f"✅ Template analysis: {analysis_result['matched_templates']} templates matched")
        
        # Test connectivity analyzer
        logger.info("Testing connectivity analyzer...")
        connectivity_analyzer = ConnectivityAnalyzer(loader)
        connectivity_items = connectivity_analyzer.detect_connectivity_items(
            mock_data["hosts"],
            mock_data["items"],
            mock_data["templates"]
        )
        logger.info(f"✅ Connectivity detection: {len(connectivity_items)} items detected")
        
        # Test master items
        master_items = connectivity_analyzer.detect_master_items(
            mock_data["hosts"],
            mock_data["items"],
            mock_data["templates"]
        )
        logger.info(f"✅ Master items detection: {len(master_items)} items detected")
        
        # Test data analyzer
        logger.info("Testing data analyzer...")
        data_analyzer = DataAnalyzer(loader)
        analysis_result = data_analyzer.analyze_connectivity(
            connectivity_items,
            mock_data["history"]
        )
        summary = analysis_result.get("summary", {})
        logger.info(f"✅ Data analysis:")
        logger.info(f"   - Total hosts: {summary.get('total_hosts', 0)}")
        logger.info(f"   - Average score: {summary.get('average_connectivity_score', 0.0):.2f}")
        
        logger.info("✅ All tests with mock data passed!")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    setup_logging(
        level="INFO",
        log_file=None,
        format_type="text",
        console_output=True
    )
    sys.exit(test_with_mock_data())
