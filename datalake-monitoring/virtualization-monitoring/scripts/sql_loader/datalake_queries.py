from utils.db import fetch_all


def fetch_vmware_vms(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (uuid)
            uuid,
            vmname,
            datacenter,
            cluster,
            vmhost,
            customerid AS customer_code,
            collection_time
        FROM vm_metrics
        WHERE collection_time >= NOW() - (%s::text || ' days')::interval
          AND uuid IS NOT NULL
        ORDER BY uuid, collection_time DESC
    """
    return fetch_all(connection, query, (str(window_days),))


def fetch_nutanix_vms(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (vm_uuid)
            vm_uuid,
            vm_name,
            cluster_name AS cluster,
            customerid AS customer_code,
            timestamp AS collection_time
        FROM nutanix_vm_metrics
        WHERE timestamp >= NOW() - (%s::text || ' days')::interval
          AND vm_uuid IS NOT NULL
        ORDER BY vm_uuid, timestamp DESC
    """
    return fetch_all(connection, query, (str(window_days),))


def fetch_ibm_lpars(connection, window_days: int) -> list[dict]:
    query = """
        SELECT DISTINCT ON (lparname)
            lparname,
            servername AS cluster,
            customerid AS customer_code,
            time AS collection_time
        FROM ibm_lpar_general
        WHERE time >= NOW() - (%s::text || ' days')::interval
          AND lparname IS NOT NULL
        ORDER BY lparname, time DESC
    """
    return fetch_all(connection, query, (str(window_days),))
