"""
generate_ondemand_report.py
Generates a detailed single-country travel risk report on demand.
Outputs: PDF (emailed) + HTML webpage (committed to docs/ for GitHub Pages)
"""

import anthropic
import json
import os
import sys
from datetime import datetime
from generate_ondemand_pdf import generate_country_pdf
from generate_ondemand_webpage import generate_country_webpage
from send_ondemand_email import send_ondemand_report

SYSTEM_PROMPT = """You are a senior corporate travel risk analyst producing detailed country briefings for multinational companies.

For the country requested, use web search to gather current information and produce a comprehensive travel risk report.

You MUST respond with a single valid JSON object and nothing else. No markdown, no backticks, no preamble, no explanation.

The JSON must follow this exact structure:
{
  "country": "<country name>",
  "city_highlight": "<most visited/relevant city for business travel>",
  "advisory_level": <1|2|3|4>,
  "advisory_label": "<Exercise Normal Precautions|Exercise Increased Caution|Reconsider Travel|Do Not Travel>",
  "overall_risk": "<Low|Moderate|High|Extreme>",
  "generated_date": "<DD Month YYYY>",

  "overview": {
    "capital": "<capital city>",
    "population": "<population with unit, e.g. 47.4 million>",
    "language": "<primary official language(s)>",
    "currency": "<currency name and code>",
    "timezone": "<timezone, e.g. CET (UTC+1)>",
    "brief": "<2 sentences about the country relevant to business travellers>"
  },

  "key_features": [
    "<fact 1 relevant to business travellers>",
    "<fact 2>",
    "<fact 3>",
    "<fact 4>"
  ],

  "key_risks": [
    "<primary risk 1 with brief context>",
    "<primary risk 2>",
    "<primary risk 3>",
    "<primary risk 4>"
  ],

  "sections": {
    "civil_unrest": {
      "level": "<Low|Moderate|High>",
      "summary": "<2-3 sentences on current protest/unrest situation>",
      "hotspots": ["<area or city>", "<area or city>"]
    },
    "womens_safety": {
      "level": "<Low|Moderate|High>",
      "summary": "<2-3 sentences on safety situation for women travellers>",
      "tips": ["<practical tip 1>", "<practical tip 2>"]
    },
    "air_pollution": {
      "level": "<Low|Moderate|High>",
      "aqi_range": "<typical AQI range or description>",
      "worst_months": "<months when pollution peaks>",
      "summary": "<1-2 sentences>"
    },
    "terrorism": {
      "level": "<Low|Moderate|High>",
      "summary": "<2-3 sentences on terrorism threat level and recent incidents if any>",
      "high_risk_areas": ["<area>", "<area>"]
    },
    "crime": {
      "level": "<Low|Moderate|High>",
      "summary": "<2-3 sentences on crime situation>",
      "common_crimes": ["<crime type>", "<crime type>"],
      "high_risk_areas": ["<area>", "<area>"]
    },
    "health": {
      "level": "<Low|Moderate|High>",
      "summary": "<2 sentences on health risks>",
      "vaccinations": ["<recommended vaccine>", "<recommended vaccine>"],
      "water_safe": true
    },
    "road_safety": {
      "level": "<Low|Moderate|High>",
      "summary": "<2 sentences on road conditions and driving risks>"
    },
    "natural_disasters": {
      "level": "<Low|Moderate|High>",
      "summary": "<2 sentences on natural disaster risks relevant to this country>"
    }
  },

  "business_hubs": [
    "<city or district name>",
    "<city or district name>",
    "<city or district name>",
    "<city or district name>"
  ],

  "hospitals": [
    {"name": "<hospital name>", "city": "<city>"},
    {"name": "<hospital name>", "city": "<city>"},
    {"name": "<hospital name>", "city": "<city>"}
  ],

  "emergency_numbers": {
    "police": "<number only, max 10 chars, e.g. 091 or 999>",
    "ambulance": "<number only, max 10 chars>",
    "fire": "<number only, max 10 chars>",
    "tourist_helpline": "<number only, max 10 chars, or N/A>",
    "emergency": "<single emergency number only, e.g. 112>"
  },

  "useful_apps": [
    {"category": "Transport", "apps": ["<app name>", "<app name>"]},
    {"category": "Food", "apps": ["<app name>", "<app name>"]},
    {"category": "Maps", "apps": ["<app name>"]},
    {"category": "Payment", "apps": ["<app name>", "<app name>"]}
  ],

  "recommendations": [
    "<specific actionable recommendation 1>",
    "<specific actionable recommendation 2>",
    "<specific actionable recommendation 3>",
    "<specific actionable recommendation 4>",
    "<specific actionable recommendation 5>",
    "<specific actionable recommendation 6>"
  ],

  "current_events": [
    {
      "title": "<headline of current relevant event>",
      "category": "<Civil Disturbance|Health|Security|Regulatory|Natural Disaster>",
      "risk_level": "<Low|Medium|High>",
      "description": "<2-3 sentences describing the event and its impact on travellers>"
    }
  ],

  "best_time_to_visit": "<max 2 sentences, months only e.g. March–May and Sept–Nov>",
  "visa_requirement": "<brief visa info for Indian passport holders>"
}

Use web search to ensure all current_events are real and recent. Advisory level must reflect the current US State Department classification found via web search."""


def classify_country(country_name: str) -> dict:
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"  Generating report for: {country_name}")
    print(f"  Using model: claude-sonnet-4-6 with web search...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                f"Generate a complete travel risk report for: {country_name}. "
                f"Search for the current US State Department advisory level, recent events, "
                f"and current conditions. Return only the JSON object."
            )
        }]
    )

    # Extract text from response
    text = ""
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()

    # Strip markdown fences if present
    if "```" in text:
        for part in text.split("```"):
            if "{" in part:
                text = part.replace("json", "").strip()
                break

    # Extract JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    data = json.loads(text)

    # Validate advisory level
    if not isinstance(data.get("advisory_level"), int) or data["advisory_level"] not in [1, 2, 3, 4]:
        data["advisory_level"] = 2

    print(f"  Advisory Level: {data.get('advisory_level')} — {data.get('overall_risk')}")
    return data


def main():
    country = os.environ.get("COUNTRY_NAME", "").strip()
    if not country:
        if len(sys.argv) > 1:
            country = " ".join(sys.argv[1:]).strip()
    if not country:
        print("ERROR: No country specified. Set COUNTRY_NAME env var or pass as argument.")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  ON-DEMAND TRAVEL RISK REPORT")
    print(f"  Country: {country}")
    print(f"  Started: {datetime.now().strftime('%d %b %Y %H:%M IST')}")
    print(f"{'='*50}\n")

    # Step 1: Generate content via Claude
    print("[1/4] Fetching live data and generating report content...")
    report_data = classify_country(country)

    # Save JSON for debugging
    with open("ondemand_report_data.json", "w") as f:
        json.dump(report_data, f, indent=2)
    print("  Report data saved.")

    # Step 2: Generate PDF
    print("\n[2/4] Generating PDF...")
    pdf_path = generate_country_pdf(report_data)

    # Step 3: Generate webpage
    print("\n[3/4] Generating webpage...")
    webpage_path = generate_country_webpage(report_data)
    print(f"  Webpage saved: {webpage_path}")

    # Step 4: Send email
    print("\n[4/4] Sending email...")
    send_ondemand_report(pdf_path, report_data, webpage_path)

    print(f"\n{'='*50}")
    print(f"  REPORT COMPLETE: {country}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
