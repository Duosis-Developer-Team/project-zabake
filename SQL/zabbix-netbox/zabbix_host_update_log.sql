-- HMDL: per-field host updates during Zabbix host.update (IP, proxy, visible name, groups, …).
-- Playbook: hmdl_update_log.yml

CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.zabbix_host_update_log (
    id                 BIGSERIAL PRIMARY KEY,
    run_id             VARCHAR(100) NULL,
    awx_job_id         VARCHAR(100) NULL,

    source_device_id   BIGINT NULL,
    source_device_name TEXT NULL,
    host_entity_type   VARCHAR(30) NULL,
    inventory_source   VARCHAR(20) NULL,

    zabbix_hostid      TEXT NULL,
    zabbix_hostname    TEXT NULL,

    field_name         TEXT NOT NULL,
    old_value          TEXT NULL,
    new_value          TEXT NULL,
    action             VARCHAR(50) NOT NULL,   -- updated | added | removed
    merge_result       VARCHAR(50) NULL,       -- updated | preserved_manual | skipped | no_change
    status             VARCHAR(50) NOT NULL,   -- updated | dry_run | failed | unknown
    reason             TEXT NULL,
    dry_run            BOOLEAN DEFAULT FALSE NOT NULL,

    processed_at       TIMESTAMPTZ DEFAULT NOW() NULL
);

COMMENT ON TABLE hmdl.zabbix_host_update_log IS
    'Field-level audit for host.update; one row per changed attribute.';
COMMENT ON COLUMN hmdl.zabbix_host_update_log.field_name IS
    'Examples: interface_ip, proxy_group, visible_name, host_groups, monitored_by.';
COMMENT ON COLUMN hmdl.zabbix_host_update_log.merge_result IS
    'Smart merge outcome when automation chose not to overwrite manual Zabbix values.';

CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_run_id
    ON hmdl.zabbix_host_update_log (run_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_source_device_id
    ON hmdl.zabbix_host_update_log (source_device_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_zabbix_hostid
    ON hmdl.zabbix_host_update_log (zabbix_hostid);
CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_field_name
    ON hmdl.zabbix_host_update_log (field_name);
CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_processed_at
    ON hmdl.zabbix_host_update_log (processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_zabbix_host_update_log_merge_manual
    ON hmdl.zabbix_host_update_log (merge_result)
    WHERE merge_result = 'preserved_manual';
