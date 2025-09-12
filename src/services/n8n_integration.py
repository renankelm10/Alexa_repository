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
            # O texto do usuário está em request -> intent -> slots -> userText -> value
            user_input = alexa_request.get("request", {}).get("intent", {}).get("slots", {}).get("userText", {}).get("value")
            return user_input
        except Exception:
            return None

    def get_response_from_n8n(self, alexa_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prepara os dados da Alexa, envia para o n8n e retorna a resposta processada.

        Args:
            alexa_request: A requisição original completa da Alexa.

        Returns:
            A resposta do n8n ou None em caso de erro.
        """
        user_input = self._get_user_input_from_request(alexa_request)
        if not user_input:
            logger.warning("[N8N Integration] Não foi possível extrair a fala do usuário da requisição.")
            # Se não houver input (ex: em um LaunchRequest), podemos enviar um evento diferente
            # ou simplesmente não fazer nada, dependendo da lógica desejada.
            # Por enquanto, retornaremos None para que o backend decida o que fazer.
            return None

        # Monta o payload simplificado para o n8n, como o workflow espera
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
        """
        Verifica se o n8n está respondendo
        """
        try:
            payload = { "action": "health_check" }
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

# Instância global para uso em toda a aplicação
n8n_integration = N8NIntegration()