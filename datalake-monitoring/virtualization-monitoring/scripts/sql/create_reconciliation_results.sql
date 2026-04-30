CREATE TABLE IF NOT EXISTS reconciliation_results (
    run_id TEXT NOT NULL,
    target TEXT NOT NULL,
    window_days INTEGER NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    summary JSONB NOT NULL,
    details JSONB,
    PRIMARY KEY (run_id, target)
);
