# AWX Credential Inputs

Define these fields in a custom credential type and inject as env vars:

- `DATALAKE_DB_HOST`
- `DATALAKE_DB_PORT`
- `DATALAKE_DB_NAME`
- `DATALAKE_DB_USER`
- `DATALAKE_DB_PASSWORD`

Optional:
- `NETBOX_DB_*` when different than datalake
- `RECONCILIATION_DB_*` for result upsert database
