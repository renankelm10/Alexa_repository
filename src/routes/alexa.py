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

        # Detecta o tipo de requisição
        request_type = alexa_request.get("request", {}).get("type", "")
        logger.info(f"[Alexa Skill] Tipo de requisição: {request_type}")
        
        # Para LaunchRequest (quando o usuário abre a skill)
        if request_type == "LaunchRequest":
            logger.info("[Alexa Skill] LaunchRequest detectado - iniciando conversa")
            welcome_response = {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Bem-vindo à conversa em inglês com IA! Como posso ajudar você hoje? Você pode me fazer perguntas ou praticar conversação em inglês."
                    },
                    "reprompt": {
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Como posso ajudar você com o inglês hoje?"
                        }
                    },
                    "shouldEndSession": False
                }
            }
            return jsonify(welcome_response)
        
        # Para SessionEndedRequest
        elif request_type == "SessionEndedRequest":
            logger.info("[Alexa Skill] SessionEndedRequest - encerrando sessão")
            return jsonify({
                "version": "1.0",
                "response": {
                    "shouldEndSession": True
                }
            })
        
        # Para IntentRequest (interações do usuário)
        elif request_type == "IntentRequest":
            intent_name = alexa_request.get("request", {}).get("intent", {}).get("name", "")
            logger.info(f"[Alexa Skill] Intent detectado: {intent_name}")
            
            # Trata intents especiais da Amazon
            if intent_name == "AMAZON.StopIntent" or intent_name == "AMAZON.CancelIntent":
                return jsonify({
                    "version": "1.0",
                    "response": {
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Até logo! Foi ótimo conversar com você. Volte sempre para praticar mais inglês!"
                        },
                        "shouldEndSession": True
                    }
                })
            
            elif intent_name == "AMAZON.HelpIntent":
                return jsonify({
                    "version": "1.0",
                    "response": {
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Você pode me fazer perguntas em inglês, pedir traduções, explicações gramaticais ou simplesmente conversar para praticar. Por exemplo, diga 'What is the weather like?' ou 'How do you say olá in English?'"
                        },
                        "reprompt": {
                            "outputSpeech": {
                                "type": "PlainText",
                                "text": "O que você gostaria de aprender ou praticar?"
                            }
                        },
                        "shouldEndSession": False
                    }
                })
        
        # Envia a requisição completa da Alexa para o n8n e espera a resposta
        n8n_alexa_response = n8n_integration.process_alexa_request_with_n8n(alexa_request)

        if n8n_alexa_response:
            logger.info(f"[Alexa Skill] Resposta formatada do n8n recebida: {json.dumps(n8n_alexa_response, indent=2)}")
            return jsonify(n8n_alexa_response)
        else:
            logger.error("[Alexa Skill] N8N não retornou uma resposta válida ou ocorreu um erro no processamento.")
            # Fallback para uma resposta de erro padrão da Alexa
            error_response = {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Desculpe, não consegui processar sua solicitação no momento. Por favor, tente novamente."
                    },
                    "reprompt": {
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": "Você pode tentar fazer sua pergunta de outra forma?"
                        }
                    },
                    "shouldEndSession": False
                }
            }
            return jsonify(error_response)

    except Exception as e:
        logger.error(f"[Alexa Skill] Erro no processamento da skill Alexa: {str(e)}", exc_info=True)
        error_response = {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Desculpe, ocorreu um erro inesperado. Por favor, tente novamente."
                },
                "shouldEndSession": False
            }
        }
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

@alexa_bp.route("/test-alexa-request", methods=["POST"])
def test_alexa_request():
    """
    Endpoint de teste para simular uma requisição da Alexa
    """
    try:
        # Requisição de teste simulada
        test_alexa_request = request.get_json() or {
            "version": "1.0",
            "session": {
                "new": True,
                "sessionId": "test-session-123",
                "user": {
                    "userId": "test-user-123"
                }
            },
            "request": {
                "type": "IntentRequest",
                "requestId": "test-request-123",
                "locale": "pt-BR",
                "timestamp": "2025-09-12T18:00:00Z",
                "intent": {
                    "name": "HelloWorldIntent",
                    "slots": {
                        "message": {
                            "value": "Hello, how are you?"
                        }
                    }
                }
            }
        }
        
        logger.info(f"[Test] Enviando requisição de teste: {json.dumps(test_alexa_request, indent=2)}")
        
        # Processa como se fosse uma requisição real
        n8n_response = n8n_integration.process_alexa_request_with_n8n(test_alexa_request)
        
        if n8n_response:
            return jsonify({
                "status": "success",
                "alexa_response": n8n_response
            })
        else:
            return jsonify({
                "status": "error",
                "message": "N8N não retornou resposta"
            }), 500
            
    except Exception as e:
        logger.error(f"[Test] Erro no teste: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500