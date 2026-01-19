#!/usr/bin/env python3
"""
Test script to check Zabbix API connection and analyze 'connection status' tags
"""

import requests
import json
from pprint import pprint

# Zabbix API Configuration
ZABBIX_URL = "http://10.134.16.235/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

class ZabbixAPI:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password
        self.auth_token = None
        self.request_id = 0
        
    def _make_request(self, method, params):
        """Make a JSON-RPC request to Zabbix API"""
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        if self.auth_token:
            payload["auth"] = self.auth_token
            
        try:
            response = requests.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json-rpc"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                print(f"[X] API Error: {result['error']}")
                return None
                
            return result.get("result")
            
        except Exception as e:
            print(f"[X] Request failed: {e}")
            return None
    
    def login(self):
        """Authenticate with Zabbix API"""
        print(f"[*] Logging in to Zabbix at {self.url}")
        
        # Try with 'user' parameter (Zabbix 5.x+)
        result = self._make_request("user.login", {
            "user": self.user,
            "password": self.password
        })
        
        if result:
            self.auth_token = result
            print(f"[+] Authentication successful (token: {self.auth_token[:20]}...)")
            return True
        
        # Try with 'username' parameter (older versions)
        result = self._make_request("user.login", {
            "username": self.user,
            "password": self.password
        })
        
        if result:
            self.auth_token = result
            print(f"[+] Authentication successful (token: {self.auth_token[:20]}...)")
            return True
            
        print("[X] Authentication failed")
        return False
    
    def get_items_by_tags(self, tag_name="connection status"):
        """Get items by tag name - searches without value filter"""
        print(f"\n[*] Searching for items with tag: '{tag_name}' (any value including None)")
        
        params = {
            "output": ["itemid", "name", "key_", "status", "hostid"],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": "extend",
            "evaltype": 0,  # AND/OR evaluation
            "tags": [
                {
                    "tag": tag_name
                    # No operator or value - matches any value including None
                }
            ],
            "monitored": True
        }
        
        result = self._make_request("item.get", params)
        return result if result else []
    
    def get_items_by_tags_python_filter(self, tag_name="connection status", limit=500):
        """Get items and filter by tag in Python (works for value=None)"""
        print(f"\n[*] Fetching all items and filtering for tag: '{tag_name}' (Python-side)")
        
        params = {
            "output": ["itemid", "name", "key_", "status", "hostid"],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": "extend",
            "monitored": True,
            "limit": limit
        }
        
        result = self._make_request("item.get", params)
        
        if not result:
            return []
        
        # Filter items that have the specific tag (regardless of value)
        matching_items = []
        for item in result:
            if item.get("tags"):
                for tag in item["tags"]:
                    if tag.get("tag", "").lower() == tag_name.lower():
                        matching_items.append(item)
                        break
        
        return matching_items
    
    def get_all_items_with_any_tags(self):
        """Get all items that have any tags"""
        print(f"\n[*] Searching for all items that have tags")
        
        params = {
            "output": ["itemid", "name", "key_", "status", "hostid"],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": "extend",
            "monitored": True,
            "limit": 50
        }
        
        result = self._make_request("item.get", params)
        
        # Filter only items that have tags
        if result:
            items_with_tags = [item for item in result if item.get("tags")]
            return items_with_tags
        return []
    
    def search_tags_containing_text(self, text="connection"):
        """Search for items with tags containing specific text"""
        print(f"\n[*] Searching for items with tags containing: '{text}'")
        
        # Get items with tags
        params = {
            "output": ["itemid", "name", "key_", "status", "hostid"],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": "extend",
            "monitored": True,
            "limit": 100
        }
        
        result = self._make_request("item.get", params)
        
        if not result:
            return []
        
        # Filter items with tags containing the text
        matching_items = []
        for item in result:
            if item.get("tags"):
                for tag in item["tags"]:
                    if text.lower() in tag.get("tag", "").lower():
                        matching_items.append(item)
                        break
        
        return matching_items
    
    def get_api_version(self):
        """Get Zabbix API version"""
        result = self._make_request("apiinfo.version", {})
        return result

def main():
    print("=" * 80)
    print("ZABBIX API TAG ANALYSIS")
    print("=" * 80)
    
    # Initialize API
    api = ZabbixAPI(ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD)
    
    # Check API version
    version = api.get_api_version()
    if version:
        print(f"[*] Zabbix API Version: {version}")
    
    # Login
    if not api.login():
        print("[X] Cannot proceed without authentication")
        return
    
    print("\n" + "=" * 80)
    print("TEST 1: Direct API search (no operator)")
    print("=" * 80)
    items = api.get_items_by_tags("connection status")
    print(f"[*] Found {len(items)} items")
    if items:
        print("\n[+] Sample items:")
        for i, item in enumerate(items[:5], 1):
            host = item.get("hosts", [{}])[0]
            print(f"\n{i}. Item ID: {item['itemid']}")
            print(f"   Name: {item['name']}")
            print(f"   Key: {item['key_']}")
            print(f"   Host: {host.get('name', 'N/A')} ({host.get('host', 'N/A')})")
            print(f"   Status: {'Enabled' if item['status'] == '0' else 'Disabled'}")
            print(f"   Tags: {item.get('tags', [])}")
    
    print("\n" + "=" * 80)
    print("TEST 2: Python-side filtering (fetch all, filter locally)")
    print("=" * 80)
    items_python = api.get_items_by_tags_python_filter("connection status", limit=200)
    print(f"[*] Found {len(items_python)} items")
    if items_python:
        print("\n[+] Sample items:")
        for i, item in enumerate(items_python[:5], 1):
            host = item.get("hosts", [{}])[0]
            print(f"\n{i}. Item ID: {item['itemid']}")
            print(f"   Name: {item['name']}")
            print(f"   Key: {item['key_']}")
            print(f"   Host: {host.get('name', 'N/A')} ({host.get('host', 'N/A')})")
            print(f"   Tags: {item.get('tags', [])}")
    
    print("\n" + "=" * 80)
    print("TEST 3: Get all items with any tags (sample of 50)")
    print("=" * 80)
    items_with_tags = api.get_all_items_with_any_tags()
    print(f"[*] Found {len(items_with_tags)} items with tags")
    
    if items_with_tags:
        print("\n[+] Unique tag names found:")
        all_tags = set()
        for item in items_with_tags:
            for tag in item.get("tags", []):
                all_tags.add(tag.get("tag", ""))
        
        for tag in sorted(all_tags):
            if tag:
                print(f"   - '{tag}'")
        
        print("\n[+] Sample items with tags:")
        for i, item in enumerate(items_with_tags[:10], 1):
            host = item.get("hosts", [{}])[0]
            print(f"\n{i}. Item: {item['name']}")
            print(f"   Host: {host.get('name', 'N/A')}")
            tags_str = [f"{t['tag']}={t.get('value', '')}" for t in item.get('tags', [])]
            print(f"   Tags: {tags_str}")
    
    print("\n" + "=" * 80)
    print("TEST 4: Search for tags containing 'connection'")
    print("=" * 80)
    connection_items = api.search_tags_containing_text("connection")
    print(f"[*] Found {len(connection_items)} items")
    
    if connection_items:
        print("\n[+] Items with 'connection' in tags:")
        for i, item in enumerate(connection_items[:10], 1):
            host = item.get("hosts", [{}])[0]
            print(f"\n{i}. Item: {item['name']}")
            print(f"   Host: {host.get('name', 'N/A')}")
            tags_str = [f"{t['tag']}={t.get('value', '')}" for t in item.get('tags', [])]
            print(f"   Tags: {tags_str}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    # Summary
    print("\n[*] SUMMARY:")
    print(f"   - Items with 'connection status' tag (API direct): {len(items)}")
    print(f"   - Items with 'connection status' tag (Python filter): {len(items_python)}")
    print(f"   - Items with any tags (sample): {len(items_with_tags)}")
    print(f"   - Items with 'connection' in tags: {len(connection_items)}")
    
    if len(items) == 0 and len(items_python) == 0:
        print("\n[!] WARNING: No items found with 'connection status' tag!")
        print("   Possible reasons:")
        print("   1. Tag name is different (check case sensitivity)")
        print("   2. Items are disabled (status != 0)")
        print("   3. Tags are on templates, not on host items")
        print("   4. Tag spelling is different")
        
        if items_with_tags:
            print("\n[!] RECOMMENDATION: Check the tag names found above")
            print("   The playbook is looking for exactly: 'connection status'")

if __name__ == "__main__":
    main()
