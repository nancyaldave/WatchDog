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
        )

