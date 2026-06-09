-- Add check_phase column for pre/post reconcile connectivity audits.
ALTER TABLE hmdl.collector_check_log
    ADD COLUMN IF NOT EXISTS check_phase VARCHAR(30) NULL;

COMMENT ON COLUMN hmdl.collector_check_log.check_phase IS
    'pre_reconcile | post_reconcile';

CREATE INDEX IF NOT EXISTS idx_collector_check_log_phase
    ON hmdl.collector_check_log (run_id, check_phase);
