-- HMDL: per-host sync run summary (devices, platforms, virtual firewalls).
-- Playbook: hmdl_sync_log.yml | Read baseline: hmdl_read_last_sync.yml

CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.zabbix_sync_log (
    id                           BIGSERIAL PRIMARY KEY,
    run_id                       VARCHAR(100) NULL,
    awx_job_id                   VARCHAR(100) NULL,
    playbook_name                TEXT NULL,

    -- Inventory identity
    source_device_id             BIGINT NULL,
    source_device_name           TEXT NULL,
    source_table                 TEXT DEFAULT 'discovery_netbox_inventory_device',
    host_entity_type             VARCHAR(30) NULL,   -- device | platform | virtual_fw
    inventory_source             VARCHAR(20) NULL,   -- loki | datalake

    -- Zabbix host
    zabbix_hostid                TEXT NULL,
    zabbix_hostname              TEXT NULL,
    zabbix_host_ip               TEXT NULL,
    last_visible_name            TEXT NULL,

    -- NetBox / discovery attributes (snapshot)
    device_type                  TEXT NULL,
    device_role                  TEXT NULL,
    manufacturer_name            TEXT NULL,
    site_name                    TEXT NULL,
    location_name                TEXT NULL,
    location_parent_name         TEXT NULL,
    root_location_name           TEXT NULL,
    last_location                TEXT NULL,
    tenant_name                  TEXT NULL,
    cluster_name                 TEXT NULL,

    -- Sync outcome
    operation                    VARCHAR(50) NULL,   -- create | update | skip
    status                       VARCHAR(50) NOT NULL,
    reason                       TEXT NULL,
    dry_run                      BOOLEAN DEFAULT FALSE NOT NULL,

    -- Proxy group audit (smart merge)
    expected_proxy_group_id      TEXT NULL,
    last_proxy_group_id          TEXT NULL,
    zabbix_proxy_group_id        TEXT NULL,
    proxy_location_change        BOOLEAN DEFAULT FALSE NOT NULL,
    proxy_manual_change_detected BOOLEAN DEFAULT FALSE NOT NULL,

    -- Smart merge audit
    field_merge_actions          JSONB NULL,
    last_managed_groups          JSONB NULL,

    -- Payloads
    request_payload              JSONB NULL,
    response_payload             JSONB NULL,
    error_payload                JSONB NULL,
    extra_data                   JSONB NULL,

    processed_at                 TIMESTAMPTZ DEFAULT NOW() NULL,
    created_at                   TIMESTAMPTZ DEFAULT NOW() NULL
);

COMMENT ON TABLE hmdl.zabbix_sync_log IS
    'One row per host processed per AWX run; baseline for proxy/location and merge reporting.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.host_entity_type IS
    'Host category: device, platform, or virtual_fw.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.inventory_source IS
    'Inventory fetch path: loki (NetBox API) or datalake (PostgreSQL discovery).';
COMMENT ON COLUMN hmdl.zabbix_sync_log.last_proxy_group_id IS
    'Proxy group id automation assigned or intended to assign.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.zabbix_proxy_group_id IS
    'Proxy group id observed on Zabbix host at sync time.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.proxy_manual_change_detected IS
    'True when Zabbix proxy differs from expected and location did not change.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.field_merge_actions IS
    'Per-field merge outcome: updated, preserved_manual, no_change.';
COMMENT ON COLUMN hmdl.zabbix_sync_log.last_managed_groups IS
    'JSON array of host group names managed by automation for this host.';

CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_processed_at
    ON hmdl.zabbix_sync_log (processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_run_id
    ON hmdl.zabbix_sync_log (run_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_source_device_id
    ON hmdl.zabbix_sync_log (source_device_id);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_status
    ON hmdl.zabbix_sync_log (status);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_zabbix_hostname
    ON hmdl.zabbix_sync_log (zabbix_hostname);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_host_entity_type
    ON hmdl.zabbix_sync_log (host_entity_type);
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_proxy_manual
    ON hmdl.zabbix_sync_log (proxy_manual_change_detected)
    WHERE proxy_manual_change_detected = TRUE;

-- Baseline lookup for next sync (matches hmdl_read_last_sync.yml)
CREATE INDEX IF NOT EXISTS idx_zabbix_sync_log_device_baseline
    ON hmdl.zabbix_sync_log (source_device_id, processed_at DESC NULLS LAST)
    WHERE status IN ('eklendi', 'güncellendi', 'güncel', 'dry_run');
