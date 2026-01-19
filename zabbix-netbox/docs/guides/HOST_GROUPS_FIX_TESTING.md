# Host Groups Fix - Testing Guide

## Overview

This guide provides manual testing procedures for the host groups fix that resolves the issue where device type and contact groups were being skipped during device processing.

## Bug Description

**Problem:** 
- Location filter "ICT11" olan cihazlar haricinde, sadece location (DC13 gibi) host group olarak ekleniyor
- Device type (örn: "Inspur M6") ve contact/sahiplik (örn: "SABANCI DX") grupları skip ediliyor

**Root Cause:**
- `zbx_group_map` was only initialized for the first device
- Subsequent devices with new group types couldn't add them because groups weren't in the map
- Only groups from the first device (typically location groups) were being added to subsequent devices

**Fix:**
- `zbx_group_map` is now updated for each device
- All unique groups (device type, location, contact) are properly identified and added
- Missing groups are created in Zabbix and added to the map dynamically

## Prerequisites

- Access to Netbox instance
- Access to Zabbix instance
- AWX/Ansible environment configured
- Test devices in Netbox with:
  - Different locations (e.g., DC11, DC13, ICT11)
  - Different device types (e.g., Inspur M6, HPE IPMI, Dell IPMI)
  - Different contact/ownership values (e.g., SABANCI DX, different custom_fields.Sahiplik)

## Test Scenarios

### Scenario 1: Multiple Devices with Different Device Types

**Purpose:** Verify that device type groups are added correctly for all devices

**Setup:**
1. Device 1: Location=DC13, Device Type=Lenovo IPMI, Contact=CONTACT_A
2. Device 2: Location=DC13, Device Type=Inspur M6, Contact=CONTACT_A
3. Device 3: Location=DC13, Device Type=HPE IPMI, Contact=CONTACT_B

**Expected Results:**
- Device 1 should have groups: ["Lenovo IPMI", "DC13", "CONTACT_A"]
- Device 2 should have groups: ["Inspur M6", "DC13", "CONTACT_A"]
- Device 3 should have groups: ["HPE IPMI", "DC13", "CONTACT_B"]

**Verification:**
```bash
# Check Zabbix host groups for each device
# In Zabbix UI: Configuration > Hosts > [device_name] > Groups

# Or via Zabbix API:
curl -X POST https://zabbix.example.com/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
      "output": ["hostid", "name"],
      "selectGroups": ["name"],
      "filter": {"host": ["device1_hostname"]}
    },
    "auth": "YOUR_AUTH_TOKEN",
    "id": 1
  }'
```

### Scenario 2: Multiple Devices with Different Contacts

**Purpose:** Verify that contact groups are added correctly for all devices

**Setup:**
1. Device 1: Location=DC14, Device Type=Inspur M6, Contact=SABANCI DX
2. Device 2: Location=DC14, Device Type=Inspur M6, Contact=BULUTISTAN
3. Device 3: Location=DC14, Device Type=Inspur M6, Contact=INTERNAL

**Expected Results:**
- Device 1 should have groups: ["Inspur M6", "DC14", "SABANCI DX"]
- Device 2 should have groups: ["Inspur M6", "DC14", "BULUTISTAN"]
- Device 3 should have groups: ["Inspur M6", "DC14", "INTERNAL"]

### Scenario 3: Location Filter ICT11

**Purpose:** Verify that ICT11 location filter works correctly

**Setup:**
1. Device 1: Location=ICT11, Device Type=Lenovo IPMI, Contact=CONTACT_A
2. Device 2: Location=DC13, Device Type=Inspur M6, Contact=CONTACT_B

**Expected Results:**
- Device 1 should be skipped or have specific handling for ICT11
- Device 2 should have groups: ["Inspur M6", "DC13", "CONTACT_B"]

### Scenario 4: Mixed Everything

**Purpose:** Verify comprehensive multi-device processing

**Setup:**
Process 5+ devices with various combinations:
- Different locations
- Different device types
- Different contacts
- Some with missing fields (no contact, etc.)

**Expected Results:**
- Each device should have its correct groups
- No group should be skipped
- Debug output should show proper group mapping for each device

## Running the Tests

### 1. Enable Debug Mode

Edit the playbook to ensure debug output is visible or set verbosity:

```bash
cd zabbix-netbox/playbooks
ansible-playbook netbox_zabbix_sync.yaml -i inventory/hosts.yml -vv
```

### 2. Review Debug Output

Look for the new debug messages in the output:

```
TASK [netbox_zabbix_sync : Debug - Show group mapping status] *****
ok: [localhost] => {
    "msg": "Host: device_name\nRequired groups: ['Inspur M6', 'DC13', 'SABANCI DX']\nGroups already in map: ['DC13']\nGroups to process: ['Inspur M6', 'SABANCI DX']\n"
}
```

**What to verify:**
- "Required groups" shows all expected groups (device type, location, contact)
- "Groups to process" shows groups not yet in the map
- For subsequent devices, "Groups already in map" should include previously processed groups

### 3. Verify in Zabbix UI

After playbook completes:

1. Navigate to: **Configuration > Hosts**
2. Select a test host
3. Check **Groups** tab
4. Verify all expected groups are present:
   - Device Type group (e.g., "Inspur M6")
   - Location group (e.g., "DC13")
   - Contact group (e.g., "SABANCI DX")

### 4. Check Host Group Creation

Verify that new groups were created in Zabbix:

1. Navigate to: **Configuration > Host groups**
2. Search for the new groups
3. Verify they exist and have correct names

## Expected Log Patterns

### Before Fix (Problematic):

```json
{
  "changed": false,
  "skip_reason": "Conditional result was False",
  "false_condition": "group_name is defined and group_name in zbx_group_map",
  "group_name": "Inspur M6"
}
```

### After Fix (Correct):

```json
{
  "ansible_facts": {
    "zbx_group_id_list": ["41", "52", "63"],
    "zbx_groups_formatted": [
      {"groupid": "41"},
      {"groupid": "52"},
      {"groupid": "63"}
    ]
  },
  "group_name": "Inspur M6"
}
```

## Troubleshooting

### Issue: Groups still being skipped

**Check:**
1. Is the fix properly deployed?
2. Is `zbx_group_map` being updated in debug output?
3. Are the group names correct in Netbox custom fields?

**Debug command:**
```bash
ansible-playbook netbox_zabbix_sync.yaml -vvv --tags debug
```

### Issue: Groups created but not assigned

**Check:**
1. Zabbix API permissions
2. Group creation success in logs
3. Map update step completion

### Issue: Duplicate groups

**Check:**
1. Group name consistency (case sensitivity)
2. Zabbix existing groups before playbook run

## Success Criteria

- [ ] All test scenarios pass
- [ ] Debug output shows correct group processing
- [ ] All devices have correct groups in Zabbix
- [ ] No "skip_reason" messages for valid groups
- [ ] New host groups created successfully in Zabbix
- [ ] `zbx_group_map` updates correctly for each device

## Rollback Procedure

If issues are found:

```bash
# Switch back to main branch
git checkout main

# Restore previous version
cd zabbix-netbox/playbooks/roles/netbox_zabbix_sync/tasks
git checkout main -- zabbix_host_operations.yml

# Re-run playbook
ansible-playbook netbox_zabbix_sync.yaml -i inventory/hosts.yml
```

## Notes

- Test with a small subset of devices first (device_limit: 5-10)
- Monitor Zabbix performance during bulk operations
- Keep backup of Zabbix database before large-scale testing
- Document any edge cases or unexpected behavior

## References

- Bug Report: See commit message in `bugfix/netbox-zabbix-host-groups-fix`
- Changes Summary: `zabbix-netbox/CHANGES_SUMMARY.md`
- Original Issue: Location filter ICT11 behavior analysis
