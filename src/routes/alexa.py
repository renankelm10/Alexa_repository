from flask import Blueprint, request, jsonify
import json
import logging
from src.services.n8n_integration import n8n_integration

alexa_bp = Blueprint("alexa", __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@alexa_bp.route("/alexa", methods=["POST"])
def alexa_skill():
    """
    Endpoint principal para receber requisições da Alexa e encaminhar para o n8n.
    """
    try:
        alexa_request = request.get_json()
        logger.info(f"[Alexa Skill] Requisição Alexa recebida: {json.dumps(alexa_request, indent=2)}")

        # Envia a requisição completa da Alexa para o n8n e espera a resposta
        # O n8n deve retornar um JSON no formato de resposta da Alexa
        n8n_alexa_response = n8n_integration.process_alexa_request_with_n8n(alexa_request)

        if n8n_alexa_response:
            logger.info(f"[Alexa Skill] Resposta formatada do n8n recebida: {json.dumps(n8n_alexa_response, indent=2)}")
            logger.info(f"[Alexa Skill] Enviando resposta para Alexa: {json.dumps(n8n_alexa_response, indent=2)}")
            return jsonify(n8n_alexa_response)
        else:
            logger.error("[Alexa Skill] N8N não retornou uma resposta válida ou ocorreu um erro no processamento. Retornando fallback.")
            # Fallback para uma resposta de erro padrão da Alexa
            error_response = {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Desculpe, não consegui processar sua solicitação no momento. Tente novamente mais tarde."
                    },
                    "shouldEndSession": True
                }
            }
            logger.info(f"[Alexa Skill] Enviando resposta de fallback para Alexa: {json.dumps(error_response, indent=2)}")
            return jsonify(error_response)

    except Exception as e:
        logger.error(f"[Alexa Skill] Erro no processamento da skill Alexa: {str(e)}")
        error_response = {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Desculpe, ocorreu um erro inesperado. Tente novamente."
                },
                "shouldEndSession": True
            }
        }
        logger.info(f"[Alexa Skill] Enviando resposta de erro inesperado para Alexa: {json.dumps(error_response, indent=2)}")
        return jsonify(error_response)

@alexa_bp.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint para verificar se o serviço está funcionando
    """
    return jsonify({"status": "healthy", "service": "alexa-skill"})


@alexa_bp.route("/n8n-status", methods=["GET"])
def n8n_status():
    """
    Endpoint para verificar se a integração com n8n está funcionando
    """
    is_healthy = n8n_integration.health_check()
    
    return jsonify({
        "n8n_integration": "healthy" if is_healthy else "unhealthy",
        "webhook_url": n8n_integration.webhook_url,
        "timestamp": n8n_integration._prepare_payload({}, {})["timestamp"]
    })

@alexa_bp.route("/send-test-event", methods=["POST"])
def send_test_event():
    """
    Endpoint para enviar um evento de teste para o n8n
    """
    try:
        test_data = request.get_json() or {"message": "Evento de teste da skill da Alexa"}
        
        result = n8n_integration.send_custom_event("test_event", test_data)
        
        if result:
            return jsonify({"status": "success", "result": result})
        else:
            return jsonify({"status": "error", "message": "Falha ao enviar evento de teste"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500