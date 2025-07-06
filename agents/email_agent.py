import smtplib
import ssl
import os
from typing import List, Dict, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
from datetime import datetime
import markdown2
import logging

logger = logging.getLogger(__name__)

class EmailAgent:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587, **kwargs):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port



    def create_html(self, event_name: str, invitation_text: str) -> str:
        return f"""
        <html>
        <head>
        <style>
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
        .container {{ background: #fff; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #d63384; }}
        </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 You're Invited to {event_name}! 🎉</h1>
                <p>{invitation_text.replace('\n', '<br>')}</p>
                <hr>
                <footer><em>Sent via EventPlanGenie ✨</em></footer>
            </div>
        </body>
        </html>
        """

    def markdown_to_pdf(self, markdown_text: str, output_path: str = "output.pdf") -> str:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in markdown_text.splitlines():
            pdf.multi_cell(0, 10, line)
        pdf.output(output_path)
        return output_path

    def generate_ics(self, event_name: str, start: str, end: str, location: str) -> str:
        dt_start = datetime.strptime(start, "%Y-%m-%d")
        dt_end = datetime.strptime(end, "%Y-%m-%d")
        dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

        return f"""
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//EventPlanGenie//EN
BEGIN:VEVENT
DTSTAMP:{dtstamp}
DTSTART;VALUE=DATE:{dt_start.strftime('%Y%m%d')}
DTEND;VALUE=DATE:{dt_end.strftime('%Y%m%d')}
SUMMARY:{event_name}
LOCATION:{location}
DESCRIPTION:Generated using EventPlanGenie
END:VEVENT
END:VCALENDAR
        """

    def send_email(
        self,
        sender_email: str,
        sender_password: str,
        recipient_emails: List[str],
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        results = []

        for recipient in recipient_emails:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = recipient

                msg.attach(MIMEText(text_content, "plain"))
                if html_content:
                    msg.attach(MIMEText(html_content, "html"))

                if attachments:
                    for file_path in attachments:
                        if os.path.isfile(file_path):
                            with open(file_path, "rb") as f:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(f.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    "Content-Disposition",
                                    f"attachment; filename={os.path.basename(file_path)}"
                                )
                                msg.attach(part)

                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(sender_email, sender_password)
                    server.send_message(msg)

                results.append({
                    "email": recipient,
                    "success": True,
                    "message": "Email sent successfully"
                })

            except Exception as e:
                logger.error(f"Failed to send to {recipient}: {e}")
                results.append({
                    "email": recipient,
                    "success": False,
                    "error": str(e)
                })

        return results

    def send_invitation(
        self,
        sender_email: str,
        sender_password: str,
        event_name: str,
        invitation_text: str,
        recipients: List[str],
        attachments: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        html_version = self.create_html(event_name, invitation_text)
        subject = f"You're Invited: {event_name}"
        return self.send_email(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_emails=recipients,
            subject=subject,
            text_content=invitation_text,
            html_content=html_version,
            attachments=attachments
        )

    def send_bulk_email(
        self,
        sender_email: str,
        sender_password: str,
        recipient_emails: List[str],
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        return self.send_email(
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_emails=recipient_emails,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            attachments=attachments
        )
