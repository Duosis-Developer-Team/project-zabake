"""Write cluster/host coverage into simple per-type hmdl tables.

One row per entity (upsert by name): collected (datalake has data) and
expected (in inventory). Base reconciler emits in_both / only_in_datalake /
only_in_loki; we translate to coverage flags.
"""

_STATUS_MAP = {
    "in_both": "in_both",
    "only_in_datalake": "only_datalake",
    "only_in_loki": "only_expected",
}

# is_live = expected AND fresh data collected within the last day (computed in SQL
# to avoid timezone-naive/aware comparison issues across metric tables).
_IS_LIVE_UPDATE = (
    "UPDATE {table} SET is_live = "
    "(expected AND last_collected IS NOT NULL "
    "AND last_collected >= NOW() - INTERVAL '1 day')"
)


def coverage_status(base_status: str) -> str:
    """Translate a base reconciler status into the coverage vocabulary."""
    return _STATUS_MAP.get(base_status, base_status)


def coverage_flags(status: str) -> tuple[bool, bool]:
    """Return (expected, collected) for a coverage status."""
    expected = status in ("in_both", "only_expected")
    collected = status in ("in_both", "only_datalake")
    return expected, collected


def _rows(target_payload: dict):
    for item in target_payload.get("details", []):
        status = coverage_status(item.get("status", ""))
        expected, collected = coverage_flags(status)
        dl = item.get("datalake") or {}
        nb = item.get("netbox") or {}
        yield dl, nb, collected, expected


def upsert_cluster_coverage(connection, table: str, source: str, target_payload: dict) -> None:
    query = f"""
        INSERT INTO {table} (source, cluster_name, collected, expected, last_collected)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source, cluster_name) DO UPDATE SET
            collected = EXCLUDED.collected,
            expected = EXCLUDED.expected,
            last_collected = EXCLUDED.last_collected,
            checked_at = NOW()
    """
    with connection.cursor() as cursor:
        for dl, nb, collected, expected in _rows(target_payload):
            cluster_name = dl.get("cluster_name") or nb.get("cluster_name") or ""
            cursor.execute(query, (source, cluster_name, collected, expected, dl.get("collection_time")))
        cursor.execute(_IS_LIVE_UPDATE.format(table=table))
    connection.commit()


def upsert_ibm_host_coverage(connection, table: str, target_payload: dict) -> None:
    query = f"""
        INSERT INTO {table} (servername, collected, expected, last_collected)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (servername) DO UPDATE SET
            collected = EXCLUDED.collected,
            expected = EXCLUDED.expected,
            last_collected = EXCLUDED.last_collected,
            checked_at = NOW()
    """
    with connection.cursor() as cursor:
        for dl, nb, collected, expected in _rows(target_payload):
            servername = dl.get("servername") or nb.get("servername") or ""
            cursor.execute(query, (servername, collected, expected, dl.get("collection_time")))
        cursor.execute(_IS_LIVE_UPDATE.format(table=table))
    connection.commit()
