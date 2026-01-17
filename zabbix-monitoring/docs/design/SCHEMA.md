# Data Schema - Zabbix Monitoring Integration

Bu doküman, Zabbix Monitoring Integration modülünde kullanılan veri yapılarını ve şemalarını açıklar.

## 📊 Veri Yapıları

### 1. Host Data Structure

```python
Host = {
    "hostid": str,              # Zabbix host ID
    "host": str,                # Hostname (unique identifier)
    "name": str,                # Display name
    "status": str,             # "0" = enabled, "1" = disabled
    "available": str,          # "0" = unknown, "1" = available, "2" = unavailable
    "description": str,        # Host description
    "proxy_hostid": str,       # Proxy host ID (if any)
    "ip": str,                 # IP address
    "dns": str,                # DNS name
    "port": str,               # Port number
    "templates": [             # Linked templates
        {
            "templateid": str,
            "name": str
        }
    ],
    "groups": [                # Host groups
        {
            "groupid": str,
            "name": str
        }
    ],
    "interfaces": [            # Host interfaces
        {
            "interfaceid": str,
            "type": str,       # "1" = agent, "2" = SNMP, "3" = IPMI, "4" = JMX
            "ip": str,
            "dns": str,
            "port": str,
            "main": str        # "1" = main interface
        }
    ]
}
```

### 2. Template Data Structure

```python
Template = {
    "templateid": str,         # Template ID
    "name": str,               # Template name
    "host": str,               # Template hostname
    "description": str,        # Template description
    "status": str,             # "0" = enabled, "1" = disabled
    "groups": [                # Template groups
        {
            "groupid": str,
            "name": str
        }
    ],
    "parent_templates": [      # Parent templates (inheritance)
        {
            "templateid": str,
            "name": str
        }
    ],
    "items": [                 # Template items
        Item
    ],
    "triggers": [              # Template triggers
        {
            "triggerid": str,
            "description": str,
            "expression": str,
            "status": str
        }
    ]
}
```

### 3. Item Data Structure

```python
Item = {
    "itemid": str,            # Item ID
    "hostid": str,            # Host ID (if linked to host)
    "templateid": str,       # Template ID (if linked to template)
    "name": str,             # Item name
    "key_": str,             # Item key
    "type": str,             # Item type
                          # "0" = Zabbix agent
                          # "1" = SNMPv1 agent
                          # "2" = Zabbix trapper
                          # "3" = simple check
                          # "4" = SNMPv2 agent
                          # "5" = Zabbix internal
                          # "6" = SNMPv3 agent
                          # "7" = Zabbix agent (active)
                          # "8" = Zabbix aggregate
                          # "9" = web item
                          # "10" = external check
                          # "11" = database monitor
                          # "12" = IPMI agent
                          # "13" = SSH agent
                          # "14" = TELNET agent
                          # "15" = calculated
                          # "16" = JMX agent
                          # "17" = SNMP trap
                          # "18" = Dependent item
                          # "19" = HTTP agent
                          # "20" = SNMP agent
    "value_type": str,       # Value type
                          # "0" = float
                          # "1" = character
                          # "2" = log
                          # "3" = numeric unsigned
                          # "4" = text
    "units": str,            # Units
    "status": str,           # "0" = enabled, "1" = disabled
    "state": str,            # "0" = normal, "1" = not supported
    "delay": str,            # Update interval
    "history": str,           # History storage period (days)
    "trends": str,           # Trends storage period (days)
    "lastvalue": str,        # Last value
    "lastclock": str,        # Last update timestamp (Unix time)
    "prevvalue": str,        # Previous value
    "templateid": str,       # Template ID (if from template)
    "template_name": str     # Template name (if from template)
}
```

### 4. Connectivity Item Structure

```python
ConnectivityItem = {
    "itemid": str,           # Item ID
    "hostid": str,           # Host ID
    "hostname": str,         # Host hostname
    "key_": str,             # Item key
    "name": str,             # Item name
    "template": str,         # Template name
    "templateid": str,       # Template ID
    "type": str,             # Item type
    "value_type": str,       # Value type
    "status": str,           # Item status
    "lastvalue": str,        # Last value
    "lastclock": str,        # Last update timestamp
    "lastclock_formatted": str,  # Formatted timestamp
    "data_available": bool,  # Whether data is available
    "data_age_seconds": int, # Age of last data in seconds
    "is_active": bool        # Whether item is considered active
}
```

### 5. History Data Structure

```python
HistoryData = {
    "itemid": str,          # Item ID
    "clock": str,           # Timestamp (Unix time)
    "value": str,           # Value
    "ns": str               # Nanoseconds
}
```

### 6. Analysis Result Structure

```python
AnalysisResult = {
    "hostid": str,                    # Host ID
    "hostname": str,                  # Host hostname
    "name": str,                      # Host display name
    "connectivity_score": float,       # Connectivity score (0.0 - 1.0)
    "total_items": int,               # Total connectivity items
    "active_items": int,              # Active items count
    "inactive_items": int,            # Inactive items count
    "connectivity_items": [            # Connectivity items details
        ConnectivityItem
    ],
    "issues": [                       # Issues found
        {
            "itemid": str,
            "key_": str,
            "name": str,
            "issue": str,             # Issue description
            "severity": str,          # "info", "warning", "error"
            "data_age_seconds": int
        }
    ],
    "templates": [                    # Templates used
        {
            "templateid": str,
            "name": str,
            "items_count": int
        }
    ],
    "last_analysis": str              # Analysis timestamp (ISO format)
}
```

### 7. Report Structure

```python
Report = {
    "report_metadata": {
        "generated_at": str,          # ISO timestamp
        "generator_version": str,     # Version
        "data_source": str,           # "api" or "database"
        "total_hosts": int,           # Total hosts analyzed
        "total_items_analyzed": int   # Total items analyzed
    },
    "summary": {
        "total_hosts": int,
        "hosts_with_connectivity": int,
        "hosts_without_connectivity": int,
        "average_connectivity_score": float,
        "total_connectivity_items": int,
        "active_items": int,
        "inactive_items": int
    },
    "hosts": [                        # Analysis results per host
        AnalysisResult
    ],
    "statistics": {
        "by_template": {              # Statistics by template
            "template_name": {
                "total_hosts": int,
                "connectivity_score": float
            }
        },
        "by_status": {                # Statistics by status
            "active": int,
            "inactive": int
        },
        "by_severity": {              # Statistics by issue severity
            "info": int,
            "warning": int,
            "error": int
        }
    }
}
```

## 🔍 Connectivity Item Patterns

Connectivity item'ları şu pattern'lere göre tespit edilir:

### Key Patterns

```python
CONNECTIVITY_PATTERNS = [
    "icmpping",              # ICMP ping
    "icmppingsec",           # ICMP ping response time
    "icmppingloss",          # ICMP ping loss
    "net.tcp.service",       # TCP service check
    "net.tcp.service.perf", # TCP service performance
    "net.udp.service",      # UDP service check
    "agent.ping",            # Zabbix agent ping
    "system.ping",           # System ping
    "vmware.hv.ping",        # VMware hypervisor ping
    "vcenter.hv.ping"        # vCenter hypervisor ping
]
```

### Item Type Filters

```python
CONNECTIVITY_ITEM_TYPES = [
    "0",   # Zabbix agent
    "3",   # Simple check
    "7",   # Zabbix agent (active)
    "9",   # Web item
    "10",  # External check
]
```

## 📈 Data Flow Schema

```
┌─────────────┐
│ Zabbix API  │
│   or DB     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Hosts     │ ──► Host[]
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Templates   │ ──► Template[]
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Items     │ ──► Item[]
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Connectivity│ ──► ConnectivityItem[]
│   Filter    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   History   │ ──► HistoryData[]
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Analysis   │ ──► AnalysisResult[]
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Report    │ ──► Report
└─────────────┘
```

## 🔄 Data Transformation

### Host + Template → Connectivity Items

```python
def extract_connectivity_items(host: Host, templates: List[Template]) -> List[ConnectivityItem]:
    """
    Extract connectivity items from host and its templates
    """
    connectivity_items = []
    
    # Get items from host
    for item in host.items:
        if is_connectivity_item(item):
            connectivity_items.append(create_connectivity_item(item, host))
    
    # Get items from templates
    for template in templates:
        for item in template.items:
            if is_connectivity_item(item):
                connectivity_items.append(create_connectivity_item(item, host, template))
    
    return connectivity_items
```

### Connectivity Items + History → Analysis Result

```python
def analyze_connectivity(
    connectivity_items: List[ConnectivityItem],
    history_data: Dict[str, List[HistoryData]]
) -> AnalysisResult:
    """
    Analyze connectivity items and generate analysis result
    """
    active_count = 0
    inactive_count = 0
    issues = []
    
    for item in connectivity_items:
        item_history = history_data.get(item.itemid, [])
        
        if item_history:
            latest = item_history[-1]
            item.lastclock = latest.clock
            item.lastvalue = latest.value
            item.data_available = True
            item.data_age_seconds = calculate_age(latest.clock)
            
            if item.data_age_seconds < INACTIVE_THRESHOLD:
                item.is_active = True
                active_count += 1
            else:
                item.is_active = False
                inactive_count += 1
                issues.append(create_issue(item, "No recent data"))
        else:
            item.data_available = False
            item.is_active = False
            inactive_count += 1
            issues.append(create_issue(item, "No data available"))
    
    connectivity_score = active_count / len(connectivity_items) if connectivity_items else 0.0
    
    return AnalysisResult(
        connectivity_score=connectivity_score,
        active_items=active_count,
        inactive_items=inactive_count,
        connectivity_items=connectivity_items,
        issues=issues
    )
```

## 📝 Notlar

- Tüm timestamp'ler Unix time formatında saklanır
- String değerler Zabbix API'den geldiği gibi string olarak tutulur
- Boolean değerler Python boolean olarak işlenir
- Connectivity score 0.0 (tamamen bağlantısız) ile 1.0 (tamamen bağlantılı) arasında değer alır
- Item status "0" = enabled, "1" = disabled
- Host status "0" = enabled, "1" = disabled
