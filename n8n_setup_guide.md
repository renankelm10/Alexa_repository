# Guia de Configuração do n8n para Integração com Alexa Skill

## Pré-requisitos

1. **Instância do n8n funcionando**
   - n8n instalado e rodando (local ou na nuvem)
   - Acesso à interface web do n8n
   - URL pública acessível (para receber webhooks da Alexa)

2. **Credenciais necessárias**
   - OpenAI API Key (para respostas inteligentes)
   - OpenWeather API Key (opcional, para informações meteorológicas)

## Passo 1: Configurar o Webhook no n8n

1. **Criar um novo workflow**
   - Acesse a interface do n8n
   - Clique em "New Workflow"
   - Nomeie como "Alexa Skill Integration"

2. **Adicionar nó Webhook**
   - Arraste o nó "Webhook" para o canvas
   - Configure:
     - **HTTP Method**: POST
     - **Path**: `alexa-skill`
     - **Response Mode**: "Using 'Respond to Webhook' Node"

3. **Obter URL do Webhook**
   - Após salvar, copie a URL do webhook
   - Formato: `https://sua-instancia-n8n.com/webhook/alexa-skill`

## Passo 2: Configurar Processamento de Dados

### Nó "Check Action Type" (IF)
```json
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.action}}",
        "operation": "equal",
        "value2": "get_response"
      }
    ]
  }
}
```

### Nó "Extract Data" (Set)
```json
{
  "values": {
    "string": [
      {
        "name": "user_input",
        "value": "={{$json.user_input}}"
      },
      {
        "name": "session_id",
        "value": "={{$json.context.session_id}}"
      },
      {
        "name": "user_id",
        "value": "={{$json.context.user_id}}"
      },
      {
        "name": "locale",
        "value": "={{$json.context.locale}}"
      }
    ]
  }
}
```

## Passo 3: Configurar Integração com OpenAI

1. **Adicionar credencial OpenAI**
   - Vá em "Credentials" → "Add Credential"
   - Selecione "OpenAI"
   - Insira sua API Key

2. **Configurar nó OpenAI Chat**
   - **Operation**: Text
   - **System Message**: 
     ```
     Você é um assistente virtual inteligente integrado com a Alexa. 
     Responda de forma natural, útil e conversacional em português brasileiro. 
     Mantenha as respostas concisas mas informativas, adequadas para serem 
     faladas pela Alexa.
     ```
   - **Text**: `={{$json.user_input}}`

## Passo 4: Configurar Resposta

### Nó "Format Response" (Set)
```json
{
  "values": {
    "string": [
      {
        "name": "response_text",
        "value": "={{$json.response}}"
      },
      {
        "name": "processed_at",
        "value": "={{new Date().toISOString()}}"
      },
      {
        "name": "session_id",
        "value": "={{$('Extract Data').item.json.session_id}}"
      }
    ]
  }
}
```

### Nó "Respond to Webhook"
- **Respond With**: JSON
- **Response Body**: `={{$json}}`

## Passo 5: Configurar Logging (Opcional)

### Banco de Dados SQLite
```sql
CREATE TABLE alexa_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    session_id TEXT,
    user_id TEXT,
    request_type TEXT,
    intent_name TEXT,
    user_input TEXT,
    response_text TEXT,
    locale TEXT
);
```

## Passo 6: Funcionalidades Avançadas

### Detecção de Pedidos de Ajuda
```json
{
  "conditions": {
    "string": [
      {
        "value1": "={{$json.user_input}}",
        "operation": "contains",
        "value2": "ajuda"
      }
    ]
  }
}
```

### Integração com API de Clima
```json
{
  "url": "https://api.openweathermap.org/data/2.5/weather",
  "queryParameters": {
    "parameters": [
      {
        "name": "q",
        "value": "={{$json.user_input.match(/clima.*?([A-Za-z\\s]+)/)?.[1] || 'São Paulo'}}"
      },
      {
        "name": "appid",
        "value": "YOUR_OPENWEATHER_API_KEY"
      },
      {
        "name": "lang",
        "value": "pt_br"
      },
      {
        "name": "units",
        "value": "metric"
      }
    ]
  }
}
```

## Passo 7: Testar a Integração

1. **Ativar o workflow**
   - Clique em "Active" no workflow
   - Verifique se o webhook está ativo

2. **Testar com curl**
   ```bash
   curl -X POST https://sua-instancia-n8n.com/webhook/alexa-skill \
     -H "Content-Type: application/json" \
     -d '{
       "action": "get_response",
       "user_input": "Olá, como você está?",
       "context": {
         "session_id": "test-session",
         "user_id": "test-user",
         "locale": "pt-BR"
       }
     }'
   ```

3. **Verificar logs**
   - Monitore execuções no n8n
   - Verifique se as respostas estão sendo geradas corretamente

## Passo 8: Configurar na Skill da Alexa

1. **Atualizar variável de ambiente**
   ```bash
   export N8N_WEBHOOK_URL="https://sua-instancia-n8n.com/webhook/alexa-skill"
   ```

2. **Ou configurar no código**
   ```python
   # Em src/services/n8n_integration.py
   self.webhook_url = "https://sua-instancia-n8n.com/webhook/alexa-skill"
   ```

## Troubleshooting

### Problemas Comuns

1. **Webhook não responde**
   - Verificar se o workflow está ativo
   - Confirmar URL do webhook
   - Verificar logs de execução

2. **OpenAI não funciona**
   - Verificar API Key
   - Confirmar créditos na conta OpenAI
   - Verificar configuração de credenciais

3. **Timeout na resposta**
   - Aumentar timeout na skill da Alexa
   - Otimizar workflow para resposta mais rápida
   - Implementar cache para respostas frequentes

### Monitoramento

1. **Logs do n8n**
   - Acompanhar execuções em tempo real
   - Verificar erros e falhas

2. **Métricas**
   - Tempo de resposta
   - Taxa de sucesso
   - Volume de requisições

## Próximos Passos

1. **Implementar cache**
   - Redis para respostas frequentes
   - Reduzir latência

2. **Adicionar mais integrações**
   - APIs de notícias
   - Serviços de calendário
   - Sistemas de CRM

3. **Melhorar IA**
   - Fine-tuning do modelo
   - Contexto de conversa persistente
   - Personalização por usuário

