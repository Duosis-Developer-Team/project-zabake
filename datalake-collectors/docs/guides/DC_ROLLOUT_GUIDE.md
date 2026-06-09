# DC Rollout Guide — datalake-collectors

Operational steps to expand platform sync beyond the DC13 pilot.

## Prerequisites

1. [proxy_assignment.yml](../../mappings/proxy_assignment.yml) uses the **multi-NiFi** schema (`proxies:` list per DC).
2. Each `proxy_nifi_host` matches an **AWX inventory** hostname (not only IP).
3. Gitea private repo `datalake-collectors-vault` is populated (see [VAULT_REPO_GUIDE.md](VAULT_REPO_GUIDE.md)).
4. HMDL SQL schema applied on the discovery PostgreSQL instance.

## Readiness check

From the repo root:

```bash
cd project-zabake/datalake-collectors
python3 scripts/verify_proxy_rollout.py
python3 scripts/verify_proxy_rollout.py --dc-filter DC16
```

Exit code `0` means no `REPLACE_*` hosts remain for the filtered scope.

## AWX job variables (per DC)

```yaml
sync_platforms: true
sync_devices: false
dry_run: true          # first pass
proxy_filter: "DC16"   # dc_code from proxy_assignment
removal_guard_enabled: true
run_basic_checks: true
deploy_scripts: false  # set true after config reconcile is stable

gitea_vault_url: "http://10.134.16.135:3000/<org>/datalake-collectors-vault.git"
# ... discovery_db_*, netbox_*, mail_recipients as in AWX_KULLANIM_REHBERI.md
```

## Dual NiFi consistency

Each NetBox platform target is fan-out to **every** proxy id under the DC (`resolve_proxy_ids`). The AWX job reconciles and (when `dry_run: false`) deploys the same `configuration_file.json` to each node.

After prod deploy, compare config hashes on both nodes:

```bash
ssh dc16-nifi-1 md5sum /Datalake_Project/configuration_file.json
ssh dc16-nifi-2 md5sum /Datalake_Project/configuration_file.json
```

## Removal guard behaviour

Before removing an IP from NetBox-managed sections, the job runs ICMP + TCP checks. If the target is still reachable (`status: ok`), the IP stays in config and appears in the email **Blocked removals** section and `hmdl.collector_diff_log` with action `removal_blocked`.

## Recommended rollout order

1. **DC16** — DR / second production site (two NiFi nodes)
2. **MAIN** — central proxy pair
3. Remaining DC codes — add rows to `proxy_assignment.yml` using the same schema

## Collector script deployment

Set `deploy_scripts: true` with `dry_run: false` to rsync platform collector directories from the AWX project checkout (`datalake/collectors/`) to `/Datalake_Project/<CollectorDir>/` on each proxy.

Supported types (default): VmWare, Nutanix, IBM-HMC, IBM-Virtualize, Veeam.

## Audit queries

```sql
SELECT * FROM hmdl.collector_sync_log ORDER BY started_at DESC LIMIT 20;
SELECT * FROM hmdl.collector_diff_log WHERE action = 'removal_blocked' ORDER BY created_at DESC LIMIT 50;
SELECT * FROM hmdl.collector_check_log WHERE check_phase = 'pre_reconcile' ORDER BY checked_at DESC LIMIT 50;
```
