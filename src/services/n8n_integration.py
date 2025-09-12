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
        self.timeout = 30  # Aumentado para 30 segundos para dar tempo ao n8n processar
        
    def extract_user_input(self, alexa_request: Dict[str, Any]) -> str:
        """
        Extrai o que o usuário falou da requisição da Alexa
        
        Args:
            alexa_request: Requisição original da Alexa
            
        Returns:
            String com o que o usuário disse
        """
        try:
            request_type = alexa_request.get("request", {}).get("type", "")
            
            # Para LaunchRequest (quando o usuário apenas abre a skill)
            if request_type == "LaunchRequest":
                return "Iniciar conversa"
            
            # Para IntentRequest (mais comum)
            elif request_type == "IntentRequest":
                intent = alexa_request.get("request", {}).get("intent", {})
                intent_name = intent.get("name", "")
                
                # Se for um intent de captura de texto genérico
                # (você precisa configurar isso na sua skill da Alexa)
                if intent_name in ["CaptureTextIntent", "AMAZON.FallbackIntent", "CatchAllIntent"]:
                    # Tenta pegar o valor do slot de texto
                    slots = intent.get("slots", {})
                    
                    # Procura por um slot que contenha o texto falado
                    for slot_name, slot_data in slots.items():
                        if slot_data and "value" in slot_data:
                            return slot_data["value"]
                    
                    # Se não encontrou em slots, tenta pegar de outras formas
                    if "value" in intent:
                        return intent["value"]
                
                # Para intents específicos
                else:
                    # Monta uma string com o intent e os valores dos slots
                    user_text = f"Intent: {intent_name}"
                    slots = intent.get("slots", {})
                    slot_values = []
                    for slot_name, slot_data in slots.items():
                        if slot_data and "value" in slot_data:
                            slot_values.append(slot_data["value"])
                    
                    if slot_values:
                        user_text = " ".join(slot_values)
                    
                    return user_text
            
            # Para SessionEndedRequest
            elif request_type == "SessionEndedRequest":
                return "Encerrar conversa"
            
            # Fallback
            return "Mensagem não identificada"
            
        except Exception as e:
            logger.error(f"Erro ao extrair input do usuário: {str(e)}")
            return "Erro ao processar mensagem"
    
    def process_alexa_request_with_n8n(self, alexa_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envia a requisição da Alexa para o n8n e retorna a resposta formatada.
        
        Args:
            alexa_request: Requisição original da Alexa.
            
        Returns:
            Resposta formatada para a Alexa ou None em caso de erro.
        """
        try:
            # Extrai o que o usuário falou
            user_input = self.extract_user_input(alexa_request)
            logger.info(f"[N8N Integration] Texto extraído do usuário: {user_input}")
            
            # Extrai informações da sessão
            session_id = alexa_request.get("session", {}).get("sessionId", "")
            user_id = alexa_request.get("session", {}).get("user", {}).get("userId", "")
            
            # Prepara o payload para o n8n com informações úteis
            payload = {
                "userInput": user_input,  # O que o usuário falou
                "sessionId": session_id,   # ID da sessão para manter contexto
                "userId": user_id,         # ID do usuário
                "locale": alexa_request.get("request", {}).get("locale", "pt-BR"),
                "timestamp": datetime.utcnow().isoformat(),
                "requestType": alexa_request.get("request", {}).get("type", ""),
                "fullRequest": alexa_request  # Envia também a requisição completa caso necessário
            }
            
            logger.info(f"[N8N Integration] Enviando payload para n8n: {json.dumps(payload, indent=2)}")
            
            # Envia para n8n
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            logger.info(f"[N8N Integration] Resposta do n8n recebida. Status: {response.status_code}")
            
            if response.content:
                n8n_response = response.json()
                logger.info(f"[N8N Integration] Resposta do n8n: {json.dumps(n8n_response, indent=2)}")
                
                # Verifica se o n8n retornou uma resposta no formato correto da Alexa
                if "version" in n8n_response and "response" in n8n_response:
                    # n8n retornou no formato correto da Alexa
                    return n8n_response
                else:
                    # n8n retornou apenas o texto ou outro formato
                    # Vamos formatar para a Alexa
                    return self.format_alexa_response(n8n_response)
            
            logger.warning("[N8N Integration] N8N retornou uma resposta vazia.")
            return None
            
        except requests.exceptions.Timeout:
            logger.error("[N8N Integration] Timeout ao enviar requisição para n8n.")
            return self.create_error_response("Desculpe, o processamento demorou muito. Por favor, tente novamente.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[N8N Integration] Erro ao enviar requisição para n8n: {str(e)}")
            return self.create_error_response("Desculpe, ocorreu um erro de conexão. Por favor, tente novamente.")
            
        except Exception as e:
            logger.error(f"[N8N Integration] Erro inesperado: {str(e)}")
            return self.create_error_response("Desculpe, ocorreu um erro inesperado.")
    
    def format_alexa_response(self, n8n_response: Any) -> Dict[str, Any]:
        """
        Formata a resposta do n8n para o formato esperado pela Alexa
        
        Args:
            n8n_response: Resposta do n8n (pode ser string, dict, etc)
            
        Returns:
            Resposta formatada para a Alexa
        """
        # Se for uma string simples
        if isinstance(n8n_response, str):
            text = n8n_response
        # Se for um dict com uma chave 'text' ou 'message'
        elif isinstance(n8n_response, dict):
            text = n8n_response.get("text", n8n_response.get("message", str(n8n_response)))
        else:
            text = str(n8n_response)
        
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": text
                },
                "shouldEndSession": False,  # Mantém a sessão aberta para continuar a conversa
                "reprompt": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Você ainda está aí? Como posso ajudar?"
                    }
                }
            }
        }
    
    def create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Cria uma resposta de erro formatada para a Alexa
        
        Args:
            error_message: Mensagem de erro para o usuário
            
        Returns:
            Resposta de erro formatada
        """
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": error_message
                },
                "shouldEndSession": False
            }
        }
    
    def health_check(self) -> bool:
        """
        Verifica se o n8n está respondendo
        
        Returns:
            True se o n8n estiver acessível, False caso contrário
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Health check falhou: {str(e)}")
            return False
    
    def send_custom_event(self, event_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envia um evento customizado para o n8n
        
        Args:
            event_type: Tipo do evento
            data: Dados do evento
            
        Returns:
            Resposta do n8n ou None em caso de erro
        """
        try:
            payload = {
                "eventType": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alexa-skill"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Erro ao enviar evento customizado: {str(e)}")
            return None
    
    def _prepare_payload(self, alexa_request: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o payload para enviar ao n8n (método auxiliar para compatibilidade)
        """
        return {
            "alexa_request": alexa_request,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }

# Instância global para uso em toda a aplicação
n8n_integration = N8NIntegration()