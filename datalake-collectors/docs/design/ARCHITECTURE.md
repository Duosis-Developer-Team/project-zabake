# Architecture — datalake-collectors

```mermaid
flowchart TB
  NB[NetBox API]
  MAP[YAML mappings Gitea/Git]
  VAULT[Gitea vault repo]
  AWX[AWX Job]
  DB[(hmdl Postgres)]
  PROXY[Proxy NiFi configuration_file.json]

  AWX --> NB
  AWX --> MAP
  AWX --> VAULT
  AWX --> DB
  AWX --> PROXY
```

## Components

- **datalake-collectors** Ansible role — orchestration
- **collector_core.py** — mapping and reconcile logic
- **HMDL tables** — inventory and audit
- **NiFi** — consumes unchanged JSON key names and comma-separated IP strings
