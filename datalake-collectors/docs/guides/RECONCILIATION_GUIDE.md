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

When `dry_run: true`, diffs are written to `hmdl.collector_diff_log` and email; proxy `configuration_file.json` is not overwritten.

## Removal guard

When `removal_guard_enabled: true` (default), IPs that NetBox no longer lists but still pass ICMP/TCP checks are **not** removed. They appear in diffs as `removal_blocked` with reason `still_reachable` and in the email report under **Blocked removals**.

## Unknown sections

Sections not in `collector_types.yml` remain untouched when `reconcile_preserve_unknown_sections: true` (default).
