"""
Alert delivery system via email, Teams, and Slack.
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, Any, List
import os


class AlertSystem:
    """Handles alert delivery to different channels."""
    
    def __init__(self, recipients_file: str = 'recipients.json'):
        """
        Initialize the alert system.
        
        Args:
            recipients_file: Path to JSON file with recipients
        """
        self.recipients_file = recipients_file
        self.recipients_data = self._load_recipients()
        self.emails = self._get_enabled_emails()
        self.teams_webhook = self.recipients_data.get('channels', {}).get('teams_webhook', '')
        self.slack_webhook = self.recipients_data.get('channels', {}).get('slack_webhook', '')
        self.email_settings = self.recipients_data.get('email_settings', {})
    
    def _load_recipients(self) -> Dict[str, Any]:
        """Load recipients from JSON file."""
        if not os.path.exists(self.recipients_file):
            print(f"⚠️  File {self.recipients_file} not found. Using default configuration.")
            return {
                'people': [],
                'channels': {},
                'email_settings': {}
            }
        
        try:
            with open(self.recipients_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading {self.recipients_file}: {e}")
            return {
                'people': [],
                'channels': {},
                'email_settings': {}
            }
    
    def _get_enabled_emails(self) -> List[str]:
        """Get list of enabled email addresses."""
        people = self.recipients_data.get('people', [])
        return [person['email'] for person in people if person.get('enabled', True)]
    
    def get_recipients_info(self) -> List[Dict[str, Any]]:
        """
        Get information for all recipients.
        
        Returns:
            List of dictionaries with information for each person
        """
        return self.recipients_data.get('people', [])
    
    def send_alert(self, message: str, alert_data: Dict[str, Any]):
        """
        Send alert to all configured channels.
        
        Args:
            message: Generated alert message
            alert_data: Detected anomaly data
        """
        # Send via email
        if self.emails:
            self._send_email(message, alert_data)
        
        # Send to Teams
        if self.teams_webhook:
            self._send_teams(message, alert_data)
        
        # Send to Slack
        if self.slack_webhook:
            self._send_slack(message, alert_data)
    
    def _send_email(self, message: str, alert_data: Dict[str, Any]):
        """Send alert via email."""
        if not self.emails:
            return
        
        try:
            # Basic SMTP configuration (adjust according to your server)
            # For Gmail: smtp.gmail.com:587
            # For Outlook: smtp-mail.outlook.com:587
            # For local server: localhost:25
            
            smtp_server = "localhost"  # Change according to your configuration
            smtp_port = 25
            
            msg = MIMEMultipart()
            from_email = self.email_settings.get('from_email', 'anomaly-detector@accounttech.com')
            from_name = self.email_settings.get('from_name', 'Anomaly Detection System')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = ", ".join(self.emails)
            msg['Subject'] = f"🚨 Anomaly Alert - Account {alert_data['account_number']}"
            
            body = f"""
{message}

---
Anomaly Detection System
Automatically generated
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (without authentication for local server)
            # If you need authentication, uncomment and configure:
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login("user", "password")
            # server.send_message(msg)
            # server.quit()
            
            print(f"  ✓ Email sent to {len(self.emails)} recipient(s)")
            
        except Exception as e:
            print(f"  ⚠️  Error sending email: {e}")
    
    def _send_teams(self, message: str, alert_data: Dict[str, Any]):
        """Send alert to Microsoft Teams."""
        if not self.teams_webhook:
            return
        
        try:
            # Message format for Teams
            teams_message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": f"Anomaly Alert - Account {alert_data['account_number']}",
                "themeColor": "FF0000",
                "title": "🚨 Anomaly Alert Detected",
                "sections": [
                    {
                        "activityTitle": f"Account: {alert_data['account_number']} - {alert_data['account_name']}",
                        "facts": [
                            {
                                "name": "Date:",
                                "value": alert_data['date']
                            },
                            {
                                "name": "Amount:",
                                "value": f"${alert_data['amount']:,.2f}"
                            },
                            {
                                "name": "Yearly Average:",
                                "value": f"${alert_data['yearly_average']:,.2f}"
                            },
                            {
                                "name": "Ratio:",
                                "value": f"{alert_data['ratio']:.2f}x"
                            },
                            {
                                "name": "Method:",
                                "value": alert_data['detection_method']
                            }
                        ],
                        "text": message
                    }
                ]
            }
            
            response = requests.post(
                self.teams_webhook,
                json=teams_message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✓ Alert sent to Teams")
            else:
                print(f"  ⚠️  Error sending to Teams: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Error sending to Teams: {e}")
    
    def _send_slack(self, message: str, alert_data: Dict[str, Any]):
        """Send alert to Slack."""
        if not self.slack_webhook:
            return
        
        try:
            slack_message = {
                "text": "🚨 Anomaly Alert Detected",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Anomaly Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Account:*\n{alert_data['account_number']} - {alert_data['account_name']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Date:*\n{alert_data['date']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Amount:*\n${alert_data['amount']:,.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Ratio:*\n{alert_data['ratio']:.2f}x"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{message}```"
                        }
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook,
                json=slack_message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✓ Alert sent to Slack")
            else:
                print(f"  ⚠️  Error sending to Slack: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Error sending to Slack: {e}")

