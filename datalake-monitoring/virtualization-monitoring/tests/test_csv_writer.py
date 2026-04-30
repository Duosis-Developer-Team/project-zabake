from pathlib import Path

from outputs.csv_writer import write_combined_csv


def test_write_combined_csv_with_bom_and_columns(tmp_path: Path):
    payload = {
        "generated_at": "2026-04-30T16:00:00+00:00",
        "targets": [
            {
                "rows": [
                    {
                        "source": "vmware",
                        "environment": "classic_vmware",
                        "vm_uuid": "u-1",
                        "vm_name": "vm-1",
                        "datalake_cluster": "km-a",
                        "loki_cluster": "km-a",
                        "cluster_match": "Y",
                        "customer": "cust",
                        "status": "in_both",
                    }
                ]
            }
        ],
    }

    csv_path = write_combined_csv(str(tmp_path), "run-1", payload)
    raw = Path(csv_path).read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")

    text = Path(csv_path).read_text(encoding="utf-8-sig")
    assert '"run_id","generated_at","source","environment","vm_uuid","vm_name","datalake_cluster","loki_cluster","cluster_match","customer","status"' in text
    assert '"run-1","2026-04-30T16:00:00+00:00","vmware","classic_vmware","u-1","vm-1","km-a","km-a","Y","cust","in_both"' in text
