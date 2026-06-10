# Reconciliation Guide

## Smart merge

For each **NetBox-managed** section, only the configured `ip_field` (and computed `secondary_fields` like `IBM-Virtualize.link`) are updated.

- **added** — IP in NetBox mapping, not in current config
- **removed** — IP in current config, no longer in NetBox
- **preserved** — IP unchanged

Non-IP keys in the section (ports, paths, usernames from vault) are merged from vault without deleting unknown keys in the current file.

## Manual-only sections

`Zabbix`, `Loki`, `ServiceCore`, `Dynamics365`, `Netbackup_old` are refreshed from vault `defaults.yml` but **IP fields are not managed** by NetBox reconcile.

## dry_run

When `dry_run: true`, diffs are written to `hmdl.collector_diff_log` and email; proxy `configuration_file.json` is not overwritten. AWX stdout notes whether each proxy **would update** or **skip deploy (unchanged)**.

## Backup before deploy

When `dry_run: false` and reconciled JSON differs from the current file on the NiFi node:

1. Copy existing `configuration_file.json` to `configuration_file.json.bak.<run_id>` on the same host (`cp -a`).
2. Write reconciled JSON to `configuration_file.json`.

Skipped when config is unchanged, file does not exist yet (greenfield), or `backup_config_before_deploy: false`.

## Removal guard

When `removal_guard_enabled: true` (default), IPs that NetBox no longer lists but still pass ICMP/TCP checks are **not** removed. They appear in diffs as `removal_blocked` with reason `still_reachable` and in the email report under **Blocked removals**.

## Unknown sections

Sections not in `collector_types.yml` remain untouched when `reconcile_preserve_unknown_sections: true` (default).
