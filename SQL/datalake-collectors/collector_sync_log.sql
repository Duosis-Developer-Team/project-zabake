-- HMDL: per-run per-proxy per-collector summary.
CREATE TABLE IF NOT EXISTS hmdl.collector_sync_log (
    id              BIGSERIAL PRIMARY KEY,
    run_id          VARCHAR(100) NOT NULL,
    awx_job_id      VARCHAR(100) NULL,
    playbook_name   TEXT NULL,
    proxy_id        TEXT NOT NULL,
    collector_id    BIGINT NULL REFERENCES hmdl.collector_definition(id) ON DELETE SET NULL,
    added_count     INTEGER DEFAULT 0 NOT NULL,
    removed_count   INTEGER DEFAULT 0 NOT NULL,
    unchanged_count INTEGER DEFAULT 0 NOT NULL,
    status          VARCHAR(50) NOT NULL,
    dry_run         BOOLEAN DEFAULT FALSE NOT NULL,
    error_payload   JSONB NULL,
    started_at      TIMESTAMPTZ DEFAULT NOW() NULL,
    finished_at     TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_collector_sync_log_run
    ON hmdl.collector_sync_log (run_id, proxy_id);
