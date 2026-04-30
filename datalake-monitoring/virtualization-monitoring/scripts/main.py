import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from matchers.keys import normalize_name
from outputs.csv_writer import write_combined_csv
from outputs.db_writer import upsert_reconciliation_results
from outputs.email_renderer import render_email_files
from outputs.json_writer import write_json_report
from reconcilers import IbmLparReconciler, NutanixVmReconciler, VmwareVmReconciler
from settings import load_settings
from sql_loader.datalake_queries import (
    fetch_ibm_lpars,
    fetch_nutanix_cluster_set,
    fetch_nutanix_vms,
    fetch_vmware_cluster_set,
    fetch_vmware_vms,
)
from sql_loader.gui_replay import build_gui_replay_snapshot
from sql_loader.netbox_queries import fetch_netbox_vm_inventory
from utils.db import connect
from utils.logging import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VM/LPAR reconciliation runner.")
    parser.add_argument("--mode", required=True, choices=["vm-reconciliation", "render-email", "upsert-reconciliation"])
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--targets", default="vmware,nutanix,ibm_lpar")
    parser.add_argument("--output-dir", default="/tmp/vm_reconciliation")
    parser.add_argument("--gui-replay-enabled", default="true")
    parser.add_argument("--input-file", default="")
    parser.add_argument("--table", default="reconciliation_results")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixtures-dir", default="")
    return parser.parse_args()


def run_reconciliation(args: argparse.Namespace) -> dict:
    settings = load_settings()
    configure_logging(settings.log_level)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_names = [item.strip() for item in args.targets.split(",") if item.strip()]
    targets = []
    gui_replay = {}
    vmware_cluster_set = set()
    nutanix_cluster_set = set()
    ibm_lpar_name_set = set()
    if args.dry_run:
        fixtures = Path(args.fixtures_dir)
        netbox_rows = json.loads((fixtures / "netbox_rows.json").read_text(encoding="utf-8"))
        vmware_cluster_file = fixtures / "vmware_clusters.json"
        nutanix_cluster_file = fixtures / "nutanix_clusters.json"
        if vmware_cluster_file.exists():
            vmware_cluster_set = set(json.loads(vmware_cluster_file.read_text(encoding="utf-8")))
        if nutanix_cluster_file.exists():
            nutanix_cluster_set = set(json.loads(nutanix_cluster_file.read_text(encoding="utf-8")))
        if "vmware" in target_names:
            rows = json.loads((fixtures / "vmware_rows.json").read_text(encoding="utf-8"))
            vmware_cluster_set = vmware_cluster_set or {
                str(row.get("cluster")).strip() for row in rows if str(row.get("cluster") or "").strip()
            }
            targets.append(("vmware", rows))
        if "nutanix" in target_names:
            rows = json.loads((fixtures / "nutanix_rows.json").read_text(encoding="utf-8"))
            nutanix_cluster_set = nutanix_cluster_set or {
                str(row.get("cluster")).strip() for row in rows if str(row.get("cluster") or "").strip()
            }
            targets.append(("nutanix", rows))
        if "ibm_lpar" in target_names:
            rows = json.loads((fixtures / "ibm_lpar_rows.json").read_text(encoding="utf-8"))
            ibm_lpar_name_set = {normalize_name(row.get("lparname")) for row in rows if normalize_name(row.get("lparname"))}
            targets.append(("ibm_lpar", rows))
        if args.gui_replay_enabled.lower() == "true":
            gui_replay = {
                "source": "internal_sql_replay",
                "vmware_distinct_vm_count": 0,
                "nutanix_distinct_vm_count": 0,
                "ibm_distinct_lpar_count": 0,
                "window_days": args.window_days,
                "note": "dry-run mode uses fixtures and skips live SQL replay counts",
            }
    else:
        with connect(settings.datalake_db) as dl_conn, connect(settings.netbox_db) as nb_conn:
            netbox_rows = fetch_netbox_vm_inventory(nb_conn)
            vmware_cluster_set = fetch_vmware_cluster_set(dl_conn, args.window_days)
            nutanix_cluster_set = fetch_nutanix_cluster_set(dl_conn, args.window_days)
            if "vmware" in target_names:
                rows = fetch_vmware_vms(dl_conn, args.window_days)
                targets.append(("vmware", rows))
            if "nutanix" in target_names:
                rows = fetch_nutanix_vms(dl_conn, args.window_days)
                targets.append(("nutanix", rows))
            if "ibm_lpar" in target_names:
                rows = fetch_ibm_lpars(dl_conn, args.window_days)
                ibm_lpar_name_set = {normalize_name(row.get("lparname")) for row in rows if normalize_name(row.get("lparname"))}
                targets.append(("ibm_lpar", rows))
            if args.gui_replay_enabled.lower() == "true":
                gui_replay = build_gui_replay_snapshot(dl_conn, args.window_days)

    reconciler_options = {
        "vmware_cluster_set": vmware_cluster_set,
        "nutanix_cluster_set": nutanix_cluster_set,
        "ibm_lpar_name_set": ibm_lpar_name_set,
    }
    reconciled_targets = []
    for source_name, rows in targets:
        if source_name == "vmware":
            reconciled_targets.append(VmwareVmReconciler(**reconciler_options).reconcile(rows, netbox_rows))
        elif source_name == "nutanix":
            reconciled_targets.append(NutanixVmReconciler(**reconciler_options).reconcile(rows, netbox_rows))
        elif source_name == "ibm_lpar":
            reconciled_targets.append(IbmLparReconciler(**reconciler_options).reconcile(rows, netbox_rows))
    targets = reconciled_targets

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
    payload = {
        "run_id": run_id,
        "window_days": args.window_days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets": targets,
        "gui_replay": gui_replay,
    }
    report_file = write_json_report(args.output_dir, run_id, payload)
    csv_file = write_combined_csv(args.output_dir, run_id, payload)
    summary_file = str(output_dir / f"vm_reconciliation_{run_id}_summary.json")
    summary_payload = {item["target"]: item["summary"] for item in targets}
    Path(summary_file).write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    return {"output_file": report_file, "summary_file": summary_file, "csv_file": csv_file}


def render_email(args: argparse.Namespace) -> dict:
    payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    return render_email_files(payload, args.output_dir)


def run_upsert(args: argparse.Namespace) -> dict:
    settings = load_settings()
    payload = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    with connect(settings.reconciliation_db) as rc_conn:
        upsert_reconciliation_results(rc_conn, args.table, payload, payload.get("window_days", 7))
    return {"status": "ok", "table": args.table}


def main() -> int:
    args = parse_args()
    if args.mode == "vm-reconciliation":
        print(json.dumps(run_reconciliation(args)))
        return 0
    if args.mode == "render-email":
        print(json.dumps(render_email(args)))
        return 0
    print(json.dumps(run_upsert(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
