-- HMDL: ICMP and TCP connectivity check results.
CREATE TABLE IF NOT EXISTS hmdl.collector_check_log (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(100) NOT NULL,
    proxy_id     TEXT NOT NULL,
    collector_id BIGINT NULL REFERENCES hmdl.collector_definition(id) ON DELETE SET NULL,
    target_id    BIGINT NULL REFERENCES hmdl.collector_target(id) ON DELETE SET NULL,
    ip           INET NOT NULL,
    check_type   VARCHAR(20) NOT NULL,
    port         INTEGER NULL,
    status       VARCHAR(30) NOT NULL,
    latency_ms   INTEGER NULL,
    error_text   TEXT NULL,
    check_phase  VARCHAR(30) NULL,
    checked_at   TIMESTAMPTZ DEFAULT NOW() NULL
);

CREATE INDEX IF NOT EXISTS idx_collector_check_log_run
    ON hmdl.collector_check_log (run_id, proxy_id);
