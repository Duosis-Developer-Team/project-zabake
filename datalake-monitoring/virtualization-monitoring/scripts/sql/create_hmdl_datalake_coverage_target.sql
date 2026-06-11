-- B) Target discovery/reachability table over the NiFi collection targets.
-- Real table (Can's request) refreshed from hmdl.collector_target each run.
-- Fields: IP, platform, DNS, network access (var/yok), tenant. No live checks:
-- network_access comes from the existing connectivity result
-- (collector_target.last_check_status, written by tcp_telnet_check).
CREATE SCHEMA IF NOT EXISTS hmdl;

CREATE TABLE IF NOT EXISTS hmdl.hmdl_datalake_coverage_target (
    ip             TEXT,
    platform       TEXT,
    dns            TEXT,
    network_access BOOLEAN,        -- true = erisim var (last_check_status='ok')
    tenant         TEXT,
    entity_type    TEXT,           -- platform | device
    dc_code        TEXT,
    proxy          TEXT,
    check_status   TEXT,           -- ok | icmp_fail | telnet_fail | partial
    checked_at     TIMESTAMPTZ
);

-- Refresh: full reload from collector_target (run each time).
TRUNCATE hmdl.hmdl_datalake_coverage_target;

INSERT INTO hmdl.hmdl_datalake_coverage_target
    (ip, platform, dns, network_access, tenant, entity_type, dc_code, proxy, check_status, checked_at)
SELECT
    host(ct.ip),
    COALESCE(cd.collector_type, ct.manufacturer),
    ct.entity_name,
    (ct.last_check_status = 'ok'),
    ct.tenant_name,
    ct.host_entity_type,
    ct.dc_code,
    ct.proxy_id,
    ct.last_check_status,
    ct.last_check_at
FROM hmdl.collector_target ct
LEFT JOIN hmdl.collector_definition cd ON cd.id = ct.collector_id
WHERE ct.status = 'active';
