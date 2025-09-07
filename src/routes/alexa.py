from flask import Blueprint, request, jsonify
import json
import logging
from src.services.n8n_integration import n8n_integration

alexa_bp = Blueprint('alexa', __name__)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@alexa_bp.route('/alexa', methods=['POST'])
def alexa_skill():
    """
    Endpoint principal para receber requisições da Alexa
    """
    try:

        alexa_request = request.get_json()
        

        logger.info(f"Alexa Request: {json.dumps(alexa_request, indent=2)}")

        request_type = alexa_request.get('request', {}).get('type')
        intent_name = alexa_request.get('request', {}).get('intent', {}).get('name')
        user_input = alexa_request.get('request', {}).get('intent', {}).get('slots', {})
        session_id = alexa_request.get('session', {}).get('sessionId')
        user_id = alexa_request.get('session', {}).get('user', {}).get('userId')

        if request_type == 'LaunchRequest':
            response = handle_launch_request(alexa_request)
        elif request_type == 'IntentRequest':
            response = handle_intent_request(alexa_request, intent_name, user_input)
        elif request_type == 'SessionEndedRequest':
            response = handle_session_ended_request(alexa_request)
        else:
            response = create_response("Desculpe, não entendi sua solicitação.", False)

        send_to_n8n(alexa_request, response)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        error_response = create_response("Desculpe, ocorreu um erro. Tente novamente.", True)
        return jsonify(error_response)

def handle_launch_request(alexa_request):
    """
    Manipula a requisição de abertura da skill
    """
    welcome_message = "Olá! Bem-vindo à nossa skill. Como posso ajudá-lo hoje?"
    reprompt_message = "Você pode me fazer uma pergunta ou pedir ajuda. O que gostaria de saber?"
    
    return create_response_with_reprompt(welcome_message, reprompt_message, False)

def handle_intent_request(alexa_request, intent_name, user_input):
    """
    Manipula requisições de intent
    """
    if intent_name == 'AMAZON.HelpIntent':
        help_message = "Esta skill pode ajudá-lo com várias tarefas. Você pode fazer perguntas ou solicitar informações. O que você gostaria de saber?"
        return create_response_with_reprompt(help_message, "Como posso ajudá-lo?", False)
    
    elif intent_name == 'AMAZON.StopIntent' or intent_name == 'AMAZON.CancelIntent':
        goodbye_message = "Obrigado por usar nossa skill. Até logo!"
        return create_response(goodbye_message, True)
    
    elif intent_name == 'UserInputIntent':
        # Intent personalizada para capturar entrada do usuário
        user_text = extract_user_text(user_input)
        response_text = process_user_input(user_text, alexa_request)
        return create_response_with_reprompt(response_text, "Há mais alguma coisa que posso ajudar?", False)
    
    else:
        # Intent não reconhecida
        fallback_message = "Não entendi sua solicitação. Pode repetir de forma diferente?"
        return create_response_with_reprompt(fallback_message, "Como posso ajudá-lo?", False)

def handle_session_ended_request(alexa_request):
    """
    Manipula o fim da sessão
    """
    return create_response("", True)

def extract_user_text(slots):
    """
    Extrai o texto do usuário dos slots
    """
    if 'userText' in slots and 'value' in slots['userText']:
        return slots['userText']['value']
    return ""

def process_user_input(user_text, alexa_request):
    """
    Processa a entrada do usuário usando n8n para gerar resposta inteligente
    """
    if not user_text:
        return "Não consegui entender o que você disse. Pode repetir?"
    
    # Preparar contexto da conversa
    context = {
        "session_id": alexa_request.get('session', {}).get('sessionId'),
        "user_id": alexa_request.get('session', {}).get('user', {}).get('userId'),
        "session_attributes": alexa_request.get('session', {}).get('attributes', {}),
        "locale": alexa_request.get('request', {}).get('locale', 'pt-BR')
    }
    
    # Tentar obter resposta do n8n
    n8n_response = n8n_integration.get_response_from_n8n(user_text, context)
    
    if n8n_response:
        return n8n_response
    else:
        # Fallback caso n8n não esteja disponível
        return f"Entendi que você disse: {user_text}. Como posso ajudá-lo com isso? (Processamento avançado temporariamente indisponível)"

def send_to_n8n(alexa_request, alexa_response):
    """
    Envia dados para o webhook do n8n usando o serviço de integração
    """
    try:
        result = n8n_integration.send_alexa_data(alexa_request, alexa_response)
        
        if result:
            logger.info("Dados enviados para n8n com sucesso")
        else:
            logger.warning("Falha ao enviar dados para n8n")
            
    except Exception as e:
        logger.error(f"Erro ao enviar dados para n8n: {str(e)}")

def create_response(output_speech, should_end_session):
    """
    Cria uma resposta básica para a Alexa
    """
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": output_speech
            },
            "shouldEndSession": should_end_session
        }
    }

def create_response_with_reprompt(output_speech, reprompt_text, should_end_session):
    """
    Cria uma resposta com reprompt para a Alexa
    """
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": output_speech
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": reprompt_text
                }
            },
            "shouldEndSession": should_end_session
        }
    }

@alexa_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar se o serviço está funcionando
    """
    return jsonify({"status": "healthy", "service": "alexa-skill"})


@alexa_bp.route('/n8n-status', methods=['GET'])
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

@alexa_bp.route('/send-test-event', methods=['POST'])
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

