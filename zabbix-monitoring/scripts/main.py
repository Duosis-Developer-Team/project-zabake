#!/usr/bin/env python3
"""
Zabbix Monitoring Integration - Main Script
Entry point for data collection, analysis, and report generation
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add scripts directory to path so that config, utils, collectors, analyzers can be imported
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


def collect_data(args):
    """Collect data from Zabbix"""
    logger.info("Starting data collection")

    # Let CLI args override: set env so get_settings() picks them up (AWX/playbook passes --zabbix-url etc)
    if getattr(args, "zabbix_url", None):
        os.environ["ZABBIX_URL"] = str(args.zabbix_url)
    if getattr(args, "zabbix_user", None):
        os.environ["ZABBIX_USER"] = str(args.zabbix_user)
    if getattr(args, "zabbix_password", None):
        os.environ["ZABBIX_PASSWORD"] = str(args.zabbix_password)

    try:
        settings = get_settings()

        if args.data_source == "api":
            collector = ZabbixAPICollector(
                url=settings.get_zabbix_url(),
                user=settings.get_zabbix_credentials()[0],
                password=settings.get_zabbix_credentials()[1],
                timeout=settings.zabbix.get("timeout", 30),
                verify_ssl=settings.zabbix.get("verify_ssl", True)
            )
            
            # Collect hosts
            hosts = collector.get_hosts(
                filter_status="enabled",
                host_groups=args.host_groups.split(",") if args.host_groups else None
            )
            
            # Collect templates
            templates = collector.get_templates()
            
            # Collect items
            host_ids = [h["hostid"] for h in hosts]
            items = collector.get_host_items(host_ids)
            
            # Collect history for connectivity items
            item_ids = [i["itemid"] for i in items]
            history = collector.get_item_history(item_ids, limit=1)
            
            # Save collected data
            collector.save_collected_data(
                output_dir=args.output_dir,
                hosts=hosts,
                templates=templates,
                items=items,
                history=history
            )
            
            logger.info("Data collection completed successfully")
            return 0
        
        elif args.data_source == "database":
            # TODO: Implement database collector
            logger.error("Database collector not yet implemented")
            return 1
        
        else:
            logger.error(f"Unknown data source: {args.data_source}")
            return 1
    
    except Exception as e:
        logger.error(f"Data collection failed: {str(e)}", exc_info=True)
        return 1


def analyze_templates(args):
    """Analyze templates"""
    logger.info("Starting template analysis")
    
    try:
        # Load template mapping
        template_loader = TemplateConfigLoader(args.template_mapping)
        
        # Load collected templates
        templates_file = Path(args.input_dir) / "templates.json"
        if not templates_file.exists():
            logger.error(f"Templates file not found: {templates_file}")
            return 1
        
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
        
        # Analyze templates
        analyzer = TemplateAnalyzer(args.template_mapping)
        analysis_result = analyzer.analyze_templates(templates_data)
        
        # Save analysis
        analyzer.save_analysis(analysis_result, args.output_dir)
        
        logger.info("Template analysis completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Template analysis failed: {str(e)}", exc_info=True)
        return 1


def detect_connectivity(args):
    """Detect connectivity items"""
    logger.info("Starting connectivity detection")
    
    try:
        # Load template mapping
        template_loader = TemplateConfigLoader(args.template_mapping)
        
        # Load collected data
        hosts_file = Path(args.input_dir) / "hosts.json"
        items_file = Path(args.input_dir) / "items.json"
        templates_file = Path(args.input_dir) / "templates.json"
        
        if not all(f.exists() for f in [hosts_file, items_file, templates_file]):
            logger.error("Required data files not found")
            return 1
        
        with open(hosts_file, 'r', encoding='utf-8') as f:
            hosts_data = json.load(f)
        with open(items_file, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
        
        # Detect connectivity items
        analyzer = ConnectivityAnalyzer(template_loader)
        connectivity_items = analyzer.detect_connectivity_items(hosts_data, items_data, templates_data)
        master_items = analyzer.detect_master_items(hosts_data, items_data, templates_data)
        
        # Save results
        analyzer.save_connectivity_items(connectivity_items, args.output_dir)
        analyzer.save_master_items(master_items, args.output_dir)
        
        logger.info("Connectivity detection completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Connectivity detection failed: {str(e)}", exc_info=True)
        return 1


def analyze_data(args):
    """Analyze connectivity data"""
    logger.info("Starting data analysis")
    
    try:
        # Load template mapping
        template_loader = TemplateConfigLoader(args.template_mapping)
        
        # Update thresholds if provided
        if args.max_data_age:
            template_loader.thresholds["max_data_age"] = args.max_data_age
        if args.inactive_threshold:
            template_loader.thresholds["inactive_threshold"] = args.inactive_threshold
        if args.min_connectivity_score:
            template_loader.thresholds["min_connectivity_score"] = args.min_connectivity_score
        
        # Load connectivity items
        connectivity_file = Path(args.input_dir) / "connectivity_items.json"
        if not connectivity_file.exists():
            logger.error(f"Connectivity items file not found: {connectivity_file}")
            return 1
        
        with open(connectivity_file, 'r', encoding='utf-8') as f:
            connectivity_items = json.load(f)
        
        # Load history data
        history_file = Path(args.input_dir) / "history.json"
        history_data = {}
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        
        # Analyze connectivity
        analyzer = DataAnalyzer(template_loader)
        analysis_result = analyzer.analyze_connectivity(connectivity_items, history_data)
        
        # Save analysis
        analyzer.save_analysis(analysis_result, args.output_dir)
        
        logger.info("Data analysis completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Data analysis failed: {str(e)}", exc_info=True)
        return 1


def check_master_items(args):
    """Check master items"""
    logger.info("Starting master items check")
    
    try:
        # Load template mapping
        template_loader = TemplateConfigLoader(args.template_mapping)
        
        # Update threshold if provided
        if args.master_item_threshold:
            template_loader.thresholds["master_item_threshold"] = args.master_item_threshold
        
        # Load master items
        master_items_file = Path(args.input_dir) / "master_items.json"
        if not master_items_file.exists():
            logger.warning("Master items file not found, skipping check")
            return 0
        
        with open(master_items_file, 'r', encoding='utf-8') as f:
            master_items = json.load(f)
        
        # Load history data
        history_file = Path(args.input_dir) / "history.json"
        history_data = {}
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        
        # Analyze master items
        analyzer = DataAnalyzer(template_loader)
        master_analysis = analyzer.analyze_master_items(master_items, history_data)
        
        # Save analysis
        analyzer.save_master_items_analysis(master_analysis, args.output_dir)
        
        logger.info("Master items check completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Master items check failed: {str(e)}", exc_info=True)
        return 1


def tag_based_connectivity_check(args):
    """Tag-based connectivity check (new approach)"""
    logger.info("Starting tag-based connectivity check")
    
    try:
        # Let CLI args override
        if getattr(args, "zabbix_url", None):
            os.environ["ZABBIX_URL"] = str(args.zabbix_url)
        if getattr(args, "zabbix_user", None):
            os.environ["ZABBIX_USER"] = str(args.zabbix_user)
        if getattr(args, "zabbix_password", None):
            os.environ["ZABBIX_PASSWORD"] = str(args.zabbix_password)
        
        settings = get_settings()
        
        # Initialize collector
        collector = ZabbixAPICollector(
            url=settings.get_zabbix_url(),
            user=settings.get_zabbix_credentials()[0],
            password=settings.get_zabbix_credentials()[1],
            timeout=settings.zabbix.get("timeout", 30),
            verify_ssl=settings.zabbix.get("verify_ssl", True)
        )
        
        # Step 1: Get hosts
        logger.info("Step 1: Collecting hosts")
        hosts = collector.get_hosts(
            filter_status="enabled",
            host_groups=args.host_groups.split(",") if args.host_groups else None
        )
        host_ids = [h["hostid"] for h in hosts]
        logger.info(f"Collected {len(hosts)} hosts")
        
        # Step 2: Get items by connection status tag
        logger.info("Step 2: Collecting items by 'connection status' tag")
        connection_tag = args.connection_tag if hasattr(args, 'connection_tag') else "connection status"
        items_with_tag = collector.get_items_by_tags(
            tags=[{"tag": connection_tag, "operator": "like"}],
            host_ids=host_ids,
            monitored_only=True
        )
        logger.info(f"Collected {len(items_with_tag)} items with '{connection_tag}' tag")
        
        # Step 3: Detect connectivity items by tag
        logger.info("Step 3: Detecting connectivity items by tag")
        from analyzers.connectivity_analyzer import ConnectivityAnalyzer
        from config.template_loader import TemplateConfigLoader
        
        template_loader = TemplateConfigLoader(args.template_mapping) if args.template_mapping else None
        analyzer = ConnectivityAnalyzer(template_loader)
        
        detection_result = analyzer.detect_connectivity_items_by_tags(
            items_data=items_with_tag,
            connection_tag=connection_tag
        )
        
        # Save detection result
        analyzer.save_tag_based_connectivity_items(detection_result, args.output_dir)
        
        # Step 4: Collect history for connection items
        logger.info("Step 4: Collecting history for connection items")
        all_connection_items = []
        for host_data in detection_result.get("hosts_with_items", []):
            all_connection_items.extend(host_data.get("items", []))
        
        history_limit = args.history_limit if hasattr(args, 'history_limit') else 10
        history_data = collector.get_item_history_by_value_types(
            items_with_types=all_connection_items,
            limit=history_limit
        )
        logger.info(f"Collected history for {len(history_data)} items")
        
        # Save history
        collector.save_collected_data(
            output_dir=args.output_dir,
            history=history_data
        )
        
        # Step 5: Analyze connectivity with per-item scoring
        logger.info("Step 5: Analyzing connectivity with per-item scoring")
        from analyzers.data_analyzer import DataAnalyzer
        
        data_analyzer = DataAnalyzer(template_loader) if template_loader else DataAnalyzer(None)
        threshold = args.threshold_percentage if hasattr(args, 'threshold_percentage') else 70.0
        
        analysis_result = data_analyzer.analyze_tag_based_connectivity(
            detection_result=detection_result,
            history_data=history_data,
            threshold_percentage=threshold
        )
        
        # Save analysis
        data_analyzer.save_tag_based_analysis(analysis_result, args.output_dir)
        
        # Step 6: Print summary
        logger.info("=" * 60)
        logger.info("CONNECTIVITY ANALYSIS SUMMARY")
        logger.info("=" * 60)
        summary = analysis_result.get("summary", {})
        logger.info(f"Total hosts analyzed: {summary.get('total_hosts_analyzed', 0)}")
        logger.info(f"Hosts with issues: {summary.get('hosts_with_issues', 0)}")
        logger.info(f"Hosts without connection items: {summary.get('hosts_without_connection_items', 0)}")
        logger.info(f"Total items analyzed: {summary.get('total_items_analyzed', 0)}")
        logger.info(f"Items below {threshold}% threshold: {summary.get('items_below_threshold', 0)}")
        logger.info("=" * 60)
        
        logger.info("Tag-based connectivity check completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Tag-based connectivity check failed: {str(e)}", exc_info=True)
        return 1


def generate_report(args):
    """Generate final report"""
    logger.info("Starting report generation")
    
    try:
        # TODO: Implement report generator
        logger.info("Report generation not yet implemented")
        return 0
    
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Zabbix Monitoring Integration")
    parser.add_argument("--mode", required=True, choices=[
        "collect", "analyze-templates", "detect-connectivity",
        "analyze-data", "check-master-items", "generate-report",
        "tag-based-connectivity"
    ], help="Operation mode")
    parser.add_argument("--data-source", default="api", choices=["api", "database"],
                       help="Data source (api or database)")
    parser.add_argument("--zabbix-url", help="Zabbix API URL")
    parser.add_argument("--zabbix-user", help="Zabbix username")
    parser.add_argument("--zabbix-password", help="Zabbix password")
    parser.add_argument("--db-host", help="Database host")
    parser.add_argument("--db-port", type=int, help="Database port")
    parser.add_argument("--db-name", help="Database name")
    parser.add_argument("--db-user", help="Database user")
    parser.add_argument("--db-password", help="Database password")
    parser.add_argument("--template-mapping", help="Template mapping YAML file")
    parser.add_argument("--input-dir", default="./debug_output",
                       help="Input directory for data files")
    parser.add_argument("--output-dir", default="./reports",
                       help="Output directory for results")
    parser.add_argument("--host-groups", help="Comma-separated host group names")
    parser.add_argument("--max-data-age", type=int, help="Maximum data age in seconds")
    parser.add_argument("--inactive-threshold", type=int, help="Inactive threshold in seconds")
    parser.add_argument("--min-connectivity-score", type=float, help="Minimum connectivity score")
    parser.add_argument("--master-item-threshold", type=int, help="Master item threshold in seconds")
    parser.add_argument("--connection-tag", default="connection status", help="Tag name for connection items")
    parser.add_argument("--history-limit", type=int, default=10, help="Number of history records to analyze per item")
    parser.add_argument("--threshold-percentage", type=float, default=70.0, help="Minimum acceptable connectivity percentage")
    parser.add_argument("--output-formats", help="Comma-separated output formats")
    parser.add_argument("--filename-pattern", help="Output filename pattern")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = args.log_level.upper()
    log_file = args.log_file
    setup_logging(
        level=log_level,
        log_file=log_file,
        format_type="json",
        console_output=True
    )
    
    # Execute based on mode
    if args.mode == "collect":
        return collect_data(args)
    elif args.mode == "analyze-templates":
        return analyze_templates(args)
    elif args.mode == "detect-connectivity":
        return detect_connectivity(args)
    elif args.mode == "analyze-data":
        return analyze_data(args)
    elif args.mode == "check-master-items":
        return check_master_items(args)
    elif args.mode == "generate-report":
        return generate_report(args)
    elif args.mode == "tag-based-connectivity":
        return tag_based_connectivity_check(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
