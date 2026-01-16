# Ansible Collections Installation Guide

## Required Collections

This project requires the following Ansible collections:

1. **community.general** - For email notifications and other utilities
2. **community.zabbix** - For Zabbix API interactions

## Installation Methods

### Method 1: Using requirements.yml (Recommended)

```bash
cd /Users/duosis-can/project-zabake/zabbix-migration
ansible-galaxy collection install -r requirements.yml
```

### Method 2: Manual Installation

```bash
ansible-galaxy collection install community.general
ansible-galaxy collection install community.zabbix
```

## Verification

Verify installed collections:

```bash
ansible-galaxy collection list | grep community
```

Expected output:
```
community.general    8.x.x
community.zabbix     2.x.x
```

## Troubleshooting

### Error: "couldn't resolve module/action 'community.general.mail'"

**Cause:** The `community.general` collection is not installed.

**Solution:**
```bash
ansible-galaxy collection install community.general
```

### Error: Collection installation fails

**Try with force flag:**
```bash
ansible-galaxy collection install -r requirements.yml --force
```

### Verify collection path

```bash
ansible-config dump | grep COLLECTIONS_PATHS
```

Default paths:
- `~/.ansible/collections`
- `/usr/share/ansible/collections`

## Notes

- Collections are installed per-user by default
- If running playbooks in containers/CI, collections must be installed in the container
- Email notifications will be skipped if `community.general` is not available (won't fail the playbook)



