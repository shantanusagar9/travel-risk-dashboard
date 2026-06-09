"""
generate_ondemand_pdf.py
Renders the single-country travel risk report to PDF using WeasyPrint + Jinja2.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS


def generate_country_pdf(report_data: dict, output_path: str = None) -> str:
    """
    Takes the structured report dict from Claude and renders it to PDF.
    Returns the output path.
    """
    if output_path is None:
        country_slug = report_data.get("country", "report").replace(" ", "_").lower()
        date_slug = datetime.now().strftime("%Y%m%d")
        output_path = f"Travel_Advisory_{country_slug}_{date_slug}.pdf"

    # Ensure generated_date is set
    if not report_data.get("generated_date"):
        report_data["generated_date"] = datetime.now().strftime("%d %B %Y")

    # Locate template — same directory as this script
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"])
    )
    template = env.get_template("report_template.html")

    html_content = template.render(data=report_data)

    # Render to PDF
    HTML(string=html_content, base_url=template_dir).write_pdf(
        output_path,
        stylesheets=[
            CSS(string="@page { size: A4; margin: 0; }")
        ]
    )

    print(f"  PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    import json
    with open("ondemand_report_data.json") as f:
        data = json.load(f)
    path = generate_country_pdf(data)
    print(f"PDF saved to: {path}")
