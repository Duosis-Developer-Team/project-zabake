# AWX Setup Guide for Tag-Based Connectivity Monitoring

## 📋 Overview

This guide explains how to set up the Zabbix Tag-Based Connectivity Monitoring playbook in AWX/Tower.

## 🚀 Quick Setup

### 1. Create Project

**Navigation:** AWX → Projects → Add

- **Name:** `Zabbix Monitoring`
- **SCM Type:** `Git`
- **SCM URL:** Your repository URL
- **SCM Branch/Tag/Commit:** `development` or `main`
- **SCM Update Options:** 
  - ✅ Clean
  - ✅ Update Revision on Launch

**Save**

### 2. Create Credentials

#### Zabbix Credentials

**Navigation:** AWX → Credentials → Add

**Option 1: Custom Credential Type**

Create custom credential type for Zabbix:

```yaml
# Input Configuration
fields:
  - id: zabbix_url
    type: string
    label: Zabbix URL
  - id: zabbix_user
    type: string
    label: Zabbix Username
  - id: zabbix_password
    type: string
    label: Zabbix Password
    secret: true

# Injector Configuration
extra_vars:
  zabbix_url: '{{ zabbix_url }}'
  zabbix_user: '{{ zabbix_user }}'
  zabbix_password: '{{ zabbix_password }}'
```

**Option 2: Machine Credential (Simpler)**

Use standard Machine credential and pass via Extra Variables.

#### SMTP Credentials (Optional)

If SMTP requires authentication:

```yaml
fields:
  - id: smtp_username
    type: string
    label: SMTP Username
  - id: smtp_password
    type: string
    label: SMTP Password
    secret: true
    
extra_vars:
  smtp_username: '{{ smtp_username }}'
  smtp_password: '{{ smtp_password }}'
```

### 3. Create Job Template

**Navigation:** AWX → Templates → Add Job Template

#### Basic Settings

- **Name:** `Zabbix Tag-Based Connectivity Check`
- **Job Type:** `Run`
- **Inventory:** `localhost` or any inventory with localhost
- **Project:** `Zabbix Monitoring`
- **Playbook:** `zabbix-monitoring/playbooks/zabbix_tag_based_monitoring.yaml`
- **Credentials:** Select your Zabbix credential

#### Extra Variables

```yaml
# Required
zabbix_url: "http://zabbix.example.com/api_jsonrpc.php"
zabbix_user: "Admin"
zabbix_password: "{{ vault_zabbix_password }}"  # or use credential

# Email Settings
smtp_server: "smtp.company.com"
smtp_port: 587
email_from: "zabbix-monitoring@company.com"
email_to: "team@company.com"  # or "user1@company.com,user2@company.com"

# Optional: SMTP Authentication
smtp_username: "notifications@company.com"
smtp_password: "{{ vault_smtp_password }}"

# Optional: Monitoring Settings
connection_tag: "connection status"
history_limit: 10
threshold_percentage: 70.0
host_groups: ""  # Empty for all hosts, or "Linux servers,Network devices"

# Optional: Debug
debug_enabled: false
debug_output_dir: "/tmp/zabbix_monitoring_output"
log_level: "INFO"
```

#### Options

- ✅ **Prompt on Launch** (for Extra Variables) - Allow runtime configuration
- ✅ **Enable Concurrent Jobs** - If you want multiple runs
- ⬜ **Enable Privilege Escalation** - Not needed (runs on localhost)

**Save**

### 4. Create Survey (Optional but Recommended)

Add survey to make it user-friendly:

#### Survey Questions

1. **Zabbix URL**
   - Type: `Text`
   - Variable: `zabbix_url`
   - Default: `http://zabbix.example.com/api_jsonrpc.php`
   - Required: ✅

2. **Email Recipients**
   - Type: `Text`
   - Variable: `email_to`
   - Default: `admin@company.com`
   - Required: ✅
   - Help Text: `Comma-separated email addresses`

3. **Host Groups Filter**
   - Type: `Text`
   - Variable: `host_groups`
   - Default: `` (empty for all)
   - Required: ⬜
   - Help Text: `Comma-separated host group names, empty for all hosts`

4. **Threshold Percentage**
   - Type: `Integer`
   - Variable: `threshold_percentage`
   - Default: `70`
   - Min: `1`
   - Max: `100`
   - Required: ✅

5. **History Limit**
   - Type: `Integer`
   - Variable: `history_limit`
   - Default: `10`
   - Min: `5`
   - Max: `50`
   - Required: ✅

6. **Enable Email**
   - Type: `Multiple Choice (single select)`
   - Variable: `send_email`
   - Choices: `true\nfalse`
   - Default: `true`

### 5. Schedule (Optional)

**Navigation:** AWX → Schedules → Add

- **Name:** `Daily Connectivity Check`
- **Job Template:** `Zabbix Tag-Based Connectivity Check`
- **Frequency:** Daily at 09:00
- **Time Zone:** Your timezone

**Save**

## 📊 Example Extra Variables

### Minimal Configuration

```yaml
zabbix_url: "http://10.134.16.235/api_jsonrpc.php"
zabbix_user: "Admin"
zabbix_password: "zabbix"
smtp_server: "localhost"
email_to: "admin@example.com"
```

### Full Configuration

```yaml
# Zabbix Connection
zabbix_url: "http://zabbix.company.com/api_jsonrpc.php"
zabbix_user: "monitoring_user"
zabbix_password: "{{ vault_zabbix_pass }}"

# Monitoring Settings
connection_tag: "connection status"
history_limit: 10
threshold_percentage: 70.0
host_groups: "Production Servers,Network Devices"

# Email Settings
send_email: true
smtp_server: "smtp.office365.com"
smtp_port: 587
smtp_username: "notifications@company.com"
smtp_password: "{{ vault_smtp_pass }}"
email_from: "zabbix-monitoring@company.com"
email_to: "ops-team@company.com,manager@company.com"

# Debug Settings
debug_enabled: false
debug_output_dir: "/tmp/zabbix_monitoring"
log_level: "INFO"
log_file: "/tmp/zabbix_monitoring.log"
```

## 🔐 Using AWX Credentials

### Method 1: Custom Credential Type (Recommended)

1. Create custom credential type (see above)
2. Create credential with Zabbix details
3. Attach to job template
4. Variables automatically injected

### Method 2: Ansible Vault in Extra Variables

```yaml
zabbix_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66386439653765653765653765653765...
```

### Method 3: AWX Vault Password

Store in AWX and reference:
```yaml
zabbix_password: "{{ vault_zabbix_password }}"
```

## 🧪 Testing

### Test Run

1. Go to **Templates** → Select your template
2. Click **Launch** 🚀
3. Fill survey if enabled
4. Wait for job to complete
5. Check **Output** tab for results
6. Verify email received

### Common Test Scenarios

```yaml
# Test 1: Single host group
host_groups: "Linux servers"

# Test 2: Multiple recipients
email_to: "admin@example.com,ops@example.com"

# Test 3: Higher threshold (more sensitive)
threshold_percentage: 80.0

# Test 4: More history data
history_limit: 20

# Test 5: Debug mode
debug_enabled: true
```

## 📧 Email Configuration

### Gmail

```yaml
smtp_server: "smtp.gmail.com"
smtp_port: 587
smtp_username: "your-email@gmail.com"
smtp_password: "app-specific-password"
email_from: "your-email@gmail.com"
```

### Office 365

```yaml
smtp_server: "smtp.office365.com"
smtp_port: 587
smtp_username: "user@company.com"
smtp_password: "password"
email_from: "user@company.com"
```

### Internal SMTP (No Auth)

```yaml
smtp_server: "mail.internal.local"
smtp_port: 25
email_from: "zabbix@company.com"
```

## 🐛 Troubleshooting

### Job Fails: "Zabbix connection parameters must be set"

**Solution:** Ensure `zabbix_url`, `zabbix_user`, `zabbix_password` are set in Extra Variables or Credentials.

### No Email Received

**Check:**
1. `send_email: true` is set
2. SMTP server is accessible from AWX
3. Email addresses are valid
4. Check job output for email sending status
5. Verify SMTP credentials if required

### "No items detected"

**Solution:**
1. Verify items have `connection status` tag in Zabbix
2. Check tag spelling (case-insensitive)
3. Ensure items are enabled
4. Verify host groups filter is correct

### "Failed to send email: Connection refused"

**Solution:**
1. Check SMTP server address and port
2. Verify network connectivity from AWX
3. Check firewall rules
4. Try port 25, 587, or 465

### "Permission denied" for output directory

**Solution:**
```yaml
debug_output_dir: "/tmp/zabbix_monitoring_output"
```

## 📝 Best Practices

### 1. Use Credentials

✅ Store sensitive data in AWX Credentials
❌ Don't hardcode passwords in Extra Variables

### 2. Use Survey for User Input

✅ Makes it easy for users
✅ Validates input
✅ Provides defaults

### 3. Schedule Regular Checks

✅ Daily or weekly monitoring
✅ Off-peak hours (e.g., 6 AM)
✅ After maintenance windows

### 4. Multiple Email Recipients

```yaml
email_to: "ops@company.com,manager@company.com,team@company.com"
```

### 5. Use Descriptive Names

```yaml
# Good
Template Name: "Prod - Zabbix Connectivity Check - Daily"

# Bad
Template Name: "zabbix check"
```

## 🎯 Advanced Configuration

### Filter Specific Host Groups

```yaml
host_groups: "Production Servers,Critical Infrastructure"
```

### Higher Sensitivity

```yaml
threshold_percentage: 90.0  # More strict
history_limit: 20  # More data points
```

### Custom Tag Name

```yaml
connection_tag: "availability"  # or "monitoring" or "health check"
```

### Multiple Notifications

Create separate job templates for different teams:

**Template 1: Linux Team**
```yaml
host_groups: "Linux servers"
email_to: "linux-team@company.com"
```

**Template 2: Network Team**
```yaml
host_groups: "Network devices"
email_to: "network-team@company.com"
```

## 📊 Monitoring Results

### Check Job Output

```
TASK [Display email notification status]
============================================
📊 Analysis Summary:
- Total Hosts: 150
- Hosts with Issues: 5
- Items Below Threshold: 8

✅ Email sent successfully to: team@company.com
Method: Python SMTP
============================================
```

### Review Analysis File

```bash
# On AWX execution node
cat /tmp/zabbix_monitoring_output/tag_based_connectivity_analysis.json
```

### Email Report

Check email for:
- Summary statistics
- Problematic items table
- Hosts without connection items
- Detailed per-item breakdown

## 🆘 Support

- **Logs:** `/tmp/zabbix_monitoring.log`
- **Output:** `/tmp/zabbix_monitoring_output/`
- **Documentation:** See project README files
- **Debug Mode:** Set `debug_enabled: true`

---

**Status:** Production Ready ✅  
**Last Updated:** January 2026  
**AWX Version:** 19.0+
