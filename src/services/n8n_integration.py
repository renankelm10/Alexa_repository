import requests
import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class N8NIntegration:
    """
    Classe para gerenciar a integração com n8n via webhooks
    """
    
    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL", "https://n8n-n8n.dwu3jc.easypanel.host/webhook/ec4f9b55-a8da-46ac-b8d5-5df3a4cc6847")
        self.timeout = 10  # timeout em segundos
        
    def process_alexa_request_with_n8n(self, alexa_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envia a requisição completa da Alexa para o n8n e retorna a resposta do n8n.
        
        Args:
            alexa_request: Requisição original da Alexa.
            
        Returns:
            Resposta do n8n (espera-se um JSON no formato de resposta da Alexa) ou None em caso de erro.
        """
        try:
            # O payload para o n8n será a própria requisição da Alexa
            payload = alexa_request
            logger.info(f"[N8N Integration] Enviando requisição para n8n: {json.dumps(payload, indent=2)}")
            
            # Enviar para n8n
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
               headers={'Content-Type': 'application/json'}

            )
            
            response.raise_for_status()
            
            logger.info(f"[N8N Integration] Resposta do n8n recebida. Status: {response.status_code}")
            
            # Retornar a resposta JSON do n8n diretamente
            if response.content:
                n8n_response_json = response.json()
                logger.info(f"[N8N Integration] Conteúdo da resposta do n8n: {json.dumps(n8n_response_json, indent=2)}")
                return n8n_response_json
            
            logger.warning("[N8N Integration] N8N retornou uma resposta vazia para a requisição Alexa.")
            return None
            
        except requests.exceptions.Timeout:
            logger.error("[N8N Integration] Timeout ao enviar requisição Alexa para n8n.")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[N8N Integration] Erro ao enviar requisição Alexa para n8n: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"[N8N Integration] Erro inesperado ao processar requisição Alexa com n8n: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """
        Verifica se o n8n está respondendo
        
        Returns:
            True se o n8n estiver acessível, False caso contrário
        """
        try:
            # Enviar um ping simples
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alexa-skill",
                "action": "health_check"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}

            )
            
            return response.status_code == 200
            
        except Exception:
            return False

# Instância global para uso em toda a aplicação
n8n_integration = N8NIntegration()