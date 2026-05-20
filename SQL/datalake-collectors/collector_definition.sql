-- HMDL: collector type catalog (maps to configuration_file.json sections).
-- Playbook: datalake_collector_sync | See migrations/001_initial_hmdl_collector_schema.sql

CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.collector_definition (
    id                 BIGSERIAL PRIMARY KEY,
    collector_type     TEXT UNIQUE NOT NULL,
    conf_key           TEXT NOT NULL,
    script_path        TEXT NULL,
    ip_field           TEXT NULL,
    ip_format          VARCHAR(30) NULL,
    source_type        VARCHAR(30) NOT NULL DEFAULT 'platform',
    default_port       INTEGER NULL,
    check_ports        INTEGER[] NOT NULL DEFAULT '{}',
    vault_key          TEXT NULL,
    enabled            BOOLEAN DEFAULT TRUE NOT NULL,
    created_at         TIMESTAMPTZ DEFAULT NOW() NULL,
    updated_at         TIMESTAMPTZ DEFAULT NOW() NULL
);

COMMENT ON TABLE hmdl.collector_definition IS
    'Catalog of datalake collector types and their configuration_file.json section keys.';
COMMENT ON COLUMN hmdl.collector_definition.source_type IS
    'platform | device | manual_only';

CREATE INDEX IF NOT EXISTS idx_collector_definition_source_type
    ON hmdl.collector_definition (source_type);
