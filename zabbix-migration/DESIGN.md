## Zabbix Migration - Design

### Goal
Automate creation or update of Zabbix hosts from CSV input with flexible template assignment, proxy routing by DC, interface handling per template type, and host macro upsert.

### CSV Schema
Required columns:
- DEVICE_TYPE
- HOSTNAME
- HOST_IP
- DC_ID
- TEMPLATE_TYPE (e.g., snmp, agent, none)

Optional columns (0..N):
- Any `KEY:VALUE` macro pair in the trailing fields, e.g. `{MACRO1:VALUE1,MACRO2:VALUE2}` or expanded as `MACRO_NAME,MACRO_VALUE` pairs. See `SCHEMA.md` for exact encoding.

### Mappings
- DEVICE_TYPE → templates: `mappings/templates.yml`
- TEMPLATE_TYPE → interface spec: `mappings/template_types.yml`
- DC_ID → proxy/proxy_group: `mappings/datacenters.yml`

### Operations per CSV Row (Idempotent)
1. Resolve templates (union of DEVICE_TYPE templates and any overrides from TEMPLATE_TYPE)
2. Ensure host exists (`host.get` by name)
   - If not exists → `host.create`
   - If exists → `host.update`
3. Ensure interfaces
   - For SNMP: add one main SNMP interface with IP=`HOST_IP`, port `161`, set SNMPv2 or v3 per config (default v2)
4. Link templates (`host.massadd` or `template.get` + `host.update` with `templates`)
5. Upsert macros (`usermacro.create` or `usermacro.update`); if exists with different value, update
6. Assign proxy/proxy group based on `DC_ID`

### Idempotency & Safety
- Use lookups before create (host, templates, macros)
- Avoid duplicates: compare by name and interface tuple (type, ip, port)
- Dry-run support: Ansible `--check` and role variable `zbx_migration_dry_run: true`
- Error handling: fail fast on unknown `DEVICE_TYPE`, `TEMPLATE_TYPE` unless `allow_unknown: true`

### Structure
- `playbooks/zabbix_migration.yaml`: Entry playbook
- `roles/zabbix_migration/`: main tasks, lookups, API calls
- `library/zabbix_*.py`: optional custom modules if needed
- `mappings/*.yml`: config-only mapping files
- `examples/hosts.csv`: sample CSV

### Security
- Store Zabbix URL/user/password in Ansible Vault or env vars
- Never commit secrets; default variables left unset

### Open Questions
- SNMP v2 vs v3 defaults? Per-device override via CSV macro like `{SNMP_VER:3}`?
- Proxy assignment: proxyid or proxy group id? Will use proxy (preferred) if mapping provides `proxyid`; fallback to `proxy_groupid`.


