-- Migration: align existing hmdl.* tables with smart-merge / datalake-source audit model.
-- Safe to run multiple times (IF NOT EXISTS).
-- Target: databases that already have the three tables from an earlier deployment.

CREATE SCHEMA IF NOT EXISTS hmdl;

-- ─── zabbix_sync_log ───────────────────────────────────────────────────────────

ALTER TABLE hmdl.zabbix_sync_log
    ADD COLUMN IF NOT EXISTS host_entity_type VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS inventory_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS last_visible_name TEXT NULL,
    ADD COLUMN IF NOT EXISTS last_location TEXT NULL,
    ADD COLUMN IF NOT EXISTS expected_proxy_group_id TEXT NULL,
    ADD COLUMN IF NOT EXISTS last_proxy_group_id TEXT NULL,
    ADD COLUMN IF NOT EXISTS zabbix_proxy_group_id TEXT NULL,
    ADD COLUMN IF NOT EXISTS proxy_location_change BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS proxy_manual_change_detected BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS field_merge_actions JSONB NULL,
    ADD COLUMN IF NOT EXISTS last_managed_groups JSONB NULL,
    ADD COLUMN IF NOT EXISTS dry_run BOOLEAN DEFAULT FALSE;

-- Backfill last_location from root_location_name where missing
UPDATE hmdl.zabbix_sync_log
SET last_location = root_location_name
WHERE last_location IS NULL
  AND root_location_name IS NOT NULL;

-- Backfill proxy ids from extra_data when present (legacy rows)
UPDATE hmdl.zabbix_sync_log
SET last_proxy_group_id = COALESCE(
        last_proxy_group_id,
        extra_data->>'last_proxy_group_id',
        extra_data->>'proxy_group_id'
    ),
    last_visible_name = COALESCE(
        last_visible_name,
        extra_data->>'last_visible_name',
        zabbix_hostname
    )
WHERE extra_data IS NOT NULL
  AND (
      last_proxy_group_id IS NULL
      OR last_visible_name IS NULL
  );

CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_host_entity_type
    ON hmdl.zabbix_sync_log (host_entity_type);

CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_proxy_manual
    ON hmdl.zabbix_sync_log (proxy_manual_change_detected)
    WHERE proxy_manual_change_detected = TRUE;

CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_device_baseline
    ON hmdl.zabbix_sync_log (source_device_id, processed_at DESC NULLS LAST)
    WHERE status IN ('eklendi', 'güncellendi', 'güncel', 'dry_run');

-- ─── zabbix_host_update_log ────────────────────────────────────────────────────

ALTER TABLE hmdl.zabbix_host_update_log
    ADD COLUMN IF NOT EXISTS host_entity_type VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS inventory_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS merge_result VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS dry_run BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_run_id
    ON hmdl.zabbix_host_update_log (run_id);

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_source_device_id
    ON hmdl.zabbix_host_update_log (source_device_id);

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_field_name
    ON hmdl.zabbix_host_update_log (field_name);

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_processed_at
    ON hmdl.zabbix_host_update_log (processed_at DESC);

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_merge_manual
    ON hmdl.zabbix_host_update_log (merge_result)
    WHERE merge_result = 'preserved_manual';

-- ─── zabbix_tag_update_log ─────────────────────────────────────────────────────

ALTER TABLE hmdl.zabbix_tag_update_log
    ADD COLUMN IF NOT EXISTS host_entity_type VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS inventory_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS merge_result VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS dry_run BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_run_id
    ON hmdl.zabbix_tag_update_log (run_id);

CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_source_device_id
    ON hmdl.zabbix_tag_update_log (source_device_id);

CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_object_type
    ON hmdl.zabbix_tag_update_log (object_type);

CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_processed_at
    ON hmdl.zabbix_tag_update_log (processed_at DESC);
