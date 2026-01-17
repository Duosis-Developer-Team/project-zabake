#!/usr/bin/env python3
"""
Manual Test Script for Zabbix Monitoring Integration
This script allows testing individual components manually
"""

import argparse
import sys
import json
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from config.settings import get_settings
from config.template_loader import TemplateConfigLoader
from utils.logger import setup_logging, get_logger
from collectors.api_collector import ZabbixAPICollector
from analyzers.template_analyzer import TemplateAnalyzer
from analyzers.connectivity_analyzer import ConnectivityAnalyzer
from analyzers.data_analyzer import DataAnalyzer

logger = get_logger(__name__)


def test_api_connection(args):
    """Test Zabbix API connection"""
    logger.info("Testing Zabbix API connection...")
    
    try:
        collector = ZabbixAPICollector(
            url=args.zabbix_url,
            user=args.zabbix_user,
            password=args.zabbix_password,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl
        )
        
        # Test with a simple API call
        hosts = collector.get_hosts(filter_status="enabled", limit=5)
        logger.info(f"✅ API connection successful! Found {len(hosts)} hosts")
        
        if hosts:
            logger.info("Sample host:")
            logger.info(f"  - Name: {hosts[0].get('name', 'N/A')}")
            logger.info(f"  - Host: {hosts[0].get('host', 'N/A')}")
            logger.info(f"  - Status: {hosts[0].get('status', 'N/A')}")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ API connection failed: {str(e)}")
        return 1


def test_template_loader(args):
    """Test template loader"""
    logger.info("Testing template loader...")
    
    try:
        loader = TemplateConfigLoader(args.template_mapping)
        
        templates = loader.templates
        logger.info(f"✅ Template loader successful! Loaded {len(templates)} templates")
        
        for template in templates[:3]:  # Show first 3
            logger.info(f"  - {template.name}")
            logger.info(f"    Connection items: {len(template.connection_check_items)}")
            logger.info(f"    Master items: {len(template.master_items)}")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Template loader failed: {str(e)}")
        return 1


def test_data_collection(args):
    """Test data collection"""
    logger.info("Testing data collection...")
    
    try:
        collector = ZabbixAPICollector(
            url=args.zabbix_url,
            user=args.zabbix_user,
            password=args.zabbix_password,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl
        )
        
        # Collect limited data for testing
        logger.info("Collecting hosts (limit: 10)...")
        hosts = collector.get_hosts(filter_status="enabled")
        hosts = hosts[:10]  # Limit for testing
        
        logger.info("Collecting templates...")
        templates = collector.get_templates()
        
        logger.info("Collecting items...")
        host_ids = [h["hostid"] for h in hosts]
        items = collector.get_host_items(host_ids)
        
        logger.info(f"✅ Data collection successful!")
        logger.info(f"  - Hosts: {len(hosts)}")
        logger.info(f"  - Templates: {len(templates)}")
        logger.info(f"  - Items: {len(items)}")
        
        # Save to debug output
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        collector.save_collected_data(
            output_dir=str(output_dir),
            hosts=hosts,
            templates=templates,
            items=items,
            history={}
        )
        
        logger.info(f"✅ Data saved to {output_dir}")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Data collection failed: {str(e)}")
        return 1


def test_connectivity_detection(args):
    """Test connectivity item detection"""
    logger.info("Testing connectivity detection...")
    
    try:
        # Load template mapping
        loader = TemplateConfigLoader(args.template_mapping)
        
        # Load collected data
        input_dir = Path(args.input_dir)
        with open(input_dir / "hosts.json", 'r') as f:
            hosts_data = json.load(f)
        with open(input_dir / "items.json", 'r') as f:
            items_data = json.load(f)
        with open(input_dir / "templates.json", 'r') as f:
            templates_data = json.load(f)
        
        # Detect connectivity items
        analyzer = ConnectivityAnalyzer(loader)
        connectivity_items = analyzer.detect_connectivity_items(hosts_data, items_data, templates_data)
        master_items = analyzer.detect_master_items(hosts_data, items_data, templates_data)
        
        logger.info(f"✅ Connectivity detection successful!")
        logger.info(f"  - Connectivity items: {len(connectivity_items)}")
        logger.info(f"  - Master items: {len(master_items)}")
        
        if connectivity_items:
            logger.info("Sample connectivity items:")
            for item in connectivity_items[:3]:
                logger.info(f"  - {item.get('key')} ({item.get('hostname')})")
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        analyzer.save_connectivity_items(connectivity_items, str(output_dir))
        analyzer.save_master_items(master_items, str(output_dir))
        
        logger.info(f"✅ Results saved to {output_dir}")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Connectivity detection failed: {str(e)}")
        return 1


def test_data_analysis(args):
    """Test data analysis"""
    logger.info("Testing data analysis...")
    
    try:
        # Load template mapping
        loader = TemplateConfigLoader(args.template_mapping)
        
        # Load connectivity items
        input_dir = Path(args.input_dir)
        with open(input_dir / "connectivity_items.json", 'r') as f:
            connectivity_items = json.load(f)
        
        # Load history
        history_data = {}
        history_file = input_dir / "history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                history_data = json.load(f)
        
        # Analyze
        analyzer = DataAnalyzer(loader)
        analysis_result = analyzer.analyze_connectivity(connectivity_items, history_data)
        
        logger.info(f"✅ Data analysis successful!")
        summary = analysis_result.get("summary", {})
        logger.info(f"  - Total hosts: {summary.get('total_hosts', 0)}")
        logger.info(f"  - Hosts with connectivity: {summary.get('hosts_with_connectivity', 0)}")
        logger.info(f"  - Hosts without connectivity: {summary.get('hosts_without_connectivity', 0)}")
        logger.info(f"  - Average score: {summary.get('average_connectivity_score', 0.0):.2f}")
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        analyzer.save_analysis(analysis_result, str(output_dir))
        
        logger.info(f"✅ Analysis results saved to {output_dir}")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Data analysis failed: {str(e)}")
        return 1


def test_full_workflow(args):
    """Test full workflow end-to-end"""
    logger.info("Testing full workflow...")
    
    try:
        # Step 1: Collect data
        logger.info("Step 1: Collecting data...")
        result = test_data_collection(args)
        if result != 0:
            return result
        
        # Step 2: Detect connectivity
        logger.info("Step 2: Detecting connectivity items...")
        result = test_connectivity_detection(args)
        if result != 0:
            return result
        
        # Step 3: Analyze data
        logger.info("Step 3: Analyzing data...")
        result = test_data_analysis(args)
        if result != 0:
            return result
        
        logger.info("✅ Full workflow test successful!")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Full workflow test failed: {str(e)}")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Manual Test Script for Zabbix Monitoring")
    parser.add_argument("--test", required=True, choices=[
        "api-connection", "template-loader", "data-collection",
        "connectivity-detection", "data-analysis", "full-workflow"
    ], help="Test to run")
    parser.add_argument("--zabbix-url", help="Zabbix API URL")
    parser.add_argument("--zabbix-user", help="Zabbix username")
    parser.add_argument("--zabbix-password", help="Zabbix password")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout")
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    parser.add_argument("--template-mapping", default="../mappings/templates.yml",
                       help="Template mapping YAML file")
    parser.add_argument("--input-dir", default="./debug_output",
                       help="Input directory for data files")
    parser.add_argument("--output-dir", default="./debug_output",
                       help="Output directory for results")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        level=args.log_level.upper(),
        log_file=None,
        format_type="text",
        console_output=True
    )
    
    # Run test
    if args.test == "api-connection":
        return test_api_connection(args)
    elif args.test == "template-loader":
        return test_template_loader(args)
    elif args.test == "data-collection":
        return test_data_collection(args)
    elif args.test == "connectivity-detection":
        return test_connectivity_detection(args)
    elif args.test == "data-analysis":
        return test_data_analysis(args)
    elif args.test == "full-workflow":
        return test_full_workflow(args)
    else:
        logger.error(f"Unknown test: {args.test}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
