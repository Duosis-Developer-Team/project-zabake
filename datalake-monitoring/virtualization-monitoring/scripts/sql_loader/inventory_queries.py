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
    """Expected IBM Power hosts from NetBox device inventory (Can's rule):
    manufacturer_display=IBM AND device_role_display=HOST. Key `name` (AS
    servername) matches ibm_server_general.server_details_servername."""
    query = """
        SELECT DISTINCT ON (name)
            name AS servername,
            collection_time
        FROM discovery_netbox_inventory_device
        WHERE manufacturer_display IN ('IBM')
          AND device_role_display IN ('HOST')
          AND name IS NOT NULL
          AND BTRIM(name) <> ''
        ORDER BY name, collection_time DESC
    """
    return fetch_all(connection, query)
