"""
Data Analyzer
Analyzes connectivity data and calculates connectivity scores
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from utils.logger import get_logger
from config.template_loader import TemplateConfigLoader

logger = get_logger(__name__)


class DataAnalyzer:
    """Data analyzer for connectivity items"""
    
    def __init__(self, template_loader: Optional[TemplateConfigLoader] = None):
        """
        Initialize data analyzer
        
        Args:
            template_loader: Template configuration loader (optional)
        """
        self.template_loader = template_loader
        if template_loader:
            self.max_data_age = template_loader.get_threshold("max_data_age", 3600)
            self.inactive_threshold = template_loader.get_threshold("inactive_threshold", 7200)
            self.min_connectivity_score = template_loader.get_threshold("min_connectivity_score", 0.8)
        else:
            # Use defaults when no template loader is provided
            self.max_data_age = 3600
            self.inactive_threshold = 7200
            self.min_connectivity_score = 0.8
        logger.info("Data analyzer initialized")
    
    def analyze_connectivity(
        self,
        connectivity_items: List[Dict[str, Any]],
        history_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze connectivity items and calculate scores
        
        Args:
            connectivity_items: List of connectivity item dictionaries
            history_data: History data dictionary (item_id -> list of records)
            
        Returns:
            Analysis results dictionary
        """
        logger.info(f"Analyzing {len(connectivity_items)} connectivity items")
        
        # Group items by host
        items_by_host = self._group_items_by_host(connectivity_items)
        
        analysis_results = []
        
        for host_id, items in items_by_host.items():
            host_result = self._analyze_host_connectivity(items, history_data)
            analysis_results.append(host_result)
        
        # Calculate summary statistics
        summary = self._calculate_summary(analysis_results)
        
        result = {
            "summary": summary,
            "hosts": analysis_results,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Analysis completed: {summary['total_hosts']} hosts analyzed")
        return result
    
    def analyze_master_items(
        self,
        master_items: List[Dict[str, Any]],
        history_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze master items
        
        Args:
            master_items: List of master item dictionaries
            history_data: History data dictionary
            
        Returns:
            Master items analysis results
        """
        logger.info(f"Analyzing {len(master_items)} master items")
        
        master_item_threshold = self.template_loader.get_threshold("master_item_threshold", 1800)
        
        results = []
        active_count = 0
        inactive_count = 0
        
        for master_item in master_items:
            item_id = master_item.get("itemid")
            item_history = history_data.get(item_id, [])
            
            result_item = {
                "itemid": item_id,
                "hostid": master_item.get("hostid"),
                "hostname": master_item.get("hostname"),
                "key": master_item.get("key"),
                "name": master_item.get("name"),
                "template": master_item.get("template"),
                "status": master_item.get("status"),
                "lastvalue": master_item.get("lastvalue", ""),
                "lastclock": master_item.get("lastclock", ""),
                "data_available": False,
                "is_active": False,
                "data_age_seconds": None,
                "issue": None
            }
            
            if item_history:
                latest = item_history[-1]  # Most recent record
                lastclock = int(latest.get("clock", 0))
                result_item["lastclock"] = str(lastclock)
                result_item["lastvalue"] = latest.get("value", "")
                result_item["data_available"] = True
                
                # Calculate data age
                now = datetime.utcnow().timestamp()
                data_age = int(now - lastclock)
                result_item["data_age_seconds"] = data_age
                
                # Check if active
                if data_age <= master_item_threshold:
                    result_item["is_active"] = True
                    active_count += 1
                else:
                    result_item["is_active"] = False
                    result_item["issue"] = f"No recent data for {data_age // 60} minutes"
                    inactive_count += 1
            else:
                result_item["data_available"] = False
                result_item["is_active"] = False
                result_item["issue"] = "No data available"
                inactive_count += 1
            
            results.append(result_item)
        
        summary = {
            "total_master_items": len(master_items),
            "active_items": active_count,
            "inactive_items": inactive_count,
            "items_with_data": active_count + inactive_count,
            "items_without_data": len(master_items) - (active_count + inactive_count)
        }
        
        return {
            "summary": summary,
            "items": results,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_host_connectivity(
        self,
        items: List[Dict[str, Any]],
        history_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze connectivity for a single host
        
        Args:
            items: List of connectivity items for the host
            history_data: History data dictionary
            
        Returns:
            Host analysis result
        """
        if not items:
            return {
                "hostid": None,
                "hostname": None,
                "connectivity_score": 0.0,
                "total_items": 0,
                "active_items": 0,
                "inactive_items": 0,
                "connectivity_items": [],
                "issues": []
            }
        
        host_id = items[0].get("hostid")
        hostname = items[0].get("hostname")
        
        analyzed_items = []
        issues = []
        active_count = 0
        inactive_count = 0
        total_weight = 0.0
        weighted_score = 0.0
        
        for item in items:
            item_id = item.get("itemid")
            item_history = history_data.get(item_id, [])
            
            priority = item.get("priority", "medium")
            if self.template_loader:
                priority_level = self.template_loader.get_priority_level(priority)
            else:
                # Default priority levels
                priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
                priority_level = priority_map.get(priority, 3)
            weight = 1.0 / priority_level  # Higher priority = higher weight
            
            analyzed_item = {
                "itemid": item_id,
                "key": item.get("key"),
                "name": item.get("name"),
                "template": item.get("template"),
                "status": item.get("status"),
                "required": item.get("required", False),
                "priority": priority,
                "lastvalue": item.get("lastvalue", ""),
                "lastclock": item.get("lastclock", ""),
                "data_available": False,
                "is_active": False,
                "data_age_seconds": None
            }
            
            if item_history:
                latest = item_history[-1]
                lastclock = int(latest.get("clock", 0))
                analyzed_item["lastclock"] = str(lastclock)
                analyzed_item["lastvalue"] = latest.get("value", "")
                analyzed_item["data_available"] = True
                
                # Calculate data age
                now = datetime.utcnow().timestamp()
                data_age = int(now - lastclock)
                analyzed_item["data_age_seconds"] = data_age
                
                # Check if active
                if data_age <= self.inactive_threshold:
                    analyzed_item["is_active"] = True
                    active_count += 1
                    weighted_score += weight
                else:
                    analyzed_item["is_active"] = False
                    inactive_count += 1
                    issue_severity = "error" if item.get("required", False) else "warning"
                    issues.append({
                        "itemid": item_id,
                        "key": item.get("key"),
                        "name": item.get("name"),
                        "issue": f"No recent data for {data_age // 60} minutes",
                        "severity": issue_severity,
                        "data_age_seconds": data_age
                    })
            else:
                analyzed_item["data_available"] = False
                analyzed_item["is_active"] = False
                inactive_count += 1
                issue_severity = "error" if item.get("required", False) else "warning"
                issues.append({
                    "itemid": item_id,
                    "key": item.get("key"),
                    "name": item.get("name"),
                    "issue": "No data available",
                    "severity": issue_severity
                })
            
            total_weight += weight
            analyzed_items.append(analyzed_item)
        
        # Calculate connectivity score
        if total_weight > 0:
            connectivity_score = weighted_score / total_weight
        else:
            connectivity_score = 0.0
        
        return {
            "hostid": host_id,
            "hostname": hostname,
            "connectivity_score": round(connectivity_score, 3),
            "total_items": len(items),
            "active_items": active_count,
            "inactive_items": inactive_count,
            "connectivity_items": analyzed_items,
            "issues": issues
        }
    
    def _group_items_by_host(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by host ID"""
        grouped = {}
        for item in items:
            host_id = item.get("hostid")
            if host_id not in grouped:
                grouped[host_id] = []
            grouped[host_id].append(item)
        return grouped
    
    def _calculate_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total_hosts = len(analysis_results)
        hosts_with_connectivity = sum(1 for r in analysis_results if r["connectivity_score"] >= self.min_connectivity_score)
        hosts_without_connectivity = total_hosts - hosts_with_connectivity
        
        total_items = sum(r["total_items"] for r in analysis_results)
        active_items = sum(r["active_items"] for r in analysis_results)
        inactive_items = sum(r["inactive_items"] for r in analysis_results)
        
        if total_hosts > 0:
            avg_score = sum(r["connectivity_score"] for r in analysis_results) / total_hosts
        else:
            avg_score = 0.0
        
        return {
            "total_hosts": total_hosts,
            "hosts_with_connectivity": hosts_with_connectivity,
            "hosts_without_connectivity": hosts_without_connectivity,
            "average_connectivity_score": round(avg_score, 3),
            "total_connectivity_items": total_items,
            "active_items": active_items,
            "inactive_items": inactive_items
        }
    
    def save_analysis(self, analysis_result: Dict[str, Any], output_dir: str):
        """
        Save analysis results to file
        
        Args:
            analysis_result: Analysis results dictionary
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "analysis_results.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved analysis results to {file_path}")
    
    def save_master_items_analysis(self, master_analysis: Dict[str, Any], output_dir: str):
        """
        Save master items analysis to file
        
        Args:
            master_analysis: Master items analysis dictionary
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "master_items_check.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(master_analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved master items analysis to {file_path}")
    
    def calculate_connectivity_score(
        self,
        history_values: List[Dict[str, Any]],
        expected_value: Any = 1
    ) -> Dict[str, Any]:
        """
        Calculate connectivity score based on history values
        
        Args:
            history_values: List of history records (sorted DESC by clock)
            expected_value: Expected value for successful connectivity (default: 1)
            
        Returns:
            Dictionary with score, successful_count, total_count, and percentage
        """
        if not history_values:
            return {
                "score": 0.0,
                "successful_count": 0,
                "total_count": 0,
                "percentage": 0.0,
                "status": "no_data"
            }
        
        total_count = len(history_values)
        successful_count = 0
        
        # Count successful connections
        for record in history_values:
            value = record.get("value", "")
            # Convert value to appropriate type for comparison
            try:
                if isinstance(expected_value, int):
                    value = int(float(value))
                elif isinstance(expected_value, float):
                    value = float(value)
                else:
                    value = str(value)
                
                if value == expected_value:
                    successful_count += 1
            except (ValueError, TypeError):
                # If conversion fails, treat as unsuccessful
                continue
        
        # Calculate percentage
        percentage = (successful_count / total_count) * 100 if total_count > 0 else 0.0
        
        # Determine status
        if percentage >= 70:
            status = "healthy"
        elif percentage >= 50:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "score": round(percentage / 100, 3),  # 0.0 to 1.0
            "successful_count": successful_count,
            "total_count": total_count,
            "percentage": round(percentage, 2),
            "status": status
        }
    
    def analyze_tag_based_connectivity(
        self,
        detection_result: Dict[str, Any],
        history_data: Dict[str, List[Dict[str, Any]]],
        threshold_percentage: float = 70.0
    ) -> Dict[str, Any]:
        """
        Analyze connectivity items detected by tags
        
        Args:
            detection_result: Detection results from connectivity_analyzer
            history_data: History data dictionary (item_id -> list of records)
            threshold_percentage: Minimum acceptable connectivity percentage (default: 70%)
            
        Returns:
            Analysis results dictionary with per-item scoring
        """
        logger.info("Analyzing tag-based connectivity items")
        
        hosts_with_items = detection_result.get("hosts_with_items", [])
        hosts_without_items = detection_result.get("hosts_without_items", [])
        
        analyzed_hosts = []
        problematic_items = []
        
        for host_data in hosts_with_items:
            host_id = host_data.get("hostid")
            hostname = host_data.get("hostname")
            host_name = host_data.get("host_name", hostname)
            items = host_data.get("items", [])
            
            analyzed_items = []
            host_has_issues = False
            
            for item in items:
                item_id = item.get("itemid")
                item_history = history_data.get(item_id, [])
                
                # Calculate connectivity score
                score_result = self.calculate_connectivity_score(item_history)
                
                analyzed_item = {
                    "itemid": item_id,
                    "key": item.get("key"),
                    "name": item.get("name"),
                    "connectivity_score": score_result["score"],
                    "percentage": score_result["percentage"],
                    "successful_count": score_result["successful_count"],
                    "total_count": score_result["total_count"],
                    "status": score_result["status"],
                    "below_threshold": score_result["percentage"] < threshold_percentage
                }
                
                analyzed_items.append(analyzed_item)
                
                # Check if item is below threshold
                if score_result["percentage"] < threshold_percentage:
                    host_has_issues = True
                    problematic_items.append({
                        "hostid": host_id,
                        "hostname": hostname,
                        "host_name": host_name,
                        "itemid": item_id,
                        "item_key": item.get("key"),
                        "item_name": item.get("name"),
                        "percentage": score_result["percentage"],
                        "status": score_result["status"],
                        "detail": f"{host_name} hostunda bulunan {item.get('name')} item'ı için connection problemleri bulunmakta."
                    })
            
            analyzed_hosts.append({
                "hostid": host_id,
                "hostname": hostname,
                "host_name": host_name,
                "items": analyzed_items,
                "total_items": len(analyzed_items),
                "items_below_threshold": sum(1 for i in analyzed_items if i["below_threshold"]),
                "has_issues": host_has_issues
            })
        
        # Calculate summary
        total_hosts_analyzed = len(analyzed_hosts)
        hosts_with_issues = sum(1 for h in analyzed_hosts if h["has_issues"])
        total_items_analyzed = sum(h["total_items"] for h in analyzed_hosts)
        items_below_threshold = len(problematic_items)
        
        summary = {
            "total_hosts_analyzed": total_hosts_analyzed,
            "hosts_with_issues": hosts_with_issues,
            "hosts_without_issues": total_hosts_analyzed - hosts_with_issues,
            "hosts_without_connection_items": len(hosts_without_items),
            "total_items_analyzed": total_items_analyzed,
            "items_below_threshold": items_below_threshold,
            "threshold_percentage": threshold_percentage,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "summary": summary,
            "hosts": analyzed_hosts,
            "problematic_items": problematic_items,
            "hosts_without_connection_items": hosts_without_items
        }
    
    def save_tag_based_analysis(self, analysis_result: Dict[str, Any], output_dir: str):
        """
        Save tag-based analysis results to file
        
        Args:
            analysis_result: Analysis results dictionary
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / "tag_based_connectivity_analysis.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved tag-based connectivity analysis to {file_path}")
