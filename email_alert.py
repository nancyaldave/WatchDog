"""
Email Alert System for Darwin Company
Sends detailed email alerts about detected anomalies.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import io


class EmailAlertSystem:
    """Handles email alerts for detected anomalies."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email alert system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.email_config = config['email']
        self.company_name = config['company']['name']
        self.enabled = self.email_config.get('enabled', True)
        
    def create_email_body(self, anomalies: pd.DataFrame, threshold: float) -> str:
        """
        Create detailed email body with anomaly information.
        
        Args:
            anomalies: DataFrame with detected anomalies
            threshold: Percentage threshold used for detection
            
        Returns:
            HTML formatted email body
        """
        total_anomalies = len(anomalies)
        total_amount = anomalies['amount'].sum()
        avg_deviation = anomalies['pct_diff_from_avg'].mean()
        
        # Group by account for summary
        account_summary = anomalies.groupby(['accountNumber', 'account']).agg({
            'amount': ['count', 'sum', 'mean'],
            'pct_diff_from_avg': 'mean'
        }).round(2)
        
        # Create HTML email
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .summary-item {{ margin: 10px 0; }}
                .summary-label {{ font-weight: bold; color: #856404; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th {{ background-color: #1976d2; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .footer {{ background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .alert-icon {{ font-size: 24px; }}
                .number {{ font-weight: bold; color: #d32f2f; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1><span class="alert-icon">🚨</span> {self.company_name} - Anomaly Detection Alert</h1>
                <p>Automated Anomaly Detection System</p>
            </div>
            
            <div class="content">
                <h2>Anomaly Detection Report</h2>
                <p>Dear Finance Team,</p>
                <p>The {self.company_name} anomaly detection system has identified <span class="number">{total_anomalies}</span> 
                transactions that exceed the configured threshold of <span class="number">{threshold}%</span> deviation from their account averages.</p>
                
                <div class="summary">
                    <h3>📊 Summary Statistics</h3>
                    <div class="summary-item">
                        <span class="summary-label">Total Anomalies Detected:</span> {total_anomalies}
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Total Amount Involved:</span> ${total_amount:,.2f}
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Average Deviation:</span> {avg_deviation:.2f}%
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Detection Date:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">Threshold Used:</span> {threshold}%
                    </div>
                </div>
                
                <h3>📋 Detailed Anomaly List</h3>
                <p>Below are the transactions that triggered the anomaly detection:</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Account Number</th>
                            <th>Account Name</th>
                            <th>Date</th>
                            <th>Amount</th>
                            <th>Account Average</th>
                            <th>% Deviation</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add rows for each anomaly (limit to top 50 for email readability)
        display_limit = min(50, len(anomalies))
        for idx, row in anomalies.head(display_limit).iterrows():
            html += f"""
                        <tr>
                            <td>{row['accountNumber']}</td>
                            <td>{row['account']}</td>
                            <td>{row['dtmDate'].strftime('%Y-%m-%d')}</td>
                            <td>${row['amount']:,.2f}</td>
                            <td>${row['avg_amount']:,.2f}</td>
                            <td style="color: #d32f2f; font-weight: bold;">{row['pct_diff_from_avg']:.2f}%</td>
                        </tr>
            """
        
        if len(anomalies) > display_limit:
            html += f"""
                        <tr>
                            <td colspan="6" style="text-align: center; font-style: italic; color: #666;">
                                ... and {len(anomalies) - display_limit} more anomalies (see attached CSV for complete list)
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
                
                <h3>⚠️ Recommended Actions</h3>
                <ul>
                    <li>Review each flagged transaction for accuracy and legitimacy</li>
                    <li>Verify that the transactions are properly authorized</li>
                    <li>Investigate any patterns or recurring anomalies</li>
                    <li>Contact the relevant department heads for clarification if needed</li>
                    <li>Update documentation if these represent legitimate business changes</li>
                </ul>
                
                <p><strong>Note:</strong> All detected anomalies have been automatically saved to the database for record-keeping and further analysis.</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from the {self.company_name} Anomaly Detection System.</p>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_csv_attachment(self, anomalies: pd.DataFrame) -> bytes:
        """
        Create CSV attachment with all anomaly details.
        
        Args:
            anomalies: DataFrame with detected anomalies
            
        Returns:
            CSV data as bytes
        """
        # Select columns for CSV export
        export_columns = [
            'accountID', 'accountNumber', 'account', 'dtmDate', 'amount',
            'avg_amount', 'pct_diff_from_avg', 'threshold_used', 'detection_date'
        ]
        
        csv_buffer = io.StringIO()
        anomalies[export_columns].to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    
    def send_alert(self, anomalies: pd.DataFrame, threshold: float) -> bool:
        """
        Send email alert with anomaly details.
        
        Args:
            anomalies: DataFrame with detected anomalies
            threshold: Percentage threshold used
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            print("📧 Email alerts are disabled in configuration")
            return False
        
        if len(anomalies) == 0:
            print("📧 No anomalies to report via email")
            return False
        
        recipients = self.email_config.get('recipients', [])
        if not recipients:
            print("⚠️  No email recipients configured")
            return False
        
        try:
            print(f"\n📧 Preparing email alert for {len(recipients)} recipient(s)...")
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['from_name']} <{self.email_config['from_email']}>"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"🚨 {self.company_name} - {len(anomalies)} Anomalies Detected - Action Required"
            
            # Create email body
            html_body = self.create_email_body(anomalies, threshold)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach CSV file
            csv_data = self.create_csv_attachment(anomalies)
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(csv_data)
            encoders.encode_base64(attachment)
            filename = f"anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(attachment)
            
            # Send email
            self._send_smtp(msg, recipients)
            
            print(f"✓ Email alert sent successfully to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email alert: {e}")
            return False
    
    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP."""
        smtp_server = self.email_config['smtp_server']
        smtp_port = self.email_config['smtp_port']
        use_tls = self.email_config.get('use_tls', False)
        use_auth = self.email_config.get('use_authentication', False)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        try:
            if use_tls:
                server.starttls()
            
            if use_auth:
                username = self.email_config.get('smtp_username', '')
                password = self.email_config.get('smtp_password', '')
                if username and password:
                    server.login(username, password)
            
            server.send_message(msg)
            
        finally:
            server.quit()

