from utils.db import fetch_all


def build_gui_replay_snapshot(connection, window_days: int) -> dict:
    vmware_count_query = """
        SELECT COUNT(DISTINCT uuid) AS count
        FROM vm_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND uuid IS NOT NULL
    """
    nutanix_count_query = """
        SELECT COUNT(DISTINCT vm_uuid) AS count
        FROM nutanix_vm_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND vm_uuid IS NOT NULL
    """
    ibm_lpar_count_query = """
        SELECT COUNT(DISTINCT lparname) AS count
        FROM ibm_lpar_general
        WHERE time >= NOW() - (%s::text || ' days')::interval
          AND lparname IS NOT NULL
    """
    vmware_count = fetch_all(connection, vmware_count_query, (str(window_days),))[0]["count"]
    nutanix_count = fetch_all(connection, nutanix_count_query, (str(window_days),))[0]["count"]
    ibm_lpar_count = fetch_all(connection, ibm_lpar_count_query, (str(window_days),))[0]["count"]
    return {
        "source": "internal_sql_replay",
        "vmware_distinct_vm_count": int(vmware_count),
        "nutanix_distinct_vm_count": int(nutanix_count),
        "ibm_distinct_lpar_count": int(ibm_lpar_count),
        "window_days": window_days,
    }
