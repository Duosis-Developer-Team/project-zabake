"""Expected (inventory) side for cluster/host coverage.

These discovery_* tables live in the datalake DB alongside the metric tables,
so they are queried on the same connection as datalake_queries.
"""

from utils.db import fetch_all


def fetch_expected_vmware_clusters(connection) -> list[dict]:
    """Expected VMware clusters from discovery_vmware_inventory_cluster.
    Key `name` matches cluster_metrics.cluster; `last_observed` gives freshness."""
    query = """
        SELECT DISTINCT ON (name)
            name AS cluster_name,
            status,
            last_observed
        FROM discovery_vmware_inventory_cluster
        WHERE name IS NOT NULL AND BTRIM(name) <> ''
        ORDER BY name, last_observed DESC
    """
    return fetch_all(connection, query)


def fetch_expected_nutanix_clusters(connection) -> list[dict]:
    """Expected Nutanix clusters from discovery_nutanix_inventory_cluster."""
    query = """
        SELECT DISTINCT ON (name)
            name AS cluster_name,
            component_uuid AS cluster_uuid,
            status,
            last_observed
        FROM discovery_nutanix_inventory_cluster
        WHERE name IS NOT NULL AND BTRIM(name) <> ''
        ORDER BY name, last_observed DESC
    """
    return fetch_all(connection, query)


def fetch_expected_ibm_hosts(connection) -> list[dict]:
    """Expected IBM Power hosts from discovery_ibm_inventory (asset_type='server').
    Key `servername` matches ibm_server_general.server_details_servername."""
    query = """
        SELECT DISTINCT ON (servername)
            servername,
            mtm,
            collection_time
        FROM discovery_ibm_inventory
        WHERE asset_type = 'server'
          AND servername IS NOT NULL
          AND BTRIM(servername) <> ''
        ORDER BY servername, collection_time DESC
    """
    return fetch_all(connection, query)
