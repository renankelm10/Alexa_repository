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
        # URL do webhook do n8n (pode ser configurada via variável de ambiente)
        self.webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://n8n-n8n.dwu3jc.easypanel.host/webhook-test/ec4f9b55-a8da-46ac-b8d5-5df3a4cc6847')
        self.timeout = 10  # timeout em segundos
        
    def send_alexa_data(self, alexa_request: Dict[str, Any], alexa_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envia dados da Alexa para o n8n
        
        Args:
            alexa_request: Requisição original da Alexa
            alexa_response: Resposta que será enviada para a Alexa
            
        Returns:
            Resposta do n8n ou None em caso de erro
        """
        try:
            # Preparar payload com dados estruturados
            payload = self._prepare_payload(alexa_request, alexa_response)
            
            # Enviar para n8n
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            logger.info(f"Dados enviados para n8n com sucesso. Status: {response.status_code}")
            
            # Retornar resposta do n8n se houver
            if response.content:
                return response.json()
            
            return {"status": "success"}
            
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar dados para n8n")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar dados para n8n: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Erro inesperado na integração com n8n: {str(e)}")
            return None
    
    def _prepare_payload(self, alexa_request: Dict[str, Any], alexa_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o payload para envio ao n8n
        """
        # Extrair informações importantes da requisição
        request_info = self._extract_request_info(alexa_request)
        session_info = self._extract_session_info(alexa_request)
        user_info = self._extract_user_info(alexa_request)
        
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "alexa-skill",
            "request_info": request_info,
            "session_info": session_info,
            "user_info": user_info,
            "alexa_request": alexa_request,
            "alexa_response": alexa_response,
            "metadata": {
                "skill_version": "1.0.0",
                "integration_version": "1.0.0"
            }
        }
        
        return payload
    
    def _extract_request_info(self, alexa_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações da requisição
        """
        request_data = alexa_request.get('request', {})
        
        return {
            "type": request_data.get('type'),
            "request_id": request_data.get('requestId'),
            "timestamp": request_data.get('timestamp'),
            "locale": request_data.get('locale'),
            "intent_name": request_data.get('intent', {}).get('name'),
            "slots": request_data.get('intent', {}).get('slots', {}),
            "confirmation_status": request_data.get('intent', {}).get('confirmationStatus')
        }
    
    def _extract_session_info(self, alexa_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações da sessão
        """
        session_data = alexa_request.get('session', {})
        
        return {
            "session_id": session_data.get('sessionId'),
            "new_session": session_data.get('new'),
            "attributes": session_data.get('attributes', {}),
            "application_id": session_data.get('application', {}).get('applicationId')
        }
    
    def _extract_user_info(self, alexa_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações do usuário (sem dados pessoais sensíveis)
        """
        user_data = alexa_request.get('session', {}).get('user', {})
        
        return {
            "user_id": user_data.get('userId'),
            "access_token": user_data.get('accessToken') is not None  # Apenas indica se existe
        }
    
    def send_custom_event(self, event_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Envia um evento customizado para o n8n
        
        Args:
            event_type: Tipo do evento (ex: 'user_feedback', 'error', 'analytics')
            data: Dados do evento
            
        Returns:
            Resposta do n8n ou None em caso de erro
        """
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alexa-skill",
                "event_type": event_type,
                "data": data,
                "metadata": {
                    "skill_version": "1.0.0",
                    "integration_version": "1.0.0"
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            logger.info(f"Evento customizado '{event_type}' enviado para n8n com sucesso")
            
            if response.content:
                return response.json()
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Erro ao enviar evento customizado para n8n: {str(e)}")
            return None
    
    def get_response_from_n8n(self, user_input: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Solicita uma resposta processada pelo n8n
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            
        Returns:
            Resposta processada ou None em caso de erro
        """
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alexa-skill",
                "action": "get_response",
                "user_input": user_input,
                "context": context,
                "metadata": {
                    "skill_version": "1.0.0",
                    "integration_version": "1.0.0"
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Assumindo que o n8n retorna a resposta em um campo específico
            if 'response_text' in result:
                return result['response_text']
            elif 'message' in result:
                return result['message']
            
            logger.warning("N8N não retornou uma resposta válida")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter resposta do n8n: {str(e)}")
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

