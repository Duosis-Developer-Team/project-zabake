-- HMDL: per-tag and per-macro changes during Zabbix host.update.
-- Playbook: hmdl_update_log.yml (object_type: tag | macro)

CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.zabbix_tag_update_log (
    id                 BIGSERIAL PRIMARY KEY,
    run_id             VARCHAR(100) NULL,
    awx_job_id         VARCHAR(100) NULL,

    source_device_id   BIGINT NULL,
    source_device_name TEXT NULL,
    host_entity_type   VARCHAR(30) NULL,
    inventory_source   VARCHAR(20) NULL,

    zabbix_hostid      TEXT NULL,
    zabbix_hostname    TEXT NULL,

    object_type        VARCHAR(50) NOT NULL,   -- tag | macro
    key_name           TEXT NOT NULL,
    old_value          TEXT NULL,
    new_value          TEXT NULL,
    action             VARCHAR(50) NOT NULL,   -- added | updated | unchanged | removed
    merge_result       VARCHAR(50) NULL,       -- updated | preserved_manual | no_change
    status             VARCHAR(50) NOT NULL,
    reason             TEXT NULL,
    dry_run            BOOLEAN DEFAULT FALSE NOT NULL,

    processed_at       TIMESTAMPTZ DEFAULT NOW() NULL
);

COMMENT ON TABLE hmdl.zabbix_tag_update_log IS
    'Tag and macro level audit; managed keys from tags_config / templates.yml.';
COMMENT ON COLUMN hmdl.zabbix_tag_update_log.object_type IS
    'tag for Zabbix host tags; macro for host macro keys.';
COMMENT ON COLUMN hmdl.zabbix_tag_update_log.merge_result IS
    'preserved_manual when tag/macro was kept due to operator override outside managed set.';

CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_run_id
    ON hmdl.zabbix_tag_update_log (run_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_source_device_id
    ON hmdl.zabbix_tag_update_log (source_device_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_zabbix_hostid
    ON hmdl.zabbix_tag_update_log (zabbix_hostid);
CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_object_type
    ON hmdl.zabbix_tag_update_log (object_type);
CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_key_name
    ON hmdl.zabbix_tag_update_log (key_name);
CREATE INDEX IF NOT EXISTS idx_zabbix_tag_update_log_processed_at
    ON hmdl.zabbix_tag_update_log (processed_at DESC);
