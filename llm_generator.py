"""
Generador de mensajes de alerta usando LLM local (Ollama).
"""

import json
import requests
from typing import Dict, Any, Optional


class LLMAlertGenerator:
    """Genera mensajes de alerta usando un LLM local."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Inicializa el generador de mensajes LLM.
        
        Args:
            llm_config: Configuración del LLM desde config.json
        """
        self.model = llm_config.get('model', 'llama3')
        self.base_url = llm_config.get('base_url', 'http://localhost:11434')
        self.enabled = llm_config.get('enabled', True)
    
    def generate_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Genera un mensaje de alerta usando el LLM local.
        
        Args:
            alert_data: Datos de la anomalía detectada
            
        Returns:
            Mensaje de alerta generado
        """
        if not self.enabled:
            return self._generate_fallback_message(alert_data)
        
        try:
            prompt = self._create_prompt(alert_data)
            message = self._call_llm(prompt)
            return message
        except Exception as e:
            print(f"  ⚠️  Error llamando LLM: {e}")
            return self._generate_fallback_message(alert_data)
    
    def _create_prompt(self, alert_data: Dict[str, Any]) -> str:
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

Mensaje:"""
    
    def _call_llm(self, prompt: str) -> str:
        """
        Llama al LLM local usando Ollama API.
        
        Args:
            prompt: Prompt para el LLM
            
        Returns:
            Respuesta del LLM
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
        """Genera mensaje de respaldo sin LLM."""
        return (
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
        )

