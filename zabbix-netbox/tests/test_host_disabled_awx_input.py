from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_host_disabled_defaults_are_false():
    defaults_path = REPO_ROOT / "playbooks" / "roles" / "netbox_zabbix_sync" / "defaults" / "main.yml"
    defaults = yaml.safe_load(defaults_path.read_text(encoding="utf-8"))

    assert defaults["create_devices_disabled"] is False
    assert defaults["create_platforms_disabled"] is False


def test_playbook_passes_host_disabled_awx_inputs_to_role():
    playbook_path = REPO_ROOT / "playbooks" / "netbox_zabbix_sync.yaml"
    playbook = yaml.safe_load(playbook_path.read_text(encoding="utf-8"))

    play_vars = playbook[0]["vars"]
    role_vars = playbook[0]["roles"][0]["vars"]

    assert play_vars["_create_devices_disabled"] == "{{ create_devices_disabled | default(false) }}"
    assert play_vars["_create_platforms_disabled"] == "{{ create_platforms_disabled | default(false) }}"
    assert role_vars["create_devices_disabled"] == "{{ _create_devices_disabled }}"
    assert role_vars["create_platforms_disabled"] == "{{ _create_platforms_disabled }}"


def test_device_and_platform_records_have_independent_host_status_flags():
    device_tasks = read_text("playbooks/roles/netbox_zabbix_sync/tasks/process_device.yml")
    platform_tasks = read_text("playbooks/roles/netbox_zabbix_sync/tasks/process_platform.yml")

    assert 'HOST_STATUS: "{{ 1 if create_devices_disabled | bool else 0 }}"' in device_tasks
    assert 'HOST_STATUS: "{{ 1 if create_platforms_disabled | bool else 0 }}"' in platform_tasks
    assert "create_platforms_disabled" not in device_tasks
    assert "create_devices_disabled" not in platform_tasks


def test_host_create_uses_status_but_host_update_does_not():
    operations = read_text("playbooks/roles/netbox_zabbix_sync/tasks/zabbix_host_operations.yml")

    create_block = operations.split("- name: Create new host (scenario create)", 1)[1].split(
        "- name: Record create success",
        1,
    )[0]
    update_block = operations.split("- name: Update existing host (scenario update", 1)[1].split(
        "- name: Record no update needed",
        1,
    )[0]

    assert 'status: "{{ zbx_record.HOST_STATUS | default(0) | int }}"' in create_block
    assert "HOST_STATUS" not in update_block
    assert "\n        status:" not in update_block
