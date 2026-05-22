-- HMDL: per-IP add/remove audit rows.
CREATE TABLE IF NOT EXISTS hmdl.collector_diff_log (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(100) NOT NULL,
    proxy_id     TEXT NOT NULL,
    collector_id BIGINT NULL REFERENCES hmdl.collector_definition(id) ON DELETE SET NULL,
    conf_key     TEXT NULL,
    action       VARCHAR(20) NOT NULL,
    ip           INET NOT NULL,
    reason       TEXT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW() NULL
);

CREATE INDEX IF NOT EXISTS idx_collector_diff_log_run
    ON hmdl.collector_diff_log (run_id, proxy_id);
