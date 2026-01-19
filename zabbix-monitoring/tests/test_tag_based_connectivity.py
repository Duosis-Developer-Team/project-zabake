"""
Unit tests for tag-based connectivity detection and analysis
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from analyzers.connectivity_analyzer import ConnectivityAnalyzer
from analyzers.data_analyzer import DataAnalyzer


class TestConnectivityAnalyzer:
    """Test ConnectivityAnalyzer tag-based detection"""
    
    def test_detect_items_by_tags_single_host(self):
        """Test detecting items by tags for a single host"""
        analyzer = ConnectivityAnalyzer(None)
        
        items_data = [
            {
                "itemid": "1001",
                "key_": "icmpping",
                "name": "ICMP Ping",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "connection status", "value": ""}]
            },
            {
                "itemid": "1002",
                "key_": "agent.ping",
                "name": "Agent Status",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "connection status", "value": ""}]
            }
        ]
        
        result = analyzer.detect_connectivity_items_by_tags(items_data)
        
        assert result["total_hosts"] == 1
        assert result["total_connection_items"] == 2
        assert len(result["hosts_with_items"]) == 1
        assert len(result["hosts_without_items"]) == 0
        assert result["hosts_with_items"][0]["hostid"] == "100"
        assert len(result["hosts_with_items"][0]["items"]) == 2
    
    def test_detect_items_by_tags_multiple_hosts(self):
        """Test detecting items by tags for multiple hosts"""
        analyzer = ConnectivityAnalyzer(None)
        
        items_data = [
            {
                "itemid": "1001",
                "key_": "icmpping",
                "name": "ICMP Ping",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "connection status", "value": ""}]
            },
            {
                "itemid": "2001",
                "key_": "snmp.available",
                "name": "SNMP Status",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "200", "host": "host2", "name": "Host 2"}],
                "tags": [{"tag": "connection status", "value": ""}]
            },
            {
                "itemid": "3001",
                "key_": "some.metric",
                "name": "Some Metric",
                "value_type": "0",
                "status": "0",
                "hosts": [{"hostid": "300", "host": "host3", "name": "Host 3"}],
                "tags": [{"tag": "performance", "value": ""}]  # Different tag
            }
        ]
        
        result = analyzer.detect_connectivity_items_by_tags(items_data)
        
        assert result["total_hosts"] == 3
        assert result["total_connection_items"] == 2
        assert len(result["hosts_with_items"]) == 2
        assert len(result["hosts_without_items"]) == 1
        assert result["hosts_without_items"][0]["hostid"] == "300"
    
    def test_detect_items_case_insensitive_tag(self):
        """Test case-insensitive tag matching"""
        analyzer = ConnectivityAnalyzer(None)
        
        items_data = [
            {
                "itemid": "1001",
                "key_": "icmpping",
                "name": "ICMP Ping",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "Connection Status", "value": ""}]  # Mixed case
            }
        ]
        
        result = analyzer.detect_connectivity_items_by_tags(items_data, connection_tag="connection status")
        
        assert result["total_connection_items"] == 1
    
    def test_detect_items_no_connection_items(self):
        """Test when no items have connection status tag"""
        analyzer = ConnectivityAnalyzer(None)
        
        items_data = [
            {
                "itemid": "1001",
                "key_": "cpu.util",
                "name": "CPU Utilization",
                "value_type": "0",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "performance", "value": ""}]
            }
        ]
        
        result = analyzer.detect_connectivity_items_by_tags(items_data)
        
        assert result["total_connection_items"] == 0
        assert len(result["hosts_with_items"]) == 0
        assert len(result["hosts_without_items"]) == 1


class TestDataAnalyzer:
    """Test DataAnalyzer scoring and analysis"""
    
    def test_calculate_score_all_successful(self):
        """Test score calculation with all successful checks"""
        analyzer = DataAnalyzer(None)
        
        history = [
            {"itemid": "1001", "value": "1", "clock": "1000"},
            {"itemid": "1001", "value": "1", "clock": "999"},
            {"itemid": "1001", "value": "1", "clock": "998"},
            {"itemid": "1001", "value": "1", "clock": "997"},
            {"itemid": "1001", "value": "1", "clock": "996"},
            {"itemid": "1001", "value": "1", "clock": "995"},
            {"itemid": "1001", "value": "1", "clock": "994"},
            {"itemid": "1001", "value": "1", "clock": "993"},
            {"itemid": "1001", "value": "1", "clock": "992"},
            {"itemid": "1001", "value": "1", "clock": "991"}
        ]
        
        result = analyzer.calculate_connectivity_score(history, expected_value=1)
        
        assert result["percentage"] == 100.0
        assert result["score"] == 1.0
        assert result["successful_count"] == 10
        assert result["total_count"] == 10
        assert result["status"] == "healthy"
    
    def test_calculate_score_partial_success(self):
        """Test score calculation with partial success"""
        analyzer = DataAnalyzer(None)
        
        history = [
            {"itemid": "1001", "value": "1", "clock": "1000"},
            {"itemid": "1001", "value": "0", "clock": "999"},
            {"itemid": "1001", "value": "1", "clock": "998"},
            {"itemid": "1001", "value": "1", "clock": "997"},
            {"itemid": "1001", "value": "0", "clock": "996"},
            {"itemid": "1001", "value": "1", "clock": "995"},
            {"itemid": "1001", "value": "1", "clock": "994"},
            {"itemid": "1001", "value": "1", "clock": "993"},
            {"itemid": "1001", "value": "1", "clock": "992"},
            {"itemid": "1001", "value": "1", "clock": "991"}
        ]
        
        result = analyzer.calculate_connectivity_score(history, expected_value=1)
        
        assert result["percentage"] == 80.0
        assert result["score"] == 0.8
        assert result["successful_count"] == 8
        assert result["total_count"] == 10
        assert result["status"] == "healthy"
    
    def test_calculate_score_warning_threshold(self):
        """Test score at warning threshold"""
        analyzer = DataAnalyzer(None)
        
        history = [
            {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
            for i in range(6)
        ] + [
            {"itemid": "1001", "value": "0", "clock": str(994 - i)}
            for i in range(4)
        ]
        
        result = analyzer.calculate_connectivity_score(history, expected_value=1)
        
        assert result["percentage"] == 60.0
        assert result["successful_count"] == 6
        assert result["status"] == "warning"
    
    def test_calculate_score_critical_threshold(self):
        """Test score at critical threshold"""
        analyzer = DataAnalyzer(None)
        
        history = [
            {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
            for i in range(3)
        ] + [
            {"itemid": "1001", "value": "0", "clock": str(997 - i)}
            for i in range(7)
        ]
        
        result = analyzer.calculate_connectivity_score(history, expected_value=1)
        
        assert result["percentage"] == 30.0
        assert result["successful_count"] == 3
        assert result["status"] == "critical"
    
    def test_calculate_score_no_data(self):
        """Test score calculation with no data"""
        analyzer = DataAnalyzer(None)
        
        result = analyzer.calculate_connectivity_score([], expected_value=1)
        
        assert result["percentage"] == 0.0
        assert result["score"] == 0.0
        assert result["successful_count"] == 0
        assert result["total_count"] == 0
        assert result["status"] == "no_data"
    
    def test_analyze_tag_based_connectivity(self):
        """Test full tag-based connectivity analysis"""
        analyzer = DataAnalyzer(None)
        
        detection_result = {
            "hosts_with_items": [
                {
                    "hostid": "100",
                    "hostname": "host1",
                    "host_name": "Host 1",
                    "items": [
                        {"itemid": "1001", "key": "icmpping", "name": "ICMP Ping"},
                        {"itemid": "1002", "key": "agent.ping", "name": "Agent Status"}
                    ]
                }
            ],
            "hosts_without_items": []
        }
        
        history_data = {
            "1001": [
                {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
                for i in range(10)
            ],  # 100% success
            "1002": [
                {"itemid": "1002", "value": "1", "clock": str(1000 - i)}
                for i in range(5)
            ] + [
                {"itemid": "1002", "value": "0", "clock": str(995 - i)}
                for i in range(5)
            ]  # 50% success
        }
        
        result = analyzer.analyze_tag_based_connectivity(
            detection_result=detection_result,
            history_data=history_data,
            threshold_percentage=70.0
        )
        
        assert result["summary"]["total_hosts_analyzed"] == 1
        assert result["summary"]["hosts_with_issues"] == 1
        assert result["summary"]["items_below_threshold"] == 1
        assert result["summary"]["total_items_analyzed"] == 2
        
        # Check problematic items
        assert len(result["problematic_items"]) == 1
        assert result["problematic_items"][0]["itemid"] == "1002"
        assert result["problematic_items"][0]["percentage"] == 50.0
    
    def test_analyze_with_hosts_without_items(self):
        """Test analysis with hosts that have no connection items"""
        analyzer = DataAnalyzer(None)
        
        detection_result = {
            "hosts_with_items": [
                {
                    "hostid": "100",
                    "hostname": "host1",
                    "host_name": "Host 1",
                    "items": [
                        {"itemid": "1001", "key": "icmpping", "name": "ICMP Ping"}
                    ]
                }
            ],
            "hosts_without_items": [
                {"hostid": "200", "hostname": "host2", "host_name": "Host 2"},
                {"hostid": "300", "hostname": "host3", "host_name": "Host 3"}
            ]
        }
        
        history_data = {
            "1001": [
                {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
                for i in range(10)
            ]
        }
        
        result = analyzer.analyze_tag_based_connectivity(
            detection_result=detection_result,
            history_data=history_data,
            threshold_percentage=70.0
        )
        
        assert result["summary"]["hosts_without_connection_items"] == 2
        assert len(result["hosts_without_connection_items"]) == 2
        assert result["hosts_without_connection_items"][0]["hostid"] == "200"
        assert result["hosts_without_connection_items"][1]["hostid"] == "300"


class TestIntegration:
    """Integration tests for the full workflow"""
    
    def test_full_workflow(self):
        """Test complete workflow from detection to analysis"""
        # Step 1: Detect items by tags
        connectivity_analyzer = ConnectivityAnalyzer(None)
        
        items_data = [
            {
                "itemid": "1001",
                "key_": "icmpping",
                "name": "ICMP Ping",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "100", "host": "host1", "name": "Host 1"}],
                "tags": [{"tag": "connection status", "value": ""}]
            },
            {
                "itemid": "2001",
                "key_": "snmp.available",
                "name": "SNMP Status",
                "value_type": "3",
                "status": "0",
                "hosts": [{"hostid": "200", "host": "host2", "name": "Host 2"}],
                "tags": [{"tag": "connection status", "value": ""}]
            },
            {
                "itemid": "3001",
                "key_": "cpu.util",
                "name": "CPU Utilization",
                "value_type": "0",
                "status": "0",
                "hosts": [{"hostid": "300", "host": "host3", "name": "Host 3"}],
                "tags": [{"tag": "performance", "value": ""}]
            }
        ]
        
        detection_result = connectivity_analyzer.detect_connectivity_items_by_tags(items_data)
        
        # Step 2: Prepare history data
        history_data = {
            "1001": [  # 80% success - healthy
                {"itemid": "1001", "value": "1", "clock": str(1000 - i)}
                for i in range(8)
            ] + [
                {"itemid": "1001", "value": "0", "clock": str(992 - i)}
                for i in range(2)
            ],
            "2001": [  # 40% success - critical
                {"itemid": "2001", "value": "1", "clock": str(1000 - i)}
                for i in range(4)
            ] + [
                {"itemid": "2001", "value": "0", "clock": str(996 - i)}
                for i in range(6)
            ]
        }
        
        # Step 3: Analyze connectivity
        data_analyzer = DataAnalyzer(None)
        analysis_result = data_analyzer.analyze_tag_based_connectivity(
            detection_result=detection_result,
            history_data=history_data,
            threshold_percentage=70.0
        )
        
        # Verify results
        assert analysis_result["summary"]["total_hosts_analyzed"] == 2
        assert analysis_result["summary"]["hosts_with_issues"] == 1
        assert analysis_result["summary"]["hosts_without_connection_items"] == 1
        assert analysis_result["summary"]["items_below_threshold"] == 1
        
        # Verify host 1 (healthy)
        host1 = next(h for h in analysis_result["hosts"] if h["hostid"] == "100")
        assert host1["has_issues"] == False
        assert host1["items"][0]["percentage"] == 80.0
        assert host1["items"][0]["status"] == "healthy"
        
        # Verify host 2 (problematic)
        host2 = next(h for h in analysis_result["hosts"] if h["hostid"] == "200")
        assert host2["has_issues"] == True
        assert host2["items"][0]["percentage"] == 40.0
        assert host2["items"][0]["status"] == "critical"
        
        # Verify problematic items
        assert len(analysis_result["problematic_items"]) == 1
        assert analysis_result["problematic_items"][0]["itemid"] == "2001"
        
        # Verify hosts without connection items
        assert len(analysis_result["hosts_without_connection_items"]) == 1
        assert analysis_result["hosts_without_connection_items"][0]["hostid"] == "300"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
