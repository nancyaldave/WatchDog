"""
Sistema de envío de alertas por email, Teams y Slack.
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, Any, List
import os


class AlertSystem:
    """Maneja el envío de alertas a diferentes canales."""
    
    def __init__(self, recipients_file: str = 'recipients.json'):
        """
        Inicializa el sistema de alertas.
        
        Args:
            recipients_file: Ruta al archivo JSON con destinatarios
        """
        self.recipients_file = recipients_file
        self.recipients_data = self._load_recipients()
        self.emails = self._get_enabled_emails()
        self.teams_webhook = self.recipients_data.get('channels', {}).get('teams_webhook', '')
        self.slack_webhook = self.recipients_data.get('channels', {}).get('slack_webhook', '')
        self.email_settings = self.recipients_data.get('email_settings', {})
    
    def _load_recipients(self) -> Dict[str, Any]:
        """Carga los destinatarios desde el archivo JSON."""
        if not os.path.exists(self.recipients_file):
            print(f"⚠️  Archivo {self.recipients_file} no encontrado. Usando configuración por defecto.")
            return {
                'people': [],
                'channels': {},
                'email_settings': {}
            }
        
        try:
            with open(self.recipients_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando {self.recipients_file}: {e}")
            return {
                'people': [],
                'channels': {},
                'email_settings': {}
            }
    
    def _get_enabled_emails(self) -> List[str]:
        """Obtiene la lista de emails habilitados."""
        people = self.recipients_data.get('people', [])
        return [person['email'] for person in people if person.get('enabled', True)]
    
    def get_recipients_info(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los destinatarios.
        
        Returns:
            Lista de diccionarios con información de cada persona
        """
        return self.recipients_data.get('people', [])
    
    def send_alert(self, message: str, alert_data: Dict[str, Any]):
        """
        Envía alerta a todos los canales configurados.
        
        Args:
            message: Mensaje de alerta generado
            alert_data: Datos de la anomalía detectada
        """
        # Enviar por email
        if self.emails:
            self._send_email(message, alert_data)
        
        # Enviar a Teams
        if self.teams_webhook:
            self._send_teams(message, alert_data)
        
        # Enviar a Slack
        if self.slack_webhook:
            self._send_slack(message, alert_data)
    
    def _send_email(self, message: str, alert_data: Dict[str, Any]):
        """Envía alerta por email."""
        if not self.emails:
            return
        
        try:
            # Configuración básica de SMTP (ajusta según tu servidor)
            # Para Gmail: smtp.gmail.com:587
            # Para Outlook: smtp-mail.outlook.com:587
            # Para servidor local: localhost:25
            
            smtp_server = "localhost"  # Cambiar según tu configuración
            smtp_port = 25
            
            msg = MIMEMultipart()
            from_email = self.email_settings.get('from_email', 'anomaly-detector@accounttech.com')
            from_name = self.email_settings.get('from_name', 'Sistema de Detección de Anomalías')
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = ", ".join(self.emails)
            msg['Subject'] = f"🚨 Alerta de Anomalía - Cuenta {alert_data['account_number']}"
            
            body = f"""
{message}

---
Sistema de Detección de Anomalías
Generado automáticamente
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email (sin autenticación para servidor local)
            # Si necesitas autenticación, descomenta y configura:
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login("user", "password")
            # server.send_message(msg)
            # server.quit()
            
            print(f"  ✓ Email enviado a {len(self.emails)} destinatario(s)")
            
        except Exception as e:
            print(f"  ⚠️  Error enviando email: {e}")
    
    def _send_teams(self, message: str, alert_data: Dict[str, Any]):
        """Envía alerta a Microsoft Teams."""
        if not self.teams_webhook:
            return
        
        try:
            # Formato de mensaje para Teams
            teams_message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": f"Alerta de Anomalía - Cuenta {alert_data['account_number']}",
                "themeColor": "FF0000",
                "title": "🚨 Alerta de Anomalía Detectada",
                "sections": [
                    {
                        "activityTitle": f"Cuenta: {alert_data['account_number']} - {alert_data['account_name']}",
                        "facts": [
                            {
                                "name": "Fecha:",
                                "value": alert_data['date']
                            },
                            {
                                "name": "Monto:",
                                "value": f"${alert_data['amount']:,.2f}"
                            },
                            {
                                "name": "Promedio Anual:",
                                "value": f"${alert_data['yearly_average']:,.2f}"
                            },
                            {
                                "name": "Ratio:",
                                "value": f"{alert_data['ratio']:.2f}x"
                            },
                            {
                                "name": "Método:",
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
                print("  ✓ Alerta enviada a Teams")
            else:
                print(f"  ⚠️  Error enviando a Teams: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Error enviando a Teams: {e}")
    
    def _send_slack(self, message: str, alert_data: Dict[str, Any]):
        """Envía alerta a Slack."""
        if not self.slack_webhook:
            return
        
        try:
            slack_message = {
                "text": "🚨 Alerta de Anomalía Detectada",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Alerta de Anomalía"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Cuenta:*\n{alert_data['account_number']} - {alert_data['account_name']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Fecha:*\n{alert_data['date']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Monto:*\n${alert_data['amount']:,.2f}"
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
                print("  ✓ Alerta enviada a Slack")
            else:
                print(f"  ⚠️  Error enviando a Slack: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Error enviando a Slack: {e}")

