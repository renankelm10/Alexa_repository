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

    def _get_user_input_from_request(self, alexa_request: Dict[str, Any]) -> Optional[str]:
        """
        Extrai o texto falado pelo usuário de dentro da requisição da Alexa.
        """
        try:
            intent = alexa_request.get("request", {}).get("intent", {})
            # Verifica se o objeto 'slots' existe antes de tentar acessá-lo
            if "slots" in intent and intent["slots"] is not None:
                user_input = intent.get("slots", {}).get("userText", {}).get("value")
                return user_input
            return None # Retorna None se não houver slots
        except Exception:
            return None

    def get_response_from_n8n(self, alexa_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prepara os dados da Alexa, envia para o n8n e retorna a resposta processada.
        """
        user_input = self._get_user_input_from_request(alexa_request)
        if not user_input:
            logger.warning("[N8N Integration] A requisição não continha texto do usuário no slot 'userText'.")
            return None

        # Monta o payload simplificado para o n8n
        payload = {
            "action": "get_response",
            "user_input": user_input,
            "context": {
                "session_id": alexa_request.get("session", {}).get("sessionId"),
                "user_id": alexa_request.get("session", {}).get("user", {}).get("userId"),
                "locale": alexa_request.get("request", {}).get("locale")
            }
        }

        try:
            logger.info(f"[N8N Integration] Enviando payload para n8n: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )

            response.raise_for_status()
            logger.info(f"[N8N Integration] Resposta do n8n recebida. Status: {response.status_code}")

            if response.content:
                n8n_response_json = response.json()
                logger.info(f"[N8N Integration] Conteúdo da resposta do n8n: {json.dumps(n8n_response_json, indent=2)}")
                return n8n_response_json

            logger.warning("[N8N Integration] N8N retornou uma resposta vazia.")
            return None

        except requests.exceptions.Timeout:
            logger.error("[N8N Integration] Timeout ao enviar requisição para n8n.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[N8N Integration] Erro ao enviar requisição para n8n: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[N8N Integration] Erro inesperado ao processar com n8n: {str(e)}")
            return None

    def health_check(self) -> bool:
        try:
            payload = { "action": "health_check" }
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

n8n_integration = N8NIntegration()