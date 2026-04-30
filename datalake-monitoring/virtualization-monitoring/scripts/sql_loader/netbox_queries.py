from utils.db import fetch_all


def fetch_netbox_vm_inventory(connection, table_name: str = "discovery_netbox_virtualization_vm") -> list[dict]:
    query = f"""
        SELECT
            id,
            name,
            cluster_name,
            device_name,
            custom_fields_uuid,
            custom_fields_moid,
            custom_fields_musteri,
            collection_time
        FROM {table_name}
        WHERE collection_time = (
            SELECT MAX(collection_time) FROM {table_name}
        )
    """
    return fetch_all(connection, query)
