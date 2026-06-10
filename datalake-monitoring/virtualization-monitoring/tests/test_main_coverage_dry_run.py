import json
import types
from pathlib import Path

from main import run_reconciliation


def _args(tmp_path, targets):
    fixtures = Path(__file__).parent / "fixtures"
    return types.SimpleNamespace(
        mode="vm-reconciliation",
        window_days=7,
        targets=targets,
        output_dir=str(tmp_path),
        gui_replay_enabled="false",
        input_file="",
        table="reconciliation_results",
        dry_run=True,
        fixtures_dir=str(fixtures),
    )


def test_dry_run_emits_coverage_targets(tmp_path):
    out = run_reconciliation(_args(tmp_path, "vmware_cluster,nutanix_cluster,ibm_host"))
    payload = json.loads(Path(out["output_file"]).read_text(encoding="utf-8"))
    cov = {t["target"]: t for t in payload["coverage_targets"]}

    assert cov["vmware_cluster"]["summary"]["in_both"] == 1
    assert cov["vmware_cluster"]["summary"]["only_in_loki"] == 1
    assert cov["nutanix_cluster"]["summary"]["in_both"] == 1
    assert cov["ibm_host"]["summary"]["only_in_datalake"] == 1
    assert cov["ibm_host"]["summary"]["only_in_loki"] == 1


def test_summary_file_includes_coverage_targets(tmp_path):
    out = run_reconciliation(_args(tmp_path, "vmware,vmware_cluster,ibm_host"))
    summary = json.loads(Path(out["summary_file"]).read_text(encoding="utf-8"))
    # both VM and coverage targets appear in the summary file
    assert "vmware" in summary
    assert "vmware_cluster" in summary
    assert "ibm_host" in summary
    assert summary["vmware_cluster"]["in_both"] == 1


def test_dry_run_vm_targets_unaffected_by_coverage(tmp_path):
    out = run_reconciliation(_args(tmp_path, "vmware,vmware_cluster"))
    payload = json.loads(Path(out["output_file"]).read_text(encoding="utf-8"))
    vm_targets = {t["target"] for t in payload["targets"]}
    cov_targets = {t["target"] for t in payload["coverage_targets"]}
    assert vm_targets == {"vmware"}
    assert cov_targets == {"vmware_cluster"}
