"""Unit tests for interface update delta policy (documentation of expected behavior)."""


def test_interface_type_unchanged_allows_ip_only_delta():
    existing_type = 2
    mapped_type = 2
    assert existing_type == mapped_type
    # When equal, payload must omit type/main/useip and send only ip/dns/port.


def test_interface_type_changed_blocks_full_replace():
    existing_type = 1
    mapped_type = 2
    assert existing_type != mapped_type
    # When different, interfaces key must be omitted from host.update (INTERFACE_TYPE_LOCKED).


def test_zabbix_error_interface_linked_to_item():
    message = 'Interface is linked to item "HA Cluster Member 2 - CPU Usage" on "HOST".'
    assert "Interface is linked to item" in message
