from pathlib import Path

from jinja2 import Template


ENV_ORDER = ["classic_vmware", "hyperconv_vmware", "hyperconv_nutanix", "power_ibm", "unknown"]
MISMATCH_PRIORITIES = {"only_in_loki": 0, "cluster_mismatch": 1, "only_in_datalake": 2, "customer_mismatch": 3}


HTML_TEMPLATE = Template(
    """
<html>
  <body>
    <h2>Datalake VM/LPAR Reconciliation</h2>
    <p>Run ID: {{ run_id }}</p>
    <p>Generated At: {{ generated_at }}</p>
    <p>Window Days: {{ window_days }}</p>

    <h3>Environment Summary</h3>
    <table border="1" cellpadding="4" cellspacing="0">
      <thead>
        <tr>
          <th>Environment</th>
          <th>Loki Count</th>
          <th>Datalake Count</th>
          <th>In Both</th>
          <th>Only in Loki</th>
          <th>Only in Datalake</th>
          <th>Cluster Mismatch</th>
          <th>Customer Mismatch</th>
        </tr>
      </thead>
      <tbody>
    {% for env_name, env_summary in environment_summaries.items() %}
        <tr>
          <td>{{ env_name }}</td>
          <td>{{ env_summary.loki_count }}</td>
          <td>{{ env_summary.datalake_count }}</td>
          <td>{{ env_summary.in_both }}</td>
          <td>{{ env_summary.only_in_loki }}</td>
          <td>{{ env_summary.only_in_datalake }}</td>
          <td>{{ env_summary.cluster_mismatch }}</td>
          <td>{{ env_summary.customer_mismatch }}</td>
        </tr>
    {% endfor %}
      </tbody>
    </table>

    {% for env_name, rows in top_mismatches.items() %}
      <h3>Top 10 mismatches - {{ env_name }}</h3>
      {% if rows %}
      <table border="1" cellpadding="4" cellspacing="0">
        <thead>
          <tr>
            <th>VM Name</th>
            <th>Loki Cluster</th>
            <th>Datalake Cluster</th>
            <th>Customer</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for row in rows %}
          <tr>
            <td>{{ row.vm_name }}</td>
            <td>{{ row.loki_cluster }}</td>
            <td>{{ row.datalake_cluster }}</td>
            <td>{{ row.customer }}</td>
            <td>{{ row.status }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
      <p>No mismatch rows.</p>
      {% endif %}
    {% endfor %}

    <p>All rows are available in the attached CSV file.</p>
  </body>
</html>
"""
)


TEXT_TEMPLATE = Template(
    """
Datalake VM/LPAR Reconciliation
Run ID: {{ run_id }}
Generated At: {{ generated_at }}
Window Days: {{ window_days }}

Environment Summary
{% for env_name, env_summary in environment_summaries.items() -%}
- {{ env_name }}: loki={{ env_summary.loki_count }}, datalake={{ env_summary.datalake_count }}, in_both={{ env_summary.in_both }}, only_in_loki={{ env_summary.only_in_loki }}, only_in_datalake={{ env_summary.only_in_datalake }}, cluster_mismatch={{ env_summary.cluster_mismatch }}, customer_mismatch={{ env_summary.customer_mismatch }}
{% endfor %}

{% for env_name, rows in top_mismatches.items() -%}
Top 10 mismatches - {{ env_name }}
{% if rows -%}
{% for row in rows -%}
- {{ row.vm_name }} | loki={{ row.loki_cluster }} | datalake={{ row.datalake_cluster }} | customer={{ row.customer }} | status={{ row.status }}
{% endfor -%}
{% else -%}
- No mismatch rows
{% endif %}
{% endfor %}

All rows are available in the attached CSV file.
"""
)


def _build_environment_summaries(payload: dict) -> dict:
    summaries = {}
    all_rows = []
    for target in payload.get("targets", []):
        all_rows.extend(target.get("rows", []))

    for env_name in ENV_ORDER:
        env_rows = [row for row in all_rows if row.get("environment") == env_name]
        if not env_rows:
            continue
        summaries[env_name] = {
            "loki_count": sum(1 for row in env_rows if row.get("status") in {"only_in_loki", "in_both", "cluster_mismatch", "customer_mismatch"}),
            "datalake_count": sum(
                1 for row in env_rows if row.get("status") in {"only_in_datalake", "in_both", "cluster_mismatch", "customer_mismatch"}
            ),
            "in_both": sum(1 for row in env_rows if row.get("status") == "in_both"),
            "only_in_loki": sum(1 for row in env_rows if row.get("status") == "only_in_loki"),
            "only_in_datalake": sum(1 for row in env_rows if row.get("status") == "only_in_datalake"),
            "cluster_mismatch": sum(1 for row in env_rows if row.get("status") == "cluster_mismatch"),
            "customer_mismatch": sum(1 for row in env_rows if row.get("status") == "customer_mismatch"),
        }
    return summaries


def _build_top_mismatches(payload: dict) -> dict:
    all_rows = []
    for target in payload.get("targets", []):
        all_rows.extend(target.get("rows", []))

    top_by_env = {}
    for env_name in ENV_ORDER:
        env_rows = [
            row
            for row in all_rows
            if row.get("environment") == env_name and row.get("status") in {"only_in_loki", "cluster_mismatch", "only_in_datalake"}
        ]
        env_rows.sort(key=lambda row: (MISMATCH_PRIORITIES.get(row.get("status", ""), 99), row.get("vm_name", "")))
        top_by_env[env_name] = env_rows[:10]
    return top_by_env


def render_email_files(payload: dict, output_dir: str) -> dict:
    environment_summaries = _build_environment_summaries(payload)
    top_mismatches = _build_top_mismatches(payload)
    run_id = payload["run_id"]
    html = HTML_TEMPLATE.render(
        run_id=run_id,
        generated_at=payload.get("generated_at", ""),
        window_days=payload.get("window_days", ""),
        environment_summaries=environment_summaries,
        top_mismatches=top_mismatches,
    )
    text = TEXT_TEMPLATE.render(
        run_id=run_id,
        generated_at=payload.get("generated_at", ""),
        window_days=payload.get("window_days", ""),
        environment_summaries=environment_summaries,
        top_mismatches=top_mismatches,
    )
    output = Path(output_dir)
    html_file = output / f"vm_reconciliation_{run_id}.html"
    text_file = output / f"vm_reconciliation_{run_id}.txt"
    html_file.write_text(html, encoding="utf-8")
    text_file.write_text(text, encoding="utf-8")
    return {"html_file": str(html_file), "text_file": str(text_file)}
