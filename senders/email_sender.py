"""Email Sender Module"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends summaries via email"""

    def __init__(self):
        """Initialize email sender with credentials from environment"""
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.receiver_email = os.getenv('EMAIL_RECEIVER')

        if not all([self.sender_email, self.sender_password, self.receiver_email]):
            logger.warning("Email credentials not fully configured")

    def send(self, subject: str, content: str, html: bool = False) -> bool:
        """
        Send email

        Args:
            subject: Email subject
            content: Email content (text or HTML)
            html: Whether content is HTML (default: False)

        Returns:
            True if sent successfully, False otherwise
        """
        if not all([self.sender_email, self.sender_password, self.receiver_email]):
            logger.error("Email credentials not configured")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = self.receiver_email

            # Add content
            if html:
                part = MIMEText(content, "html")
            else:
                part = MIMEText(content, "plain")

            message.attach(part)

            # Send email (Gmail example)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    self.receiver_email,
                    message.as_string()
                )

            logger.info(f"Email sent successfully to {self.receiver_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def send_summary(self, summary: str, num_items: int = 0) -> bool:
        """
        Send daily summary email

        Args:
            summary: Summarized content
            num_items: Number of items collected

        Returns:
            True if sent successfully
        """
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"📰 Daily Content Summary - {today} ({num_items} items)"

        # Convert to HTML for better formatting
        html_content = self._markdown_to_html(summary, num_items)

        return self.send(subject, html_content, html=True)

    def _markdown_to_html(self, summary: str, num_items: int) -> str:
        """Convert markdown summary to HTML email"""
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #1a1a1a;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #2c3e50;
                    margin-top: 25px;
                }}
                h3 {{
                    color: #34495e;
                }}
                a {{
                    color: #007bff;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .meta {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .summary-content {{
                    white-space: pre-wrap;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📰 Daily Content Summary</h1>
                <div class="meta">
                    Generated: {today} | Items collected: {num_items}
                </div>
                <div class="summary-content">
{summary}
                </div>
                <div class="footer">
                    This is an automated summary generated by Content Aggregator
                </div>
            </div>
        </body>
        </html>
        """

        return html


def test_email_sender():
    """Test function"""
    sender = EmailSender()

    test_summary = """
## 주요 트렌드
AI, Python, Web Development

## 핵심 뉴스/글
1. **New AI Model Released** - OpenAI announces GPT-5
   https://example.com/news/1

2. **Python 3.13 Beta** - New features and improvements
   https://example.com/news/2

## 기술/개발
- React 19 released with new features
- TypeScript 5.0 performance improvements

## 흥미로운 토론/의견
- Discussion about the future of web frameworks
- Debate on AI safety measures
    """

    success = sender.send_summary(test_summary, num_items=10)

    if success:
        print("Test email sent successfully!")
    else:
        print("Failed to send test email. Check your credentials.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_email_sender()
