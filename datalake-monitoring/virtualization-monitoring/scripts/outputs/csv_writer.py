import csv
from pathlib import Path


CSV_COLUMNS = [
    "run_id",
    "generated_at",
    "source",
    "environment",
    "vm_uuid",
    "vm_name",
    "datalake_cluster",
    "loki_cluster",
    "cluster_match",
    "customer",
    "status",
]


def write_combined_csv(output_dir: str, run_id: str, payload: dict) -> str:
    path = Path(output_dir) / f"vm_reconciliation_{run_id}.csv"
    rows = []
    for target in payload.get("targets", []):
        rows.extend(target.get("rows", []))

    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "run_id": run_id,
                    "generated_at": payload.get("generated_at", ""),
                    "source": row.get("source", ""),
                    "environment": row.get("environment", ""),
                    "vm_uuid": row.get("vm_uuid", ""),
                    "vm_name": row.get("vm_name", ""),
                    "datalake_cluster": row.get("datalake_cluster", ""),
                    "loki_cluster": row.get("loki_cluster", ""),
                    "cluster_match": row.get("cluster_match", ""),
                    "customer": row.get("customer", ""),
                    "status": row.get("status", ""),
                }
            )

    return str(path)
