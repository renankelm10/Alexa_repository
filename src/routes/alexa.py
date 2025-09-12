from flask import Blueprint, request, jsonify
import json
import logging
from src.services.n8n_integration import n8n_integration

alexa_bp = Blueprint("alexa", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_alexa_response(text, should_end_session=False):
    """Função auxiliar para criar uma resposta padrão da Alexa."""
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text
            },
            "shouldEndSession": should_end_session
        }
    }

@alexa_bp.route("/alexa", methods=["POST"])
def alexa_skill():
    """
    Endpoint principal que recebe requisições da Alexa.
    """
    try:
        alexa_request = request.get_json()
        logger.info(f"[Alexa Skill] Requisição recebida: {json.dumps(alexa_request, indent=2)}")

        request_type = alexa_request.get("request", {}).get("type")

        # Lógica para diferentes tipos de requisição
        if request_type == "LaunchRequest":
            # Quando o usuário apenas abre a skill: "Alexa, abrir assistente conversacional"
            logger.info("[Alexa Skill] É um LaunchRequest. Enviando saudação.")
            response = create_alexa_response("Olá! Bem-vindo ao assistente conversacional. O que você gostaria de saber?")
            return jsonify(response)

        elif request_type == "IntentRequest":
            # Quando o usuário faz um pedido: "Alexa, qual a capital do Brasil?"
            logger.info("[Alexa Skill] É um IntentRequest. Processando com n8n.")
            
            n8n_response_data = n8n_integration.get_response_from_n8n(alexa_request)

            if n8n_response_data and "response_text" in n8n_response_data:
                # O n8n deve retornar um JSON com a chave "response_text"
                response_text = n8n_response_data["response_text"]
                response = create_alexa_response(response_text)
                logger.info(f"[Alexa Skill] Enviando resposta do n8n para Alexa: {json.dumps(response, indent=2)}")
                return jsonify(response)
            else:
                logger.error("[Alexa Skill] N8N não retornou uma resposta válida. Usando fallback.")
                response = create_alexa_response("Desculpe, não consegui processar sua solicitação agora. Tente novamente.")
                return jsonify(response)
        
        elif request_type == "SessionEndedRequest":
            # Quando a sessão termina
            logger.info("[Alexa Skill] Sessão encerrada.")
            return jsonify({})

        else:
            logger.warning(f"[Alexa Skill] Tipo de requisição não suportado: {request_type}")
            response = create_alexa_response("Não entendi o que você disse.")
            return jsonify(response)

    except Exception as e:
        logger.error(f"[Alexa Skill] Erro fatal no processamento: {str(e)}")
        response = create_alexa_response("Ocorreu um erro inesperado. Por favor, tente mais tarde.")
        return jsonify(response)

# (O restante do arquivo /health, /n8n-status, etc., pode permanecer o mesmo)
@alexa_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "alexa-skill"})

@alexa_bp.route("/n8n-status", methods=["GET"])
def n8n_status():
    is_healthy = n8n_integration.health_check()
    return jsonify({"n8n_integration": "healthy" if is_healthy else "unhealthy"})