"""Unit tests for Hana Linux VM transform helper."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playbooks" / "roles" / "netbox_zabbix_sync" / "files"))

from hana_linux_vm_transform import (  # noqa: E402
    extract_dc_code,
    is_hana_linux_vm,
    transform_hana_linux_vms,
    vm_row_to_device,
)


def test_extract_dc_code_from_cluster():
    assert extract_dc_code("DC13-G2-CLS-IBM") == "DC13"
    assert extract_dc_code("DC14-G2-CLS-IBM") == "DC14"
    assert extract_dc_code("") == ""


def test_is_hana_linux_vm_filters_non_hana():
    assert is_hana_linux_vm(
        {
            "name": "Aksular_S4_Hanadb_Dev",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_guest_os": "Linux/SLES",
            "custom_fields_endpoint": "10.34.2.141",
            "status_value": "poweredOn",
        }
    )
    assert not is_hana_linux_vm(
        {
            "name": "Generic_Linux_VM",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_guest_os": "Linux/SLES",
            "custom_fields_endpoint": "10.34.2.141",
            "status_value": "poweredOn",
        }
    )
    assert not is_hana_linux_vm(
        {
            "name": "Offline_Hana_Dev",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_guest_os": "Linux/SLES",
            "custom_fields_endpoint": "10.34.2.141",
            "status_value": "poweredOff",
        }
    )


def test_vm_row_to_device_shape():
    device = vm_row_to_device(
        {
            "id": 123,
            "name": "Boyner_Hana_Cocpit",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_endpoint": "10.34.2.141",
            "custom_fields_guest_os": "Linux/SLES",
            "custom_fields_musteri": "Boyner",
            "site_name": "DC13",
        }
    )
    assert device["id"] == "vm-123"
    assert device["device_model"] == "Hana Linux"
    assert device["device_role_name"] == "HANA VM"
    assert device["primary_ip_address"] == "10.34.2.141"
    assert device["root_location_name"] == "DC13"


def test_transform_deduplicates_by_name():
    rows = [
        {
            "id": 1,
            "name": "Dup_Hana_Dev",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_guest_os": "Linux",
            "custom_fields_endpoint": "10.0.0.1",
            "status_value": "poweredOn",
        },
        {
            "id": 2,
            "name": "Dup_Hana_Dev",
            "cluster_name": "DC13-G2-CLS-IBM",
            "custom_fields_guest_os": "Linux",
            "custom_fields_endpoint": "10.0.0.2",
            "status_value": "poweredOn",
        },
    ]
    devices = transform_hana_linux_vms(rows)
    assert len(devices) == 1
