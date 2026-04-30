from utils.db import fetch_all


def fetch_vmware_vms(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (uuid)
            uuid,
            vmname,
            datacenter,
            cluster,
            vmhost,
            collection_time
        FROM vm_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND uuid IS NOT NULL
        ORDER BY uuid, collection_time DESC
    """
    return fetch_all(connection, query, (str(window_days),))


def fetch_nutanix_vms(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (nvm.vm_uuid)
            nvm.vm_uuid,
            nvm.vm_name,
            nvm.cluster_uuid::text AS cluster_uuid,
            COALESCE(ncm.cluster_name, '') AS cluster,
            nvm.collection_time
        FROM nutanix_vm_metrics nvm
        LEFT JOIN LATERAL (
            SELECT cluster_name
            FROM nutanix_cluster_metrics ncm
            WHERE ncm.cluster_uuid = nvm.cluster_uuid
            ORDER BY ncm.collection_time DESC
            LIMIT 1
        ) ncm ON TRUE
        WHERE nvm.collection_time >= NOW() - (%s::text || ' days')::interval
          AND nvm.vm_uuid IS NOT NULL
        ORDER BY nvm.vm_uuid, nvm.collection_time DESC
    """
    return fetch_all(connection, query, (str(window_days),))


def fetch_ibm_lpars(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (lparname)
            lparname,
            servername AS cluster,
            time AS collection_time
        FROM ibm_lpar_general
        WHERE time >= NOW() - (%s::text || ' days')::interval
          AND lparname IS NOT NULL
        ORDER BY lparname, time DESC
    """
    return fetch_all(connection, query, (str(window_days),))


def fetch_vmware_cluster_set(connection, window_days: int) -> set[str]:
    query = """
        SELECT DISTINCT cluster
        FROM vm_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND cluster IS NOT NULL
          AND BTRIM(cluster) <> ''
    """
    rows = fetch_all(connection, query, (str(window_days),))
    return {str(row["cluster"]).strip() for row in rows if row.get("cluster")}


def fetch_nutanix_cluster_set(connection, window_days: int) -> set[str]:
    query = """
        SELECT DISTINCT cluster_name
        FROM nutanix_cluster_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND cluster_name IS NOT NULL
          AND BTRIM(cluster_name) <> ''
    """
    rows = fetch_all(connection, query, (str(window_days),))
    return {str(row["cluster_name"]).strip() for row in rows if row.get("cluster_name")}
