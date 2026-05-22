"""Regression: NetBox entity fetch must complete before Phase A compare engine."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_YML = REPO_ROOT / "playbooks/roles/netbox_zabbix_sync/tasks/main.yml"
RUN_PARALLEL_COMPARE = REPO_ROOT / "playbooks/roles/netbox_zabbix_sync/tasks/run_parallel_compare.yml"
PLATFORM_APPLY = REPO_ROOT / "playbooks/roles/netbox_zabbix_sync/tasks/process_platform_apply.yml"
VFW_APPLY = REPO_ROOT / "playbooks/roles/netbox_zabbix_sync/tasks/process_virtual_fw_apply.yml"


def _line_number(text: str, needle: str) -> int:
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return idx
    raise AssertionError(f"Pattern not found: {needle!r}")


def test_platform_fetch_before_phase_a_compare():
    text = MAIN_YML.read_text(encoding="utf-8")
    platform_fetch = _line_number(text, "include_tasks: fetch_all_platforms.yml")
    phase_a = _line_number(text, "include_tasks: run_parallel_compare.yml")
    assert platform_fetch < phase_a, (
        f"fetch_all_platforms.yml (line {platform_fetch}) must appear before "
        f"run_parallel_compare.yml (line {phase_a})"
    )


def test_empty_platform_list_set_fact_before_phase_a():
    text = MAIN_YML.read_text(encoding="utf-8")
    empty_platforms = _line_number(text, "Set empty NetBox platform list when platform sync is disabled")
    phase_a = _line_number(text, "include_tasks: run_parallel_compare.yml")
    assert empty_platforms < phase_a


def test_phase_a_cleanup_includes_platform_and_vfw_plans():
    text = MAIN_YML.read_text(encoding="utf-8")
    cleanup = _line_number(text, "Clean up leftover compare plan and result temp files")
    phase_a = _line_number(text, "include_tasks: run_parallel_compare.yml")
    assert cleanup < phase_a
    block = text.splitlines()[cleanup - 1 : cleanup + 5]
    joined = "\n".join(block)
    assert "platform_plan_*.json" in joined
    assert "vfw_plan_*.json" in joined


def test_compare_summary_loaded_from_file_not_stdout_parse():
    text = RUN_PARALLEL_COMPARE.read_text(encoding="utf-8")
    assert "compare_summary.json" in text
    assert "Load compare engine summary from file" in text
    assert "parsed.type is defined and parsed.type == 'summary'" not in text


def test_platform_apply_graceful_missing_plan():
    text = PLATFORM_APPLY.read_text(encoding="utf-8")
    assert "Check platform sync plan file exists" in text
    assert "Record missing platform plan" in text
    assert "lookup('file'" in text
    assert "Phase A plan missing" in text


def test_vfw_apply_graceful_missing_plan():
    text = VFW_APPLY.read_text(encoding="utf-8")
    assert "Check VFW sync plan file exists" in text
    assert "Record missing VFW plan" in text
    assert "Phase A plan missing" in text
