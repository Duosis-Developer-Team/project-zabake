## CSV Schema

Required headers (order fixed):
```
DEVICE_TYPE,HOSTNAME,HOST_IP,DC_ID,TEMPLATE_TYPE,MACROS
```

Notes:
- `MACROS` is optional; when present it must be a single field containing a JSON-like map or comma-delimited pairs. Supported formats:
  - JSON object: `{ "{MACRO1}": "VALUE1", "{MACRO2}": "VALUE2" }`
  - Pair list: `{MACRO1:VALUE1,MACRO2:VALUE2}` (no quotes)

Examples:
```
ROUTER,edge-rtr-01,10.0.0.1,DC01,snmp,{ {SNMP_COMMUNITY}:public,{SITE}:ANK }
SWITCH,sw-01,10.0.0.2,DC02,snmp,{ {SNMP_COMMUNITY}:core,{RACK}:R1 }
SERVER,app01,10.0.1.10,DC03,agent,
```

Validation rules:
- `HOST_IP` must be IPv4 or IPv6 literal
- `TEMPLATE_TYPE` in [snmp, agent, none]
- `DEVICE_TYPE`, `DC_ID` must exist in mappings


