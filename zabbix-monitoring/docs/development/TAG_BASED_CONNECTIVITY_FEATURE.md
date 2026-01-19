# Tag-Based Connectivity Feature

## 📋 Overview

This feature implements a tag-based approach for detecting and analyzing connectivity items in Zabbix, replacing the previous template mapping-based approach.

## 🎯 Motivation

**Previous Approach Limitations:**
- Required manual configuration in `templates.yml` for each connectivity item
- Item names/keys had to match specific patterns
- Required maintenance when item names changed
- Not flexible for different environments

**New Approach Benefits:**
- No configuration needed - uses Zabbix tags
- Simply add "connection status" tag to any item that represents connectivity
- Flexible - works with any item type, name, or key
- Easy to maintain - add/remove tags in Zabbix UI

## 🏗️ Architecture

### Data Flow

```
1. Zabbix API → Get items with "connection status" tag
2. Group items by host
3. Collect last N history values for each item (default: 10)
4. Calculate connectivity score per item
5. Identify items below threshold (default: 70%)
6. Generate report with problematic items
7. Send email notification
```

### Components

1. **API Collector** (`api_collector.py`)
   - `get_items_by_tags()`: Fetch items by tag
   - `get_item_history_by_value_types()`: Collect history for items with different value types

2. **Connectivity Analyzer** (`connectivity_analyzer.py`)
   - `detect_connectivity_items_by_tags()`: Detect and group connectivity items by host
   - Identify hosts without connection items

3. **Data Analyzer** (`data_analyzer.py`)
   - `calculate_connectivity_score()`: Calculate score based on last N values
   - `analyze_tag_based_connectivity()`: Analyze all items with per-item scoring

4. **Main Script** (`main.py`)
   - New mode: `tag-based-connectivity`
   - Orchestrates the entire workflow

5. **Ansible Playbooks**
   - `zabbix_tag_based_monitoring.yaml`: Main playbook
   - `tag_based_connectivity_check.yml`: Task for running check
   - `send_tag_based_notification_email.yml`: Task for sending email

## 📊 Scoring Algorithm

### Connectivity Score Calculation

For each item, we analyze the last N values (default: 10):

```
Score = (Successful Checks / Total Checks) × 100
```

**Example:**
- Last 10 values: [1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
- Successful: 8
- Total: 10
- Score: 80%
- Status: Healthy (≥70%)

### Status Thresholds

- **Healthy**: ≥70% (Green)
- **Warning**: 50-69% (Orange)
- **Critical**: <50% (Red)

### Per-Item Evaluation

Each item is evaluated independently:
- Host X has items A, B, C
- Item A: 90% (Healthy)
- Item B: 65% (Warning)
- Item C: 45% (Critical)

Result: Items B and C are reported as problematic.

## 📧 Email Report Format

### Report Sections

1. **Summary**
   - Total hosts analyzed
   - Hosts with issues
   - Hosts without connection items
   - Total items analyzed
   - Items below threshold

2. **Problematic Items Table**
   - Host name
   - Item name
   - Connectivity score
   - Status (Critical/Warning)
   - Detail message

3. **Hosts Without Connection Items**
   - List of hosts that don't have any items with "connection status" tag
   - Useful for identifying missing monitoring

### Example Report

```
Host       Item                Score   Status     Detail
--------------------------------------------------------------
Server-A   SNMP availability   45%     CRITICAL   Server-A hostunda bulunan SNMP availability item'ı için connection problemleri bulunmakta.
Server-A   ICMP ping           60%     WARNING    Server-A hostunda bulunan ICMP ping item'ı için connection problemleri bulunmakta.
Server-B   Agent status        30%     CRITICAL   Server-B hostunda bulunan Agent status item'ı için connection problemleri bulunmakta.

Hosts Without Connection Items:
- Server-C
- Server-D
```

## 🚀 Usage

### 1. Tag Items in Zabbix

Add "connection status" tag to any item that represents connectivity:

1. Go to Configuration → Hosts
2. Select a host
3. Go to Items
4. Edit the item
5. Add tag: `connection status` (value can be empty)

### 2. Run via Python Script

```bash
python3 scripts/main.py \
  --mode tag-based-connectivity \
  --zabbix-url "http://zabbix.example.com" \
  --zabbix-user "admin" \
  --zabbix-password "password" \
  --output-dir "./reports" \
  --connection-tag "connection status" \
  --history-limit 10 \
  --threshold-percentage 70.0 \
  --log-level INFO
```

### 3. Run via Ansible

```bash
ansible-playbook \
  -i inventory \
  zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=http://zabbix.example.com" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password" \
  -e "email_to=admin@example.com"
```

### 4. AWX Integration

Create a job template with:

**Extra Variables:**
```yaml
zabbix_url: "http://zabbix.example.com"
zabbix_user: "admin"
zabbix_password: "password"
connection_tag: "connection status"
history_limit: 10
threshold_percentage: 70.0
send_email: true
email_to: "admin@example.com"
```

## 🔧 Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `connection_tag` | Tag name to identify connection items | "connection status" |
| `history_limit` | Number of history records to analyze | 10 |
| `threshold_percentage` | Minimum acceptable percentage | 70.0 |
| `host_groups` | Filter by host groups (comma-separated) | All hosts |

## 📝 Output Files

The script generates the following files:

1. **connectivity_items_by_tag.json**
   - Detected connectivity items grouped by host
   - Hosts without connection items

2. **tag_based_connectivity_analysis.json**
   - Complete analysis results
   - Per-item scores
   - Problematic items
   - Summary statistics

3. **history.json**
   - Raw history data for all analyzed items

## 🧪 Testing

### Manual Testing Steps

1. Create test hosts in Zabbix
2. Add items with "connection status" tag
3. Generate some history data
4. Run the script
5. Verify analysis results
6. Check email notification

### Unit Tests

```bash
cd zabbix-monitoring
python3 -m pytest tests/test_tag_based_connectivity.py -v
```

## 🆚 Comparison with Old Approach

| Aspect | Old Approach | New Approach |
|--------|--------------|--------------|
| Configuration | Required in YAML file | No configuration needed |
| Flexibility | Limited to predefined patterns | Any item can be tagged |
| Maintenance | Update YAML for each change | Update tags in Zabbix UI |
| Scalability | Manual work for new templates | Automatic with tags |
| Scoring | Host-level weighted average | Per-item individual scores |
| Threshold | Single global threshold | Per-item threshold check |

## 🔄 Migration from Old Approach

If you're migrating from the old template-based approach:

1. **Keep both approaches available** for transition period
2. **Tag existing items** that were previously detected by template mapping
3. **Test parallel** - run both approaches and compare results
4. **Gradually migrate** - move hosts group by group
5. **Deprecate old approach** once all items are tagged

## 📚 Related Documentation

- [API Reference](../scripts/API_REFERENCE.md)
- [Architecture](../design/ARCHITECTURE.md)
- [Email Notification Guide](../guides/EMAIL_NOTIFICATION_GUIDE.md)
- [AWX Testing Guide](../guides/AWX_TESTING.md)

## 🎯 Future Enhancements

1. **Multiple tag support** - Combine different tags for advanced filtering
2. **Custom scoring algorithms** - Different calculation methods per item type
3. **Historical trend analysis** - Track score changes over time
4. **Predictive alerts** - Predict issues before threshold is reached
5. **Dashboard integration** - Real-time connectivity dashboard

## 📊 Benefits Summary

✅ **Zero Configuration** - No YAML files to maintain
✅ **Flexible** - Works with any item type
✅ **Per-Item Analysis** - Individual scoring and reporting
✅ **Easy Maintenance** - Manage tags in Zabbix UI
✅ **Scalable** - Handles large environments
✅ **Comprehensive Reports** - Detailed per-item breakdown
✅ **Missing Item Detection** - Identifies hosts without monitoring

## 🐛 Troubleshooting

### No items found
- Verify items have "connection status" tag in Zabbix
- Check tag spelling and case sensitivity
- Ensure items are monitored (status = 0)

### Score always 0%
- Check if items have history data
- Verify expected value (default: 1 for successful)
- Increase history_limit if needed

### Email not sent
- Verify SMTP settings
- Check email credentials
- Review log file for errors

## 📞 Support

For issues or questions:
1. Check log file: `/tmp/zabbix_tag_based_monitoring.log`
2. Review analysis results: `tag_based_connectivity_analysis.json`
3. Enable debug mode: `debug_enabled: true`
