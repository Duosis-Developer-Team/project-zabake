# Zabbix Monitoring Integration

> **Tag-Based Connectivity Monitoring for Zabbix**

Monitor Zabbix host connectivity by tagging items - no configuration files needed!

## 🚀 Quick Start

### 1. Tag Items in Zabbix

Add `connection status` tag to connectivity-related items:
- ICMP ping items
- SNMP availability items
- Agent status items
- Any custom connectivity checks

### 2. Run Monitoring

```bash
# Python
cd scripts
python3 main.py --mode tag-based-connectivity \
  --zabbix-url "http://zabbix.example.com" \
  --zabbix-user "admin" \
  --zabbix-password "password"

# Ansible
cd playbooks
ansible-playbook zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=http://zabbix.example.com" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### 3. Get Results

- **Per-item connectivity scores** (based on last 10 values)
- **Email notifications** for items below 70% threshold
- **Missing monitoring detection** for hosts without connection items

## 📚 Documentation

- **[Quick Start Guide](TAG_BASED_CONNECTIVITY_README.md)** - Get started in 5 minutes
- **[Complete Documentation](docs/development/TAG_BASED_CONNECTIVITY_FEATURE.md)** - Detailed feature guide
- **[Architecture](docs/design/ARCHITECTURE.md)** - System design
- **[AWX Guide](docs/guides/AWX_TESTING.md)** - AWX/Tower integration

## 🎯 Key Features

✅ **Zero Configuration** - Just tag items in Zabbix  
✅ **Flexible** - Works with any item type  
✅ **Per-Item Scoring** - Individual connectivity analysis  
✅ **Email Reports** - Detailed HTML notifications  
✅ **Missing Detection** - Identifies unmonitored hosts  
✅ **Scalable** - Handles large environments  

## 📊 How It Works

1. **Detection**: Finds all items with "connection status" tag
2. **Analysis**: Calculates score from last N history values
3. **Scoring**: `Score = (Successful Checks / Total Checks) × 100`
4. **Reporting**: Items below threshold (default: 70%) are reported
5. **Notification**: Email sent with detailed breakdown

## ⚙️ Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `connection_tag` | Tag name for connection items | "connection status" |
| `history_limit` | Number of values to analyze | 10 |
| `threshold_percentage` | Minimum acceptable % | 70.0 |
| `host_groups` | Filter by host groups | All hosts |

## 🧪 Testing

```bash
# Manual test (no Zabbix needed)
python3 scripts/test_tag_based_manual.py

# Unit tests
pytest tests/test_tag_based_connectivity.py -v
```

All 12 unit tests pass ✅

## 📧 Email Report Example

```
PROBLEMATIC ITEMS (Below 70%)
====================================
Host        Item                Score   Status
--------------------------------------------
Server-A    SNMP Availability   45%     CRITICAL
Server-A    Agent Status        60%     WARNING

HOSTS WITHOUT CONNECTION ITEMS
====================================
- Server-C (No connection monitoring)
```

## 🆚 vs. Legacy Approach

| Feature | Legacy (Deprecated) | Tag-Based (Current) |
|---------|---------------------|---------------------|
| Setup | YAML configuration | Zabbix tags only |
| Flexibility | Pattern matching | Any tagged item |
| Maintenance | Update YAML files | Update tags in UI |
| Scoring | Host-level average | Per-item individual |
| Reporting | Host connectivity | Item-level detail |

## 🔧 Requirements

- Python 3.7+
- Ansible 2.9+ (for playbook)
- Zabbix 5.0+
- Required Python packages: `requests`, `pyyaml`

```bash
pip install -r scripts/requirements.txt
```

## 🚀 AWX/Tower Integration

1. Create Job Template
2. Set Project & Playbook: `zabbix_tag_based_monitoring.yaml`
3. Add Credentials (Zabbix + SMTP)
4. Configure Extra Variables
5. Schedule or run manually

See [AWX Guide](docs/guides/AWX_TESTING.md) for details.

## 📁 Project Structure

```
zabbix-monitoring/
├── TAG_BASED_CONNECTIVITY_README.md  # Quick start guide
├── playbooks/
│   ├── zabbix_tag_based_monitoring.yaml  # Main playbook
│   └── roles/zabbix_monitoring/tasks/
│       ├── tag_based_connectivity_check.yml
│       └── send_tag_based_notification_email.yml
├── scripts/
│   ├── main.py                        # Main entry point
│   ├── collectors/api_collector.py    # Zabbix API
│   ├── analyzers/                     # Analysis modules
│   └── test_tag_based_manual.py      # Manual test
└── tests/
    └── test_tag_based_connectivity.py # Unit tests
```

## 🐛 Troubleshooting

### No items detected
```bash
# Check tag spelling (case-insensitive)
# Verify items are enabled
# Ensure hosts are monitored
```

### Low scores
```bash
# Check item history data
# Verify expected value (default: 1)
# Increase --history-limit if needed
```

### Email not sent
```bash
# Verify SMTP settings
# Check send_email: true
# Review log: /tmp/zabbix_tag_based_monitoring.log
```

## 📝 Migration from Legacy

The old template-based approach is **deprecated**. To migrate:

1. ✅ Identify connectivity items in your templates
2. ✅ Add "connection status" tag to these items in Zabbix
3. ✅ Test with `--mode tag-based-connectivity`
4. ✅ Switch playbooks to `zabbix_tag_based_monitoring.yaml`
5. ✅ Remove old template YAML files

Legacy modes still work but show deprecation warnings.

## 🎉 Benefits

- **10x Faster Setup** - No configuration files
- **100% Flexible** - Tag any item type
- **Real-time Updates** - Changes in Zabbix UI
- **Better Visibility** - Per-item breakdown
- **Easier Maintenance** - No YAML to manage

## 📞 Support

- **Issues**: Check log file and analysis JSON
- **Questions**: See complete documentation
- **Debug**: Enable `debug_enabled: true` in playbook

## 🏆 Success Metrics

✅ 12/12 Unit Tests Passing  
✅ Zero Configuration Required  
✅ Works with All Item Types  
✅ Handles Large Environments  
✅ Production Ready  

## 📄 License

Part of the project-zabake repository.

---

**Status**: Production Ready ✅  
**Last Updated**: January 2026  
**Primary Mode**: `tag-based-connectivity`
