from pathlib import Path

from jinja2 import Template


HTML_TEMPLATE = Template(
    """
<html>
  <body>
    <h2>Datalake VM/LPAR Reconciliation</h2>
    <p>Run ID: {{ run_id }}</p>
    <ul>
    {% for target, summary in summaries.items() %}
      <li>{{ target }}: datalake={{ summary.datalake_count }}, netbox={{ summary.netbox_count }}, only_datalake={{ summary.only_in_datalake }}, only_netbox={{ summary.only_in_netbox }}</li>
    {% endfor %}
    </ul>
  </body>
</html>
"""
)


TEXT_TEMPLATE = Template(
    """
Datalake VM/LPAR Reconciliation
Run ID: {{ run_id }}
{% for target, summary in summaries.items() -%}
- {{ target }}: datalake={{ summary.datalake_count }}, netbox={{ summary.netbox_count }}, only_datalake={{ summary.only_in_datalake }}, only_netbox={{ summary.only_in_netbox }}
{% endfor %}
"""
)


def render_email_files(payload: dict, output_dir: str) -> dict:
    summaries = {item["target"]: item["summary"] for item in payload["targets"]}
    run_id = payload["run_id"]
    html = HTML_TEMPLATE.render(run_id=run_id, summaries=summaries)
    text = TEXT_TEMPLATE.render(run_id=run_id, summaries=summaries)
    output = Path(output_dir)
    html_file = output / f"vm_reconciliation_{run_id}.html"
    text_file = output / f"vm_reconciliation_{run_id}.txt"
    html_file.write_text(html, encoding="utf-8")
    text_file.write_text(text, encoding="utf-8")
    return {"html_file": str(html_file), "text_file": str(text_file)}
