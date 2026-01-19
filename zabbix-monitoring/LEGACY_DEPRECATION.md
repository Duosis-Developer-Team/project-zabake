# Legacy Mode Deprecation Notice

## ⚠️ Important: Template-Based Modes Are Deprecated

The following modes are **deprecated** and will be removed in a future release:

- `collect`
- `analyze-templates`
- `detect-connectivity`
- `analyze-data`
- `check-master-items`
- `generate-report`

## ✅ Use Tag-Based Mode Instead

The new `tag-based-connectivity` mode is the **only supported** approach going forward.

### Why the Change?

| Old Approach | Problem |
|--------------|---------|
| YAML configuration required | Manual maintenance burden |
| Pattern matching for items | Breaks when item names change |
| Template-specific logic | Not flexible across environments |
| Complex setup | High barrier to entry |

### New Approach Benefits

| Tag-Based Mode | Benefit |
|----------------|---------|
| Just tag items in Zabbix | Zero configuration |
| Works with any item | Complete flexibility |
| Manage via Zabbix UI | Easy maintenance |
| Per-item analysis | Better visibility |

## 🔄 Migration Guide

### Step 1: Identify Current Items

If you're using the old approach, you have template mappings like:

```yaml
# OLD: mappings/templates.yml
templates:
  - name: "Template Server SNMP"
    connection_check_items:
      - key: "icmpping"
        name: "ICMP Ping"
        required: true
```

### Step 2: Tag Items in Zabbix

For each connectivity item in your templates:

1. Go to **Configuration → Hosts**
2. Select host → **Items**
3. Find the connectivity item (e.g., "ICMP Ping")
4. Edit item → **Tags**
5. Add tag: **Name:** `connection status`, **Value:** *(leave empty)*
6. Save

Repeat for all connectivity items across all hosts.

### Step 3: Update Playbooks

**Old Playbook:**
```yaml
# OLD: zabbix_monitoring_check.yaml
- name: "Detect connectivity items"
  include_role:
    name: zabbix_monitoring
    tasks_from: detect_connectivity.yml
```

**New Playbook:**
```yaml
# NEW: zabbix_tag_based_monitoring.yaml
- name: "Run tag-based connectivity check"
  include_role:
    name: zabbix_monitoring
    tasks_from: tag_based_connectivity_check.yml
```

### Step 4: Update AWX Job Templates

**Old Job Template:**
- Playbook: `zabbix_monitoring_check.yaml`
- Mode: `detect-connectivity`

**New Job Template:**
- Playbook: `zabbix_tag_based_monitoring.yaml`
- Mode: `tag-based-connectivity`

### Step 5: Test

```bash
# Test with new mode
ansible-playbook zabbix_tag_based_monitoring.yaml \
  -e "zabbix_url=http://zabbix.example.com" \
  -e "zabbix_user=admin" \
  -e "zabbix_password=password"
```

Verify:
- ✅ All expected items are detected
- ✅ Scores are calculated correctly
- ✅ Email notifications work
- ✅ Hosts without items are listed

### Step 6: Clean Up

Once migration is complete:

1. Delete old template YAML files:
   ```bash
   rm mappings/templates.yml
   ```

2. Remove old playbook references

3. Update documentation

## 📊 Comparison

### Detection Logic

**Old:**
```python
# Pattern matching from YAML
for template in templates:
    for item_config in template.connection_check_items:
        if item.key matches item_config.key:
            # Found connectivity item
```

**New:**
```python
# Tag-based detection
for item in all_items:
    if item has tag "connection status":
        # Found connectivity item
```

### Scoring Logic

**Old:**
```python
# Host-level weighted average
host_score = sum(item_score * weight) / total_weight
```

**New:**
```python
# Per-item individual scoring
item_score = successful_checks / total_checks * 100
```

### Maintenance

**Old:**
```yaml
# Edit YAML file
templates:
  - name: "New Template"
    connection_check_items:
      - key: "new.item"
        name: "New Item"
# Commit, push, deploy
```

**New:**
```
1. Open Zabbix UI
2. Go to item
3. Add "connection status" tag
4. Done!
```

## ⏰ Timeline

| Date | Action |
|------|--------|
| January 2026 | Tag-based mode released |
| January 2026 | Legacy modes marked deprecated |
| March 2026 | Warning messages added |
| June 2026 | Legacy modes removed |

## 🆘 Need Help?

### Still Using Legacy Mode?

If you see this warning:

```
⚠️  Mode 'detect-connectivity' is DEPRECATED
⚠️  Please use 'tag-based-connectivity' mode instead
⚠️  See TAG_BASED_CONNECTIVITY_README.md for migration guide
```

**Action Required:** Follow this migration guide.

### Migration Issues?

1. Check [Quick Start Guide](TAG_BASED_CONNECTIVITY_README.md)
2. Review [Complete Documentation](docs/development/TAG_BASED_CONNECTIVITY_FEATURE.md)
3. Test with [Manual Test Script](scripts/test_tag_based_manual.py)

### Questions?

- Review log file: `/tmp/zabbix_tag_based_monitoring.log`
- Check analysis output: `reports/tag_based_connectivity_analysis.json`
- Enable debug: `debug_enabled: true`

## ✅ Migration Checklist

- [ ] Identified all connectivity items in templates
- [ ] Tagged items in Zabbix with "connection status"
- [ ] Updated playbooks to use `zabbix_tag_based_monitoring.yaml`
- [ ] Updated AWX job templates
- [ ] Tested new mode in dev/staging
- [ ] Verified email notifications
- [ ] Deployed to production
- [ ] Removed old template YAML files
- [ ] Updated documentation

## 🎯 Why This Is Better

1. **Zero Config** - No YAML files to maintain
2. **Flexible** - Tag any item type
3. **Easy Maintenance** - Change tags in Zabbix UI
4. **Better Reports** - Per-item breakdown
5. **Scalable** - No configuration overhead

## 📝 Summary

**Old Way:** Configure templates → Match items → Calculate scores → Report  
**New Way:** Tag items → Detect items → Calculate scores → Report

**Result:** 90% less configuration, 100% more flexible! 🎉

---

**Status**: Legacy modes deprecated as of January 2026  
**Removal Date**: June 2026  
**Migration Required**: Yes
