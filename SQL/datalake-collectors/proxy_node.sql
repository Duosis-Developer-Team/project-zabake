-- HMDL: NiFi proxy registry materialized during collector sync jobs.
CREATE TABLE IF NOT EXISTS hmdl.proxy_node (
    proxy_id            TEXT PRIMARY KEY,
    dc_code             TEXT NOT NULL,
    proxy_nifi_host     TEXT NOT NULL,
    ssh_user            TEXT DEFAULT 'root' NOT NULL,
    conf_path           TEXT DEFAULT '/Datalake_Project/configuration_file.json' NOT NULL,
    gitea_audit_path    TEXT NULL,
    first_seen_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_seen_at        TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_run_id         VARCHAR(100) NULL,
    last_awx_job_id     VARCHAR(100) NULL,
    last_dry_run        BOOLEAN DEFAULT FALSE NOT NULL
);

COMMENT ON TABLE hmdl.proxy_node IS
    'NiFi proxy nodes observed during datalake_collector_sync runs; read by hmdl-api topology.';

CREATE INDEX IF NOT EXISTS idx_proxy_node_dc_code
    ON hmdl.proxy_node (dc_code);
