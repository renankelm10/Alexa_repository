#!/usr/bin/env python3
"""
Script de teste para simular requisições da Alexa para a skill
"""

import requests
import json
import sys

def create_launch_request():
    """Cria uma requisição de abertura da skill"""
    return {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": "amzn1.echo-api.session.test-session-id",
            "application": {
                "applicationId": "amzn1.ask.skill.test-skill-id"
            },
            "user": {
                "userId": "amzn1.ask.account.test-user-id"
            },
            "attributes": {}
        },
        "context": {
            "System": {
                "application": {
                    "applicationId": "amzn1.ask.skill.test-skill-id"
                },
                "user": {
                    "userId": "amzn1.ask.account.test-user-id"
                },
                "device": {
                    "deviceId": "amzn1.ask.device.test-device-id",
                    "supportedInterfaces": {}
                }
            }
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": "amzn1.echo-api.request.test-request-id",
            "timestamp": "2025-09-02T19:00:00Z",
            "locale": "pt-BR"
        }
    }

def create_intent_request(user_text):
    """Cria uma requisição de intent com texto do usuário"""
    return {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": "amzn1.echo-api.session.test-session-id",
            "application": {
                "applicationId": "amzn1.ask.skill.test-skill-id"
            },
            "user": {
                "userId": "amzn1.ask.account.test-user-id"
            },
            "attributes": {}
        },
        "context": {
            "System": {
                "application": {
                    "applicationId": "amzn1.ask.skill.test-skill-id"
                },
                "user": {
                    "userId": "amzn1.ask.account.test-user-id"
                },
                "device": {
                    "deviceId": "amzn1.ask.device.test-device-id",
                    "supportedInterfaces": {}
                }
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.test-request-id",
            "timestamp": "2025-09-02T19:00:00Z",
            "locale": "pt-BR",
            "intent": {
                "name": "UserInputIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "userText": {
                        "name": "userText",
                        "value": user_text,
                        "confirmationStatus": "NONE"
                    }
                }
            }
        }
    }

def test_endpoint(url, request_data, test_name):
    """Testa um endpoint com dados específicos"""
    print(f"\n=== {test_name} ===")
    print(f"URL: {url}")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    try:
        response = requests.post(url, json=request_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return False

def test_health_endpoint(base_url):
    """Testa o endpoint de saúde"""
    print("\n=== Teste de Saúde ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição de saúde: {e}")
        return False

def test_n8n_status(base_url):
    """Testa o status da integração com n8n"""
    print("\n=== Teste de Status N8N ===")
    try:
        response = requests.get(f"{base_url}/n8n-status", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição de status n8n: {e}")
        return False

def main():
    base_url = "http://localhost:5000/api"
    alexa_url = f"{base_url}/alexa"
    
    print("=== Teste da Skill da Alexa ===")
    print(f"Base URL: {base_url}")
    
    # Teste 1: Health Check
    health_ok = test_health_endpoint(base_url)
    
    # Teste 2: N8N Status
    n8n_ok = test_n8n_status(base_url)
    
    # Teste 3: Launch Request
    launch_request = create_launch_request()
    launch_ok = test_endpoint(alexa_url, launch_request, "Teste de Abertura da Skill")
    
    # Teste 4: Intent Request - Saudação
    intent_request_1 = create_intent_request("Olá, como você está?")
    intent_ok_1 = test_endpoint(alexa_url, intent_request_1, "Teste de Intent - Saudação")
    
    # Teste 5: Intent Request - Pergunta
    intent_request_2 = create_intent_request("Qual é a capital do Brasil?")
    intent_ok_2 = test_endpoint(alexa_url, intent_request_2, "Teste de Intent - Pergunta")
    
    # Teste 6: Intent Request - Ajuda
    intent_request_3 = create_intent_request("preciso de ajuda")
    intent_ok_3 = test_endpoint(alexa_url, intent_request_3, "Teste de Intent - Ajuda")
    
    # Resumo dos testes
    print("\n=== RESUMO DOS TESTES ===")
    tests = [
        ("Health Check", health_ok),
        ("N8N Status", n8n_ok),
        ("Launch Request", launch_ok),
        ("Intent - Saudação", intent_ok_1),
        ("Intent - Pergunta", intent_ok_2),
        ("Intent - Ajuda", intent_ok_3)
    ]
    
    for test_name, result in tests:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, result in tests if result)
    print(f"\nTotal: {total_passed}/{len(tests)} testes passaram")
    
    if total_passed == len(tests):
        print("🎉 Todos os testes passaram!")
        return 0
    else:
        print("⚠️  Alguns testes falharam")
        return 1

if __name__ == "__main__":
    sys.exit(main())

