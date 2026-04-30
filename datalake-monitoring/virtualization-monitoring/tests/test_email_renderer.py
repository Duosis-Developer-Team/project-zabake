from pathlib import Path

from outputs.email_renderer import render_email_files


def test_render_email_files_contains_environment_summary_and_top_mismatch(tmp_path: Path):
    payload = {
        "run_id": "run-1",
        "generated_at": "2026-04-30T16:00:00+00:00",
        "window_days": 7,
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
                    },
                    {
                        "source": "vmware",
                        "environment": "classic_vmware",
                        "vm_uuid": "u-2",
                        "vm_name": "vm-2",
                        "datalake_cluster": "",
                        "loki_cluster": "km-a",
                        "cluster_match": "N/A",
                        "customer": "cust",
                        "status": "only_in_loki",
                    },
                ]
            }
        ],
    }

    files = render_email_files(payload, str(tmp_path))
    text = Path(files["text_file"]).read_text(encoding="utf-8")
    html = Path(files["html_file"]).read_text(encoding="utf-8")

    assert "Environment Summary" in text
    assert "classic_vmware: loki=2, datalake=1, in_both=1, only_in_loki=1" in text
    assert "Top 10 mismatches - classic_vmware" in text
    assert "All rows are available in the attached CSV file." in text
    assert "<h3>Environment Summary</h3>" in html
