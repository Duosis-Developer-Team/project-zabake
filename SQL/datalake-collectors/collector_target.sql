-- HMDL: per-target inventory (collector x IP x proxy).
CREATE TABLE IF NOT EXISTS hmdl.collector_target (
    id                  BIGSERIAL PRIMARY KEY,
    collector_id        BIGINT NOT NULL REFERENCES hmdl.collector_definition(id) ON DELETE CASCADE,
    netbox_entity_id    BIGINT NULL,
    host_entity_type    VARCHAR(30) NOT NULL,
    ip                  INET NOT NULL,
    dc_code             VARCHAR(20) NULL,
    tenant_name         TEXT NULL,
    proxy_id            TEXT NOT NULL,
    entity_name         TEXT NULL,
    manufacturer        TEXT NULL,
    last_seen_in_netbox TIMESTAMPTZ DEFAULT NOW() NULL,
    last_distributed_at TIMESTAMPTZ NULL,
    last_check_status   VARCHAR(30) NULL,
    last_check_at       TIMESTAMPTZ NULL,
    status              VARCHAR(20) DEFAULT 'active' NOT NULL,
    extra               JSONB NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW() NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NULL,
    UNIQUE (collector_id, ip, proxy_id)
);

COMMENT ON TABLE hmdl.collector_target IS
    'Which collector runs against which IP on which proxy NiFi node.';
COMMENT ON COLUMN hmdl.collector_target.host_entity_type IS
    'platform | device';

CREATE INDEX IF NOT EXISTS idx_collector_target_proxy
    ON hmdl.collector_target (proxy_id, status);
CREATE INDEX IF NOT EXISTS idx_collector_target_collector
    ON hmdl.collector_target (collector_id, status);
