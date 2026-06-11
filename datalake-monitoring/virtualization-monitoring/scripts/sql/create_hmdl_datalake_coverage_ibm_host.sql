-- Host-level datalake coverage for IBM Power servers. New, simple table.
-- One row per server: is its data collected and is it in inventory?
CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.hmdl_datalake_coverage_ibm_host (
    servername  TEXT         NOT NULL,
    collected      BOOLEAN     NOT NULL,     -- ibm_server_general'da var mi
    expected       BOOLEAN     NOT NULL,     -- envanterde (inventory) var mi
    last_collected TIMESTAMPTZ NULL,         -- topladigimiz en guncel veri zamani
    checked_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (servername)
);

CREATE INDEX IF NOT EXISTS idx_dl_cov_ibm_host_collected
    ON hmdl.hmdl_datalake_coverage_ibm_host (collected, expected);
