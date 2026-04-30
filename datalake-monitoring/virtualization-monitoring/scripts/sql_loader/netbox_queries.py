from utils.db import fetch_all


def fetch_netbox_vm_inventory(connection) -> list[dict]:
    query = """
        SELECT
            id,
            name,
            cluster_name,
            device_name,
            custom_fields_uuid,
            custom_fields_moid,
            custom_fields_musteri,
            collection_time
        FROM netbox_virtualization_vm
        WHERE collection_time = (
            SELECT MAX(collection_time) FROM netbox_virtualization_vm
        )
    """
    return fetch_all(connection, query)
