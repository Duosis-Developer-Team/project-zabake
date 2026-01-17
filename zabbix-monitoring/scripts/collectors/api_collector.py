"""
Zabbix API Data Collector
Collects hosts, templates, items, and history data from Zabbix API
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)


class ZabbixAPIError(Exception):
    """Zabbix API error exception"""
    pass


class ZabbixAPICollector:
    """Zabbix API data collector"""
    
    def __init__(self, url: str, user: str, password: str, timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize Zabbix API collector
        
        Args:
            url: Zabbix API URL
            user: Zabbix username
            password: Zabbix password
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
        """
        self.url = url.rstrip('/')
        if not self.url.endswith('/api_jsonrpc.php'):
            self.url = f"{self.url}/api_jsonrpc.php"
        
        self.user = user
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auth_token = None
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Authenticate
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Zabbix API"""
        try:
            response = self._api_request("user.login", {
                "user": self.user,
                "password": self.password
            })
            self.auth_token = response.get("result")
            logger.info("Successfully authenticated with Zabbix API")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise ZabbixAPIError(f"Failed to authenticate: {str(e)}")
    
    def _api_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make API request to Zabbix
        
        Args:
            method: API method name
            params: Method parameters
            
        Returns:
            API response
        """
        if params is None:
            params = {}
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time() * 1000)
        }
        
        if self.auth_token:
            payload["auth"] = self.auth_token
        
        try:
            response = self.session.post(
                self.url,
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                raise ZabbixAPIError(f"API error: {error.get('message', 'Unknown error')} (Code: {error.get('code', 'N/A')})")
            
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise ZabbixAPIError(f"Request failed: {str(e)}")
    
    def get_hosts(self, filter_status: str = "enabled", host_groups: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get all hosts from Zabbix
        
        Args:
            filter_status: Filter by status ("enabled", "disabled", "all")
            host_groups: Filter by host group names
            
        Returns:
            List of host dictionaries
        """
        logger.info("Collecting hosts from Zabbix API")
        
        params = {
            "output": "extend",
            "selectGroups": "extend",
            "selectInterfaces": "extend",
            "selectParentTemplates": ["templateid", "name"],
            "selectTags": "extend"
        }
        
        # Filter by status
        if filter_status == "enabled":
            params["filter"] = {"status": "0"}
        elif filter_status == "disabled":
            params["filter"] = {"status": "1"}
        
        # Filter by host groups
        if host_groups:
            group_ids = self._get_group_ids(host_groups)
            if group_ids:
                params["groupids"] = group_ids
        
        try:
            response = self._api_request("host.get", params)
            hosts = response.get("result", [])
            logger.info(f"Collected {len(hosts)} hosts")
            return hosts
        
        except Exception as e:
            logger.error(f"Failed to collect hosts: {str(e)}")
            raise
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Get all templates from Zabbix
        
        Returns:
            List of template dictionaries
        """
        logger.info("Collecting templates from Zabbix API")
        
        params = {
            "output": "extend",
            "selectGroups": "extend",
            "selectParentTemplates": ["templateid", "name"],
            "selectTags": "extend"
        }
        
        try:
            response = self._api_request("template.get", params)
            templates = response.get("result", [])
            logger.info(f"Collected {len(templates)} templates")
            return templates
        
        except Exception as e:
            logger.error(f"Failed to collect templates: {str(e)}")
            raise
    
    def get_template_items(self, template_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get items for specific templates
        
        Args:
            template_ids: List of template IDs
            
        Returns:
            List of item dictionaries
        """
        logger.info(f"Collecting items for {len(template_ids)} templates")
        
        params = {
            "output": "extend",
            "templateids": template_ids
        }
        
        try:
            response = self._api_request("item.get", params)
            items = response.get("result", [])
            logger.info(f"Collected {len(items)} items")
            return items
        
        except Exception as e:
            logger.error(f"Failed to collect template items: {str(e)}")
            raise
    
    def get_host_items(self, host_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get items for specific hosts
        
        Args:
            host_ids: List of host IDs
            
        Returns:
            List of item dictionaries
        """
        logger.info(f"Collecting items for {len(host_ids)} hosts")
        
        items = []
        batch_size = 100  # Process in batches
        
        for i in range(0, len(host_ids), batch_size):
            batch = host_ids[i:i + batch_size]
            
            params = {
                "output": "extend",
                "hostids": batch
            }
            
            try:
                response = self._api_request("item.get", params)
                batch_items = response.get("result", [])
                items.extend(batch_items)
                logger.debug(f"Collected {len(batch_items)} items for batch {i // batch_size + 1}")
            
            except Exception as e:
                logger.error(f"Failed to collect items for batch: {str(e)}")
                raise
        
        logger.info(f"Collected total {len(items)} items")
        return items
    
    def get_item_history(
        self,
        item_ids: List[str],
        value_type: int = 3,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
        limit: int = 1
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get history data for items
        
        Args:
            item_ids: List of item IDs
            value_type: Value type (0=float, 1=str, 2=log, 3=uint, 4=text)
            time_from: Start time (default: 1 hour ago)
            time_to: End time (default: now)
            limit: Number of records per item (default: 1, latest)
            
        Returns:
            Dictionary mapping item_id to list of history records
        """
        logger.info(f"Collecting history for {len(item_ids)} items")
        
        if time_from is None:
            time_from = datetime.now() - timedelta(hours=1)
        if time_to is None:
            time_to = datetime.now()
        
        time_from_ts = int(time_from.timestamp())
        time_to_ts = int(time_to.timestamp())
        
        history_data = {}
        batch_size = 50  # Process in smaller batches for history
        
        for i in range(0, len(item_ids), batch_size):
            batch = item_ids[i:i + batch_size]
            
            params = {
                "output": "extend",
                "itemids": batch,
                "history": value_type,
                "time_from": time_from_ts,
                "time_to": time_to_ts,
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": limit
            }
            
            try:
                response = self._api_request("history.get", params)
                batch_history = response.get("result", [])
                
                # Group by item_id
                for record in batch_history:
                    item_id = record.get("itemid")
                    if item_id not in history_data:
                        history_data[item_id] = []
                    history_data[item_id].append(record)
                
                logger.debug(f"Collected history for batch {i // batch_size + 1}")
            
            except Exception as e:
                logger.error(f"Failed to collect history for batch: {str(e)}")
                # Continue with other batches
        
        logger.info(f"Collected history for {len(history_data)} items")
        return history_data
    
    def get_item_trends(
        self,
        item_ids: List[str],
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trend data for items
        
        Args:
            item_ids: List of item IDs
            time_from: Start time (default: 1 hour ago)
            time_to: End time (default: now)
            
        Returns:
            Dictionary mapping item_id to list of trend records
        """
        logger.info(f"Collecting trends for {len(item_ids)} items")
        
        if time_from is None:
            time_from = datetime.now() - timedelta(hours=1)
        if time_to is None:
            time_to = datetime.now()
        
        time_from_ts = int(time_from.timestamp())
        time_to_ts = int(time_to.timestamp())
        
        params = {
            "output": "extend",
            "itemids": item_ids,
            "time_from": time_from_ts,
            "time_to": time_to_ts
        }
        
        try:
            response = self._api_request("trend.get", params)
            trends = response.get("result", [])
            
            # Group by item_id
            trend_data = {}
            for record in trends:
                item_id = record.get("itemid")
                if item_id not in trend_data:
                    trend_data[item_id] = []
                trend_data[item_id].append(record)
            
            logger.info(f"Collected trends for {len(trend_data)} items")
            return trend_data
        
        except Exception as e:
            logger.error(f"Failed to collect trends: {str(e)}")
            raise
    
    def _get_group_ids(self, group_names: List[str]) -> List[str]:
        """
        Get host group IDs by names
        
        Args:
            group_names: List of host group names
            
        Returns:
            List of group IDs
        """
        if not group_names:
            return []
        
        params = {
            "output": ["groupid"],
            "filter": {"name": group_names}
        }
        
        try:
            response = self._api_request("hostgroup.get", params)
            groups = response.get("result", [])
            return [g["groupid"] for g in groups]
        
        except Exception as e:
            logger.warning(f"Failed to get group IDs: {str(e)}")
            return []
    
    def save_collected_data(
        self,
        output_dir: str,
        hosts: List[Dict[str, Any]] = None,
        templates: List[Dict[str, Any]] = None,
        items: List[Dict[str, Any]] = None,
        history: Dict[str, List[Dict[str, Any]]] = None
    ):
        """
        Save collected data to JSON files
        
        Args:
            output_dir: Output directory
            hosts: Host data
            templates: Template data
            items: Item data
            history: History data
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if hosts is not None:
            file_path = output_path / "hosts.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(hosts, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(hosts)} hosts to {file_path}")
        
        if templates is not None:
            file_path = output_path / "templates.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(templates)} templates to {file_path}")
        
        if items is not None:
            file_path = output_path / "items.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(items)} items to {file_path}")
        
        if history is not None:
            file_path = output_path / "history.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved history for {len(history)} items to {file_path}")
