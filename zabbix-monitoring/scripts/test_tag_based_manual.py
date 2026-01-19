#!/usr/bin/env python3
"""
Manual test script for tag-based connectivity detection
This script can be run without connecting to a real Zabbix server
"""

import json
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from analyzers.connectivity_analyzer import ConnectivityAnalyzer
from analyzers.data_analyzer import DataAnalyzer
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO", console_output=True)
logger = get_logger(__name__)


def create_mock_items():
    """Create mock items data for testing"""
    return [
        {
            "itemid": "1001",
            "key_": "icmpping",
            "name": "ICMP Ping",
            "value_type": "3",
            "status": "0",
            "hosts": [{"hostid": "100", "host": "server-a.example.com", "name": "Server A"}],
            "tags": [{"tag": "connection status", "value": ""}]
        },
        {
            "itemid": "1002",
            "key_": "agent.ping",
            "name": "Zabbix Agent Status",
            "value_type": "3",
            "status": "0",
            "hosts": [{"hostid": "100", "host": "server-a.example.com", "name": "Server A"}],
            "tags": [{"tag": "connection status", "value": ""}]
        },
        {
            "itemid": "2001",
            "key_": "snmp.available",
            "name": "SNMP Availability",
            "value_type": "3",
            "status": "0",
            "hosts": [{"hostid": "200", "host": "server-b.example.com", "name": "Server B"}],
            "tags": [{"tag": "connection status", "value": ""}]
        },
        {
            "itemid": "3001",
            "key_": "cpu.util",
            "name": "CPU Utilization",
            "value_type": "0",
            "status": "0",
            "hosts": [{"hostid": "300", "host": "server-c.example.com", "name": "Server C"}],
            "tags": [{"tag": "performance", "value": ""}]  # Different tag - should be excluded
        }
    ]


def create_mock_history():
    """Create mock history data for testing"""
    return {
        # Server A - ICMP Ping: 90% success (healthy)
        "1001": [
            {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
            for i in range(9)
        ] + [
            {"itemid": "1001", "value": "0", "clock": "991"}
        ],
        # Server A - Agent Status: 60% success (warning)
        "1002": [
            {"itemid": "1002", "value": "1", "clock": str(1000 - i)}
            for i in range(6)
        ] + [
            {"itemid": "1002", "value": "0", "clock": str(994 - i)}
            for i in range(4)
        ],
        # Server B - SNMP Availability: 30% success (critical)
        "2001": [
            {"itemid": "2001", "value": "1", "clock": str(1000 - i)}
            for i in range(3)
        ] + [
            {"itemid": "2001", "value": "0", "clock": str(997 - i)}
            for i in range(7)
        ]
    }


def main():
    """Run manual test"""
    logger.info("=" * 70)
    logger.info("Tag-Based Connectivity Detection - Manual Test")
    logger.info("=" * 70)
    
    # Step 1: Create mock data
    logger.info("\nStep 1: Creating mock data...")
    items_data = create_mock_items()
    history_data = create_mock_history()
    logger.info(f"Created {len(items_data)} mock items")
    logger.info(f"Created history for {len(history_data)} items")
    
    # Step 2: Detect connectivity items
    logger.info("\nStep 2: Detecting connectivity items by tags...")
    analyzer = ConnectivityAnalyzer(None)
    detection_result = analyzer.detect_connectivity_items_by_tags(
        items_data=items_data,
        connection_tag="connection status"
    )
    
    logger.info("\nDetection Results:")
    logger.info(f"  Total hosts: {detection_result['total_hosts']}")
    logger.info(f"  Hosts with connection items: {len(detection_result['hosts_with_items'])}")
    logger.info(f"  Hosts without connection items: {len(detection_result['hosts_without_items'])}")
    logger.info(f"  Total connection items: {detection_result['total_connection_items']}")
    
    # Step 3: Analyze connectivity
    logger.info("\nStep 3: Analyzing connectivity...")
    data_analyzer = DataAnalyzer(None)
    analysis_result = data_analyzer.analyze_tag_based_connectivity(
        detection_result=detection_result,
        history_data=history_data,
        threshold_percentage=70.0
    )
    
    # Step 4: Display results
    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS RESULTS")
    logger.info("=" * 70)
    
    summary = analysis_result["summary"]
    logger.info("\nSummary:")
    logger.info(f"  Total hosts analyzed: {summary['total_hosts_analyzed']}")
    logger.info(f"  Hosts with issues: {summary['hosts_with_issues']}")
    logger.info(f"  Hosts without issues: {summary['hosts_without_issues']}")
    logger.info(f"  Hosts without connection items: {summary['hosts_without_connection_items']}")
    logger.info(f"  Total items analyzed: {summary['total_items_analyzed']}")
    logger.info(f"  Items below threshold: {summary['items_below_threshold']}")
    logger.info(f"  Threshold: {summary['threshold_percentage']}%")
    
    # Display problematic items
    logger.info("\n" + "=" * 70)
    logger.info("PROBLEMATIC ITEMS (Below 70% Threshold)")
    logger.info("=" * 70)
    
    if analysis_result["problematic_items"]:
        logger.info(f"\n{'Host':<25} {'Item':<25} {'Score':<8} {'Status':<10}")
        logger.info("-" * 70)
        for item in analysis_result["problematic_items"]:
            logger.info(
                f"{item['host_name']:<25} "
                f"{item['item_name']:<25} "
                f"{item['percentage']:<8.2f} "
                f"{item['status']:<10}"
            )
    else:
        logger.info("\n✅ No problematic items found! All items are above threshold.")
    
    # Display hosts without connection items
    logger.info("\n" + "=" * 70)
    logger.info("HOSTS WITHOUT CONNECTION ITEMS")
    logger.info("=" * 70)
    
    if analysis_result["hosts_without_connection_items"]:
        logger.info(f"\n{'Host ID':<15} {'Hostname':<30} {'Display Name':<25}")
        logger.info("-" * 70)
        for host in analysis_result["hosts_without_connection_items"]:
            logger.info(
                f"{host['hostid']:<15} "
                f"{host['hostname']:<30} "
                f"{host.get('host_name', host['hostname']):<25}"
            )
    else:
        logger.info("\n✅ All hosts have connection items!")
    
    # Display detailed per-host analysis
    logger.info("\n" + "=" * 70)
    logger.info("DETAILED PER-HOST ANALYSIS")
    logger.info("=" * 70)
    
    for host in analysis_result["hosts"]:
        logger.info(f"\n📍 Host: {host['host_name']} ({host['hostname']})")
        logger.info(f"   Status: {'⚠️  HAS ISSUES' if host['has_issues'] else '✅ HEALTHY'}")
        logger.info(f"   Total items: {host['total_items']}")
        logger.info(f"   Items below threshold: {host['items_below_threshold']}")
        
        logger.info(f"\n   {'Item':<30} {'Score':<10} {'Status':<12} {'Success/Total':<15}")
        logger.info("   " + "-" * 70)
        
        for item in host["items"]:
            status_icon = "🔴" if item["status"] == "critical" else "🟡" if item["status"] == "warning" else "🟢"
            logger.info(
                f"   {item['name']:<30} "
                f"{item['percentage']:<10.2f} "
                f"{status_icon} {item['status']:<10} "
                f"{item['successful_count']}/{item['total_count']:<15}"
            )
    
    # Save results to file
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "manual_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n\n✅ Test completed successfully!")
    logger.info(f"📄 Results saved to: {output_file}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
