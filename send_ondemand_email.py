"""
send_ondemand_email.py
Sends a single-country travel risk report via Gmail SMTP.
Includes webpage link in email body.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

LEVEL_COLORS = {1: "#1a7a3f", 2: "#c47900", 3: "#c44a00", 4: "#a01010"}
LEVEL_BG     = {1: "#e8f5ee", 2: "#fef9ec", 3: "#fef0ea", 4: "#fdeaea"}
LEVEL_NAMES  = {1: "Low Risk", 2: "Moderate Risk", 3: "High Risk", 4: "Extreme Risk"}
LEVEL_LABELS = {
    1: "Exercise Normal Precautions",
    2: "Exercise Increased Caution",
    3: "Reconsider Travel",
    4: "Do Not Travel"
}


def build_email_html(report_data: dict, date_str: str, webpage_url: str) -> str:
    country = report_data.get("country", "")
    level   = report_data.get("advisory_level", 2)
    risk    = report_data.get("overall_risk", "Moderate")
    label   = report_data.get("advisory_label", LEVEL_LABELS.get(level, ""))
    city    = report_data.get("city_highlight", "")
    recs    = report_data.get("recommendations", [])[:3]

    color     = LEVEL_COLORS.get(level, "#c47900")
    bg        = LEVEL_BG.get(level, "#fef9ec")
    risk_name = LEVEL_NAMES.get(level, risk)
    city_line = f" · {city}" if city else ""

    rec_rows = ""
    for i, rec in enumerate(recs, 1):
        rec_rows += f"""
        <tr>
          <td style="padding:5px 0;font-size:13px;color:#444;font-family:Arial,sans-serif;line-height:1.5;">
            <span style="color:{color};font-weight:700;">{i}.</span> {rec}
          </td>
        </tr>"""

    webpage_btn = ""
    if webpage_url:
        webpage_btn = f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">
          <tr>
            <td align="center">
              <a href="{webpage_url}"
                 style="display:inline-block;background:#0f1f3d;color:#ffffff;
                        padding:13px 28px;border-radius:8px;text-decoration:none;
                        font-size:14px;font-weight:600;font-family:Arial,sans-serif;">
                View Full Report Online →
              </a>
            </td>
          </tr>
        </table>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#f4f6fb;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f6fb;">
    <tr><td align="center" style="padding:24px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#0f1f3d;padding:22px 28px;">
            <p style="margin:0;font-size:20px;font-weight:800;color:#fff;font-family:Arial,sans-serif;letter-spacing:-0.5px;">Across Assist</p>
            <p style="margin:4px 0 0;font-size:12px;color:#aabbcc;font-family:Arial,sans-serif;">Travel Advisory — {country}{city_line}</p>
          </td>
        </tr>

        <!-- Advisory Banner -->
        <tr>
          <td style="padding:20px 28px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:{bg};border-radius:8px;border-left:4px solid {color};">
              <tr>
                <td style="padding:14px 16px;">
                  <table cellpadding="0" cellspacing="0" border="0">
                    <tr>
                      <td style="width:46px;height:46px;background:{color};border-radius:50%;
                                 text-align:center;vertical-align:middle;">
                        <span style="font-size:20px;font-weight:900;color:#fff;font-family:Arial,sans-serif;">{level}</span>
                      </td>
                      <td style="padding-left:12px;">
                        <p style="margin:0;font-size:14px;font-weight:700;color:{color};font-family:Arial,sans-serif;">Level {level} — {label}</p>
                        <p style="margin:3px 0 0;font-size:11px;color:#666;font-family:Arial,sans-serif;">Overall Risk: <b>{risk_name}</b> · US State Department</p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Recommendations -->
        <tr>
          <td style="padding:18px 28px 0;">
            <p style="margin:0 0 8px;font-size:12px;font-weight:700;color:#0f1f3d;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:0.5px;">Top Recommendations</p>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">{rec_rows}</table>
          </td>
        </tr>

        <!-- Webpage CTA -->
        <tr><td style="padding:0 28px;">{webpage_btn}</td></tr>

        <!-- Attachment note -->
        <tr>
          <td style="padding:18px 28px 22px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#f4f6fb;border-radius:7px;border:1px solid #dde3ef;">
              <tr>
                <td style="padding:11px 14px;">
                  <p style="margin:0;font-size:12px;color:#555;font-family:Arial,sans-serif;line-height:1.6;">
                    📎 Full PDF report is attached. It includes risk assessments, current events, hospital listings, helplines, and travel recommendations.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:14px 28px;border-top:1px solid #eee;">
            <p style="margin:0;font-size:11px;color:#999;font-family:Arial,sans-serif;line-height:1.7;">
              Generated: {date_str}<br/>
              Source: US State Department · travel.state.gov<br/>
              For internal use only — Across Assist Private Limited
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_ondemand_report(pdf_path: str, report_data: dict, webpage_path: str = None):
    sender         = os.environ["SENDER_EMAIL"]
    recipients_raw = os.environ["RECIPIENT_EMAILS"]
    app_password   = os.environ["GMAIL_APP_PASSWORD"]
    github_username = os.environ.get("MY_GITHUB_USERNAME", "")

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    country  = report_data.get("country", "Unknown")
    now      = datetime.now()
    date_str = now.strftime("%d %B %Y, %I:%M %p IST")
    subject  = f"Travel Advisory — {country} · {now.strftime('%d %b %Y')}"

    # Build webpage URL if we have the path and username
    webpage_url = ""
    if webpage_path and github_username:
        slug = country.lower().replace(" ", "-").replace("_", "-")
        webpage_url = f"https://{github_username}.github.io/travel-risk-dashboard/{slug}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Across Assist Travel Risk <{sender}>"
    msg["To"]      = ", ".join(recipients)

    html_body = build_email_html(report_data, date_str, webpage_url)
    msg.attach(MIMEText(html_body, "html"))

    # Attach PDF
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = f"Travel_Advisory_{country.replace(' ','_')}_{now.strftime('%Y%m%d')}.pdf"
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    print(f"  Sending to: {', '.join(recipients)}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, recipients, msg.as_string())
    print("  Email sent successfully!")
