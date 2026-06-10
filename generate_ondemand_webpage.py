"""
generate_ondemand_webpage.py
Renders the single-country travel risk report as an HTML webpage
and saves it to docs/<countryslug>.html for GitHub Pages.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def generate_country_webpage(report_data: dict) -> str:
    """
    Renders report_data to an HTML file in docs/<country>.html
    Returns the output path.
    """
    country = report_data.get("country", "report")
    country_slug = country.lower().replace(" ", "-").replace("_", "-")

    # Ensure docs/ directory exists
    os.makedirs("docs", exist_ok=True)
    output_path = f"docs/{country_slug}.html"

    # Ensure generated_date is set
    if not report_data.get("generated_date"):
        report_data["generated_date"] = datetime.now().strftime("%d %B %Y")

    # Locate template — same directory as this script
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"])
    )
    template = env.get_template("webpage_template.html")
    html_content = template.render(data=report_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  Webpage saved: {output_path}")
    return output_path


if __name__ == "__main__":
    import json
    with open("ondemand_report_data.json") as f:
        data = json.load(f)
    path = generate_country_webpage(data)
    print(f"Webpage saved to: {path}")
