# Legacy Tasks (Deprecated)

⚠️ **These tasks are deprecated and will be removed in June 2026**

## Migration Required

Use the new tag-based approach instead:
- **New Playbook**: `../../zabbix_tag_based_monitoring.yaml`
- **New Tasks**: `tag_based_connectivity_check.yml`, `send_tag_based_notification_email.yml`

## Legacy Tasks in This Folder

These tasks implement the old template-based approach:

1. `validate_config.yml` - Config validation
2. `collect_data.yml` - Data collection
3. `analyze_templates.yml` - Template analysis
4. `detect_connectivity.yml` - Connectivity detection
5. `analyze_data.yml` - Data analysis
6. `check_master_items.yml` - Master item checking
7. `generate_report.yml` - Report generation

## Why Deprecated?

- ❌ Required YAML configuration files
- ❌ Pattern matching for item detection
- ❌ Complex setup and maintenance
- ❌ Not flexible across environments

## New Approach

- ✅ Zero configuration - just tag items
- ✅ Flexible - works with any item
- ✅ Easy maintenance via Zabbix UI
- ✅ Per-item analysis and reporting

## Migration Guide

See [LEGACY_DEPRECATION.md](../../../../LEGACY_DEPRECATION.md) for complete migration instructions.

---

**Deprecated**: January 2026  
**Removal Date**: June 2026
