-- Cluster-level datalake coverage (VMware + Nutanix, separated by `source`).
-- One row per (run, source, cluster): is it expected (inventory) and collected (metrics)?
CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.hmdl_datalake_monitoring_clusters (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL,
    source              VARCHAR(20) NOT NULL,          -- 'vmware' | 'nutanix'
    cluster_name        TEXT NOT NULL,
    cluster_uuid        TEXT NULL,                     -- nutanix only; NULL for vmware
    datacenter          TEXT NULL,
    expected            BOOLEAN NOT NULL,
    collected           BOOLEAN NOT NULL,
    status              VARCHAR(20) NOT NULL,          -- in_both | only_expected | only_datalake
    datalake_last_seen  TIMESTAMPTZ NULL,              -- *_metrics latest collection_time
    expected_last_seen  TIMESTAMPTZ NULL,              -- inventory last_observed
    window_days         INTEGER NOT NULL,
    details             JSONB NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (run_id, source, cluster_name)
);

CREATE INDEX IF NOT EXISTS idx_dlm_clusters_run
    ON hmdl.hmdl_datalake_monitoring_clusters (run_id, source);
CREATE INDEX IF NOT EXISTS idx_dlm_clusters_status
    ON hmdl.hmdl_datalake_monitoring_clusters (status);
