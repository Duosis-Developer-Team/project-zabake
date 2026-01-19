# Tag-Based Connectivity Monitoring

## 🎯 Quick Start

This feature allows you to monitor Zabbix host connectivity by simply tagging items, without any configuration files.

### 1. Tag Your Items in Zabbix

Add the `connection status` tag to any item that represents connectivity:

1. Go to **Configuration → Hosts**
2. Select a host → **Items**
3. Edit an item (e.g., "ICMP ping", "SNMP availability", "Agent status")
4. Add tag: **Name:** `connection status`, **Value:** *(leave empty)*
5. Save

### 2. Run the Check

#### Python Script
```bash
cd zabbix-monitoring/scripts
python3 main.py \
  --mode tag-based-connectivity \
  --zabbix-url "http://your-zabbix.com" \
  --zabbix-user "admin" \
  --zabbix-password "password" \
  --output-dir "./reports"
```

#### Ansible Playbook
```bash
cd zabbix-monitoring/playbooks
ansible-playbook zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=http://your-zabbix.com" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

### 3. Check Results

The script will:
- ✅ Detect all items with "connection status" tag
- ✅ Analyze last 10 values for each item
- ✅ Calculate connectivity score (percentage)
- ✅ Report items below 70% threshold
- ✅ Identify hosts without connection items
- ✅ Send email notification (if configured)

## 📊 Example Output

```
PROBLEMATIC ITEMS (Below 70% Threshold)
========================================
Host             Item                Score   Status
---------------------------------------------------------
Server-A         SNMP Availability   45%     CRITICAL
Server-A         Agent Status        60%     WARNING
Server-B         ICMP Ping           55%     WARNING

HOSTS WITHOUT CONNECTION ITEMS
========================================
- Server-C
- Server-D
```

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--connection-tag` | Tag name to identify connection items | "connection status" |
| `--history-limit` | Number of history values to analyze | 10 |
| `--threshold-percentage` | Minimum acceptable connectivity % | 70.0 |
| `--host-groups` | Filter by host groups (comma-separated) | All hosts |

## 📧 Email Notifications

Configure email settings:

```yaml
# Ansible variables
smtp_server: "smtp.example.com"
smtp_port: 25
email_from: "zabbix@example.com"
email_to: "admin@example.com"
```

Or environment variables:
```bash
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT=25
export EMAIL_FROM="zabbix@example.com"
export EMAIL_TO="admin@example.com"
```

## 🧪 Testing

### Manual Test (No Zabbix Required)
```bash
cd zabbix-monitoring/scripts
python3 test_tag_based_manual.py
```

### Unit Tests
```bash
cd zabbix-monitoring
pytest tests/test_tag_based_connectivity.py -v
```

## 📚 Documentation

- [Complete Feature Documentation](docs/development/TAG_BASED_CONNECTIVITY_FEATURE.md)
- [Architecture](docs/design/ARCHITECTURE.md)
- [Email Notification Guide](docs/guides/EMAIL_NOTIFICATION_GUIDE.md)
- [AWX Testing Guide](docs/guides/AWX_TESTING.md)

## 🆚 vs. Old Template-Based Approach

| Feature | Old Approach | New Approach |
|---------|--------------|--------------|
| Configuration | Required YAML file | No configuration |
| Flexibility | Pattern matching only | Any tagged item |
| Maintenance | Update YAML on changes | Update tags in Zabbix |
| Scoring | Host-level average | Per-item individual |
| Reporting | Host connectivity | Per-item breakdown |

## 🚀 AWX Integration

1. Create Job Template
2. Set inventory and playbook: `zabbix_tag_based_monitoring.yaml`
3. Add Extra Variables:
```yaml
zabbix_url: "http://zabbix.example.com"
zabbix_user: "admin"
zabbix_password: "{{ vault_zabbix_password }}"
send_email: true
email_to: "team@example.com"
```
4. Schedule or run manually

## 🎯 Use Cases

### Use Case 1: SNMP Device Monitoring
Tag these items with "connection status":
- SNMP availability
- SNMP agent ping
- Interface status checks

### Use Case 2: Server Monitoring
Tag these items:
- ICMP ping
- Zabbix agent availability
- SSH service status

### Use Case 3: Network Device Monitoring
Tag these items:
- ICMP ping
- SNMP availability
- BGP session status

## 🐛 Troubleshooting

### No items detected
- Verify tag spelling: "connection status" (case-insensitive)
- Check items are enabled (status = 0)
- Ensure items belong to monitored hosts

### Score always 0%
- Verify items have history data
- Check expected value (default: 1 = success)
- Increase `--history-limit` if needed

### Email not sent
- Verify SMTP settings
- Check `send_email: true`
- Review log file for errors

## 📞 Support

For issues or questions:
1. Check log file: `/tmp/zabbix_tag_based_monitoring.log`
2. Review analysis results: `reports/tag_based_connectivity_analysis.json`
3. Enable debug: `debug_enabled: true`

## 🎉 Benefits

✅ **Zero Configuration** - Just tag items in Zabbix  
✅ **Flexible** - Works with any item type  
✅ **Per-Item Analysis** - Individual scoring  
✅ **Easy Maintenance** - Manage via Zabbix UI  
✅ **Scalable** - Handles large environments  
✅ **Comprehensive** - Detailed reports  
✅ **Missing Item Detection** - Finds unmonitored hosts  

## 📝 License

Part of the project-zabake repository.

## 👥 Contributing

See project contributing guidelines.
