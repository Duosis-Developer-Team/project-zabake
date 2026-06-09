"""Tests for deploy_collector_scripts manifest builder."""

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROLE_FILES = (
    Path(__file__).resolve().parents[1]
    / "playbooks/roles/datalake_collector_sync/files"
)
sys.path.insert(0, str(ROLE_FILES))

from deploy_collector_scripts import local_dir, remote_dir  # noqa: E402


def test_remote_dir_strips_datalake_prefix():
    assert remote_dir(
        "datalake/collectors/VMware/vmware_data_collector.py",
        "/Datalake_Project",
    ) == "/Datalake_Project/VMware"


def test_local_dir_resolves_under_src_root(tmp_path):
    src = tmp_path / "collectors"
    (src / "IBM").mkdir(parents=True)
    path = local_dir("datalake/collectors/IBM/ibm_data_collector.py", src)
    assert path == src / "IBM"


def test_manifest_cli(tmp_path):
    collector_types = tmp_path / "collector_types.yml"
    collector_types.write_text(
        yaml.safe_dump(
            {
                "VmWare": {
                    "script_path": "datalake/collectors/VMware/vmware_data_collector.py",
                }
            }
        ),
        encoding="utf-8",
    )
    src = tmp_path / "collectors"
    (src / "VMware").mkdir(parents=True)
    (src / "VMware" / "vmware_data_collector.py").write_text("# stub", encoding="utf-8")
    out = tmp_path / "manifest.json"
    script = ROLE_FILES / "deploy_collector_scripts.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--collector-types",
            str(collector_types),
            "--src",
            str(src),
            "--types",
            "VmWare",
            "--manifest-output",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["count"] == 1
    assert data["deploy_paths"][0]["dest"] == "/Datalake_Project/VMware"
