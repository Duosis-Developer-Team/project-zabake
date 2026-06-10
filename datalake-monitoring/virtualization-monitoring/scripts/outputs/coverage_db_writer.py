"""Write cluster/host coverage reconciliation into per-type hmdl tables.

Coverage vocabulary (per row): in_both | only_expected | only_datalake.
Base reconciler emits in_both / only_in_datalake / only_in_loki; we translate.
"""

from psycopg2.extras import Json

_STATUS_MAP = {
    "in_both": "in_both",
    "only_in_datalake": "only_datalake",
    "only_in_loki": "only_expected",
}


def coverage_status(base_status: str) -> str:
    """Translate a base reconciler status into the coverage vocabulary."""
    return _STATUS_MAP.get(base_status, base_status)


def coverage_flags(status: str) -> tuple[bool, bool]:
    """Return (expected, collected) for a coverage status."""
    expected = status in ("in_both", "only_expected")
    collected = status in ("in_both", "only_datalake")
    return expected, collected


def _detail_rows(target_payload: dict) -> list[dict]:
    return target_payload.get("details", [])


def upsert_cluster_coverage(connection, table: str, run_id: str, source: str, target_payload: dict, window_days: int) -> None:
    query = f"""
        INSERT INTO {table}
            (run_id, source, cluster_name, cluster_uuid, datacenter,
             expected, collected, status, datalake_last_seen, expected_last_seen,
             window_days, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id, source, cluster_name) DO UPDATE SET
            cluster_uuid = EXCLUDED.cluster_uuid,
            datacenter = EXCLUDED.datacenter,
            expected = EXCLUDED.expected,
            collected = EXCLUDED.collected,
            status = EXCLUDED.status,
            datalake_last_seen = EXCLUDED.datalake_last_seen,
            expected_last_seen = EXCLUDED.expected_last_seen,
            window_days = EXCLUDED.window_days,
            details = EXCLUDED.details
    """
    with connection.cursor() as cursor:
        for item in _detail_rows(target_payload):
            status = coverage_status(item.get("status", ""))
            expected, collected = coverage_flags(status)
            dl = item.get("datalake") or {}
            nb = item.get("netbox") or {}
            cluster_name = dl.get("cluster_name") or nb.get("cluster_name") or ""
            cursor.execute(
                query,
                (
                    run_id,
                    source,
                    cluster_name,
                    dl.get("cluster_uuid") or nb.get("cluster_uuid"),
                    dl.get("datacenter") or nb.get("datacenter"),
                    expected,
                    collected,
                    status,
                    dl.get("collection_time"),
                    nb.get("last_observed"),
                    window_days,
                    Json({"datalake": dl, "expected": nb}),
                ),
            )
    connection.commit()


def upsert_ibm_host_coverage(connection, table: str, run_id: str, target_payload: dict, window_days: int) -> None:
    query = f"""
        INSERT INTO {table}
            (run_id, servername, mtm, expected, collected, status,
             datalake_last_seen, expected_last_seen, window_days, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id, servername) DO UPDATE SET
            mtm = EXCLUDED.mtm,
            expected = EXCLUDED.expected,
            collected = EXCLUDED.collected,
            status = EXCLUDED.status,
            datalake_last_seen = EXCLUDED.datalake_last_seen,
            expected_last_seen = EXCLUDED.expected_last_seen,
            window_days = EXCLUDED.window_days,
            details = EXCLUDED.details
    """
    with connection.cursor() as cursor:
        for item in _detail_rows(target_payload):
            status = coverage_status(item.get("status", ""))
            expected, collected = coverage_flags(status)
            dl = item.get("datalake") or {}
            nb = item.get("netbox") or {}
            servername = dl.get("servername") or nb.get("servername") or ""
            cursor.execute(
                query,
                (
                    run_id,
                    servername,
                    dl.get("mtm") or nb.get("mtm"),
                    expected,
                    collected,
                    status,
                    dl.get("collection_time"),
                    nb.get("collection_time"),
                    window_days,
                    Json({"datalake": dl, "expected": nb}),
                ),
            )
    connection.commit()
