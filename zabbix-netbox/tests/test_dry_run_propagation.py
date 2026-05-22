"""Ensure dry_run is passed into zabbix_host_operations and hostgroup.create is guarded."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _zabbix_include_block(tasks_text: str, marker: str) -> str:
    start = tasks_text.index(marker)
    chunk = tasks_text[start : start + 1200]
    return chunk.split("when:", 1)[0]


APPLY_FILES = (
    "playbooks/roles/netbox_zabbix_sync/tasks/process_device_apply.yml",
    "playbooks/roles/netbox_zabbix_sync/tasks/process_platform_apply.yml",
    "playbooks/roles/netbox_zabbix_sync/tasks/process_virtual_fw_apply.yml",
)

LEGACY_FILES = (
    "playbooks/roles/netbox_zabbix_sync/tasks/process_device.yml",
    "playbooks/roles/netbox_zabbix_sync/tasks/process_platform.yml",
    "playbooks/roles/netbox_zabbix_sync/tasks/process_virtual_fw.yml",
)


def test_apply_paths_use_plan_payloads_not_zabbix_host_operations():
    for rel in APPLY_FILES:
        text = read_text(rel)
        assert "include_tasks: zabbix_host_operations.yml" not in text, rel
        assert "host.create" in text or "host.create from plan" in text.lower() or 'method: "host.create"' in text or "method: host.create" in text
        assert "dry_run | default(false) | bool" in text, rel


def test_legacy_paths_pass_dry_run_into_zabbix_host_operations():
    for rel in LEGACY_FILES:
        block = _zabbix_include_block(
            read_text(rel),
            "include_tasks: zabbix_host_operations.yml",
        )
        assert 'dry_run: "{{ dry_run | default(false) | bool }}"' in block, rel


def test_hostgroup_create_respects_dry_run():
    ops = read_text("playbooks/roles/netbox_zabbix_sync/tasks/zabbix_host_operations.yml")
    assert ops.count("method: \"hostgroup.create\"") == 2
    assert ops.count("not (dry_run | default(false) | bool)") >= 2


def test_main_normalizes_dry_run_at_start():
    main = read_text("playbooks/roles/netbox_zabbix_sync/tasks/main.yml")
    assert "Normalize dry_run flag" in main
    assert 'dry_run: "{{ dry_run | default(false) | bool }}"' in main
