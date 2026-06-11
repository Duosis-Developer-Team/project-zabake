-- Cluster-level datalake coverage (VMware + Nutanix). New, simple table.
-- One row per (source, cluster): is its data collected and is it in inventory?
CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.hmdl_datalake_coverage_cluster (
    source        VARCHAR(20)  NOT NULL,   -- 'vmware' | 'nutanix'
    cluster_name  TEXT         NOT NULL,
    collected      BOOLEAN     NOT NULL,    -- datalake'te metrik var mi
    expected       BOOLEAN     NOT NULL,    -- envanterde (inventory) var mi
    last_collected TIMESTAMPTZ NULL,        -- topladigimiz en guncel veri zamani
    is_live        BOOLEAN     NOT NULL DEFAULT FALSE,  -- expected & son 1 gunde veri var
    checked_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, cluster_name)
);

CREATE INDEX IF NOT EXISTS idx_dl_cov_cluster_collected
    ON hmdl.hmdl_datalake_coverage_cluster (collected, expected);
