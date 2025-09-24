## Zabbix Migration - Overview

This module automates migrating hosts into Zabbix from a CSV file. For each CSV row, it will:
- Create or update the host
- Apply templates based on `DEVICE_TYPE` and `TEMPLATE_TYPE`
- Assign the host to a proxy/proxy group inferred from `DC_ID`
- Ensure optional host-level macros exist with provided values

### High-level Flow
1. Parse CSV with columns: `DEVICE_TYPE,HOSTNAME,HOST_IP,DC_ID,TEMPLATE_TYPE,{MACRO1:VALUE1,MACRO2:VALUE2,...}`
2. Resolve mappings:
   - DEVICE_TYPE → template ids/names (default set per type)
   - TEMPLATE_TYPE → interface requirements (e.g., SNMP)
   - DC_ID → proxy_groupid or proxyid
3. For each row:
   - Create/ensure host with name and technical host name
   - Create/ensure interface(s) according to template type
   - Link templates
   - Upsert macros
   - Set proxy/proxy group

### Components
- Ansible playbook(s) under `playbooks/`
- Ansible role `roles/zabbix_migration/`
- Mapping files under `mappings/`
- Example CSV under `examples/`

See `DESIGN.md` for detailed behavior and idempotency rules.


