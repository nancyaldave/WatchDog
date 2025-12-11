"""
Alert message generator using local LLM (Ollama).
"""

import json
import requests
from typing import Dict, Any, Optional


class LLMAlertGenerator:
    """Generates alert messages using a local LLM."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the LLM message generator.
        
        Args:
            llm_config: LLM configuration from config.json
        """
        self.model = llm_config.get('model', 'llama3')
        self.base_url = llm_config.get('base_url', 'http://localhost:11434')
        self.enabled = llm_config.get('enabled', True)
    
    def generate_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Generate an alert message using the local LLM.
        
        Args:
            alert_data: Detected anomaly data
            
        Returns:
            Generated alert message
        """
        if not self.enabled:
            return self._generate_fallback_message(alert_data)
        
        try:
            prompt = self._create_prompt(alert_data)
            message = self._call_llm(prompt)
            return message
        except Exception as e:
            print(f"  ⚠️  Error calling LLM: {e}")
            return self._generate_fallback_message(alert_data)
    
    def _create_prompt(self, alert_data: Dict[str, Any]) -> str:
<<<<<<< HEAD
        """Crea el prompt para el LLM."""
        return f"""Eres un asistente financiero experto. Genera un mensaje profesional de alerta en español para notificar sobre una anomalía detectada en una cuenta contable mediante machine learning (Isolation Forest).

Datos de la anomalía:
- Número de cuenta: {alert_data['account_number']}
- Nombre de cuenta: {alert_data['account_name']}
- Fecha: {alert_data['date']}
- Monto detectado: ${alert_data['amount']:,.2f}
- Promedio anual: ${alert_data['yearly_average']:,.2f}
- Ratio vs promedio: {alert_data['ratio']:.2f}x
- Método de detección: {alert_data['detection_method']}
- Score de anomalía: {alert_data['isolation_score']:.4f}

Genera un mensaje conciso (máximo 150 palabras) que:
1. Explique claramente la anomalía detectada por el modelo de machine learning
2. Proporcione contexto sobre por qué es significativa según el algoritmo
3. Sugiera acciones recomendadas
4. Sea profesional pero urgente
=======
        """Create the prompt for the LLM."""
        return f"""You are an expert financial assistant. Generate a professional alert message in Spanish to notify about an anomaly detected in an accounting account.

Anomaly data:
- Account number: {alert_data['account_number']}
- Account name: {alert_data['account_name']}
- Date: {alert_data['date']}
- Detected amount: ${alert_data['amount']:,.2f}
- Yearly average: ${alert_data['yearly_average']:,.2f}
- Ratio vs average: {alert_data['ratio']:.2f}x
- Detection method: {alert_data['detection_method']}

Generate a concise message (maximum 150 words) that:
1. Clearly explains the detected anomaly
2. Provides context on why it is significant
3. Suggests recommended actions
4. Is professional but urgent
>>>>>>> b766129897ae58f35583cf00e50dc151d956090a

Message:"""
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the local LLM using Ollama API.
        
        Args:
            prompt: Prompt for the LLM
            
        Returns:
            LLM response
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 300
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _generate_fallback_message(self, alert_data: Dict[str, Any]) -> str:
        """Generate fallback message without LLM."""
        return (
<<<<<<< HEAD
            f"🚨 ALERTA DE ANOMALÍA DETECTADA\n\n"
            f"Se ha detectado una anomalía significativa en la cuenta contable mediante Isolation Forest:\n\n"
            f"• Cuenta: {alert_data['account_number']} - {alert_data['account_name']}\n"
            f"• Fecha: {alert_data['date']}\n"
            f"• Monto detectado: ${alert_data['amount']:,.2f}\n"
            f"• Promedio anual: ${alert_data['yearly_average']:,.2f}\n"
            f"• Ratio: {alert_data['ratio']:.2f}x el promedio anual\n"
            f"• Método de detección: {alert_data['detection_method']}\n"
            f"• Score de anomalía: {alert_data['isolation_score']:.4f}\n\n"
            f"El modelo de machine learning (Isolation Forest) ha identificado este registro como una anomalía. "
            f"Se recomienda una revisión inmediata para verificar la validez de la transacción "
            f"y determinar si requiere acción correctiva.\n\n"
            f"Por favor, investigue esta anomalía lo antes posible."
=======
            f"🚨 ANOMALY ALERT DETECTED\n\n"
            f"A significant anomaly has been detected in the accounting account:\n\n"
            f"• Account: {alert_data['account_number']} - {alert_data['account_name']}\n"
            f"• Date: {alert_data['date']}\n"
            f"• Detected amount: ${alert_data['amount']:,.2f}\n"
            f"• Yearly average: ${alert_data['yearly_average']:,.2f}\n"
            f"• Ratio: {alert_data['ratio']:.2f}x the yearly average\n"
            f"• Detection method: {alert_data['detection_method']}\n\n"
            f"This amount significantly exceeds the historical yearly average. "
            f"An immediate review is recommended to verify the validity of the transaction "
            f"and determine if corrective action is required.\n\n"
            f"Please investigate this anomaly as soon as possible."
>>>>>>> b766129897ae58f35583cf00e50dc151d956090a
        )

