-- Host-level datalake coverage for IBM Power servers.
-- Collected = ibm_server_general.server_details_servername (freshness via "time").
-- Expected  = discovery_ibm_inventory.servername (asset_type='server').
CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.hmdl_datalake_monitoring_ibm_host (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL,
    servername          TEXT NOT NULL,                 -- ibm_server_general.server_details_servername
    mtm                 TEXT NULL,                     -- server_details_mtm
    expected            BOOLEAN NOT NULL,
    collected           BOOLEAN NOT NULL,
    status              VARCHAR(20) NOT NULL,          -- in_both | only_expected | only_datalake
    datalake_last_seen  TIMESTAMPTZ NULL,              -- ibm_server_general."time" latest
    expected_last_seen  TIMESTAMPTZ NULL,              -- discovery_ibm_inventory.collection_time
    window_days         INTEGER NOT NULL,
    details             JSONB NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (run_id, servername)
);

CREATE INDEX IF NOT EXISTS idx_dlm_ibmhost_run
    ON hmdl.hmdl_datalake_monitoring_ibm_host (run_id);
CREATE INDEX IF NOT EXISTS idx_dlm_ibmhost_status
    ON hmdl.hmdl_datalake_monitoring_ibm_host (status);
