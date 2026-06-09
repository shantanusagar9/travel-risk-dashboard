"""
send_ondemand_email.py
Sends a single-country travel risk report via Gmail SMTP.
Reuses the same SMTP setup as send_email.py.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

LEVEL_COLORS = {1: "#2E7D32", 2: "#F57F17", 3: "#E65100", 4: "#B71C1C"}
LEVEL_BG     = {1: "#E8F5E9", 2: "#FFF8E1", 3: "#FBE9E7", 4: "#FFEBEE"}
LEVEL_NAMES  = {1: "Low Risk", 2: "Moderate Risk", 3: "High Risk", 4: "Extreme Risk"}
LEVEL_LABELS = {
    1: "Exercise Normal Precautions",
    2: "Exercise Increased Caution",
    3: "Reconsider Travel",
    4: "Do Not Travel"
}


def build_ondemand_email_html(report_data: dict, date_str: str) -> str:
    country = report_data.get("country", "")
    level   = report_data.get("advisory_level", 2)
    risk    = report_data.get("overall_risk", "Moderate")
    label   = report_data.get("advisory_label", LEVEL_LABELS.get(level, ""))
    city    = report_data.get("city_highlight", "")
    summary_items = report_data.get("recommendations", [])[:3]

    color  = LEVEL_COLORS.get(level, "#F57F17")
    bg     = LEVEL_BG.get(level, "#FFF8E1")
    risk_label = LEVEL_NAMES.get(level, risk)

    rec_rows = ""
    for i, rec in enumerate(summary_items, 1):
        rec_rows += f"""
        <tr>
          <td style="padding:4px 0; font-size:13px; color:#444; font-family:Arial,sans-serif;">
            <span style="color:{color}; font-weight:700;">{i}.</span> {rec}
          </td>
        </tr>"""

    city_line = f" · {city}" if city else ""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0; padding:0; background-color:#f0f2f5; font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f0f2f5;">
    <tr>
      <td align="center" style="padding:24px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="max-width:560px; background:#ffffff; border-radius:12px;
                      overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:#1a1a2e; padding:24px 28px;">
              <p style="margin:0; font-size:22px; font-weight:700; color:#ffffff; font-family:Arial,sans-serif;">Across Assist</p>
              <p style="margin:4px 0 0; font-size:13px; color:#aabbcc; font-family:Arial,sans-serif;">Travel Advisory — {country}{city_line}</p>
            </td>
          </tr>

          <!-- Advisory Level Block -->
          <tr>
            <td style="padding:0 28px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="margin:20px 0; background:{bg}; border-radius:8px; border-left:4px solid {color};">
                <tr>
                  <td style="padding:16px 18px;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="width:48px; height:48px; background:{color}; border-radius:50%;
                                   text-align:center; vertical-align:middle;">
                          <span style="font-size:22px; font-weight:800; color:#fff; font-family:Arial,sans-serif; line-height:48px;">{level}</span>
                        </td>
                        <td style="padding-left:14px;">
                          <p style="margin:0; font-size:15px; font-weight:700; color:{color}; font-family:Arial,sans-serif;">
                            Level {level} — {label}
                          </p>
                          <p style="margin:3px 0 0; font-size:12px; color:#666; font-family:Arial,sans-serif;">
                            Overall Risk: <b>{risk_label}</b> · US State Department
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Top Recommendations -->
          <tr>
            <td style="padding:0 28px 20px;">
              <p style="margin:0 0 10px; font-size:13px; font-weight:700; color:#1a1a2e; font-family:Arial,sans-serif;">
                Top Recommendations
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {rec_rows}
              </table>
            </td>
          </tr>

          <!-- Attachment Note -->
          <tr>
            <td style="padding:0 28px 24px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0;">
                <tr>
                  <td style="padding:12px 16px;">
                    <p style="margin:0; font-size:12px; color:#555; font-family:Arial,sans-serif; line-height:1.6;">
                      📎 The full detailed report (PDF) is attached to this email.<br/>
                      It includes risk assessments, current events, hospital listings, helplines, and travel recommendations.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 28px; border-top:1px solid #eeeeee;">
              <p style="margin:0; font-size:11px; color:#999; font-family:Arial,sans-serif; line-height:1.7;">
                Generated: {date_str}<br/>
                Source: US State Department · travel.state.gov<br/>
                For internal use only — Across Assist Private Limited
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_ondemand_report(pdf_path: str, report_data: dict):
    sender       = os.environ["SENDER_EMAIL"]
    recipients_raw = os.environ["RECIPIENT_EMAILS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    country  = report_data.get("country", "Unknown")
    now      = datetime.now()
    date_str = now.strftime("%d %B %Y, %I:%M %p IST")
    subject  = f"Travel Advisory Report — {country} · {now.strftime('%d %b %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Across Assist Travel Risk <{sender}>"
    msg["To"]      = ", ".join(recipients)

    html_body = build_ondemand_email_html(report_data, date_str)
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

    print(f"  Sending report to: {', '.join(recipients)}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, recipients, msg.as_string())
    print("  Email sent successfully!")


if __name__ == "__main__":
    import json
    with open("ondemand_report_data.json") as f:
        data = json.load(f)
    send_ondemand_report("travel_risk_report.pdf", data)
