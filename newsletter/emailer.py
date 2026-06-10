"""Send the edition via Gmail SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import config

log = logging.getLogger(__name__)

# Email clients want self-contained styling. Gmail honors a <style> block in
# the head, with inline-friendly, conservative rules as the safety net.
EMAIL_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin: 0; padding: 0; background: #f6f1e7; }}
  .sheet {{
    max-width: 660px; margin: 0 auto; padding: 36px 28px 48px;
    background: #fbf7ee; color: #2b2620;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 17px; line-height: 1.65;
  }}
  h1 {{ font-size: 34px; line-height: 1.12; font-weight: 800; margin: 8px 0 6px;
       letter-spacing: -0.01em; }}
  h1 + p {{ font-size: 19px; line-height: 1.45; color: #564c3e; }}
  h2 {{ font-size: 15px; letter-spacing: 0.16em; text-transform: uppercase;
       font-weight: 800; border-top: 3px solid #211c16;
       padding-top: 10px; margin: 38px 0 14px; }}
  h3 {{ font-size: 22px; font-weight: 700; font-style: normal; margin: 26px 0 8px; }}
  h2:first-of-type + p::first-letter {{
    font-size: 56px; line-height: 0.85; font-weight: 800; float: left;
    padding: 3px 7px 0 0; color: #1f6e5c;
  }}
  a {{ color: #2a5b7d; }}
  em {{ color: #5a5044; }}
  li {{ margin-bottom: 8px; }}
  .meta {{ font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase;
          color: #8a7c66; margin-bottom: 4px; }}
  .footer {{ margin-top: 44px; padding-top: 14px; border-top: 1px solid #cdbfa5;
            font-size: 13px; color: #8a7c66; font-style: italic; }}
</style>
</head>
<body>
<div class="sheet">
<div class="meta">AI Update &middot; {date_long}</div>
{body}
<div class="footer">
  <p>Set twice weekly by machine, read by hand.{archive_link}</p>
</div>
</div>
</body>
</html>
"""


def send_edition(body_html: str, title: str, date_long: str, slug: str) -> None:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set — cannot send email."
        )

    archive_link = ""
    if config.SITE_BASE_URL:
        url = f"{config.SITE_BASE_URL.rstrip('/')}/editions/{slug}.html"
        archive_link = f' <a href="{url}">Read on the web</a>.'

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Update — {title}"
    msg["From"] = f"AI Update <{config.GMAIL_ADDRESS}>"
    msg["To"] = config.RECIPIENT_EMAIL

    plain = "Your AI Update edition is best read in an HTML-capable client."
    if config.SITE_BASE_URL:
        plain += f"\n\nRead it on the web: {config.SITE_BASE_URL.rstrip('/')}/editions/{slug}.html"
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(
        MIMEText(
            EMAIL_TEMPLATE.format(
                body=body_html, date_long=date_long, archive_link=archive_link
            ),
            "html",
        )
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        server.send_message(msg)
    log.info("email sent to %s", config.RECIPIENT_EMAIL)
