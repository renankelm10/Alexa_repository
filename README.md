# Skill da Alexa com Integração n8n

## Visão Geral

Esta é uma skill personalizada para Amazon Alexa que mantém conversas contínuas com o usuário, sempre esperando uma resposta após cada interação. A skill está integrada com n8n via webhooks para processamento avançado de dados e automação de workflows.

## Características Principais

- **Conversas Contínuas**: A skill mantém a sessão aberta (`shouldEndSession: false`) para permitir conversas fluidas
- **Integração n8n**: Todos os dados são enviados para n8n via webhook para processamento avançado
- **Fallback Inteligente**: Se o n8n não estiver disponível, a skill continua funcionando com respostas básicas
- **Logging Completo**: Todas as interações são registradas para análise e debugging
- **Arquitetura Modular**: Código organizado em blueprints e serviços para fácil manutenção

## Estrutura do Projeto

```
alexa-skill-app/
├── src/
│   ├── main.py                 # Aplicação Flask principal
│   ├── routes/
│   │   ├── alexa.py           # Endpoints da skill da Alexa
│   │   └── user.py            # Endpoints de usuário (template)
│   ├── services/
│   │   └── n8n_integration.py # Serviço de integração com n8n
│   ├── models/
│   │   └── user.py            # Modelos de dados (template)
│   └── static/                # Arquivos estáticos
├── interaction_model.json      # Modelo de interação da Alexa
├── skill.json                 # Configuração da skill
├── n8n_workflow_example.json  # Exemplo de workflow do n8n
├── n8n_setup_guide.md         # Guia de configuração do n8n
├── test_alexa_request.py       # Script de testes
└── requirements.txt           # Dependências Python
```

## Instalação e Configuração

### 1. Configurar o Ambiente

```bash
# Clonar ou baixar o projeto
cd alexa-skill-app

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# URL do webhook do n8n
export N8N_WEBHOOK_URL="https://sua-instancia-n8n.com/webhook/alexa-skill"
```

### 3. Iniciar o Servidor

```bash
python src/main.py
```

O servidor estará disponível em `http://localhost:5000`

## Endpoints da API

### Skill da Alexa

- **POST** `/api/alexa` - Endpoint principal para requisições da Alexa
- **GET** `/api/health` - Verificação de saúde do serviço
- **GET** `/api/n8n-status` - Status da integração com n8n
- **POST** `/api/send-test-event` - Enviar evento de teste para n8n

### Exemplos de Uso

#### Teste de Saúde
```bash
curl http://localhost:5000/api/health
```

#### Teste da Skill
```bash
curl -X POST http://localhost:5000/api/alexa \
  -H "Content-Type: application/json" \
  -d @test_launch_request.json
```

## Configuração da Skill na Amazon

### 1. Criar a Skill no Console da Amazon

1. Acesse o [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Clique em "Create Skill"
3. Configure:
   - **Skill name**: Assistente Conversacional
   - **Primary locale**: Portuguese (BR)
   - **Model**: Custom
   - **Hosting method**: Provision your own

### 2. Configurar o Modelo de Interação

1. Vá para "Build" > "Interaction Model"
2. Copie o conteúdo de `interaction_model.json`
3. Cole no JSON Editor
4. Clique em "Save Model" e "Build Model"

### 3. Configurar o Endpoint

1. Vá para "Build" > "Endpoint"
2. Selecione "HTTPS"
3. Configure:
   - **Default Region**: `https://sua-url-publica.com/api/alexa`
   - **SSL Certificate**: "My development endpoint is a sub-domain..."

### 4. Testar a Skill

1. Vá para "Test"
2. Ative o teste para "Development"
3. Digite ou fale: "abra assistente conversacional"

## Integração com n8n

### Configuração Básica

1. **Instalar n8n**:
   ```bash
   npm install n8n -g
   n8n start
   ```

2. **Importar Workflow**:
   - Acesse a interface do n8n
   - Importe o arquivo `n8n_workflow_example.json`
   - Configure as credenciais necessárias (OpenAI, etc.)

3. **Ativar Webhook**:
   - Ative o workflow
   - Copie a URL do webhook
   - Configure na variável `N8N_WEBHOOK_URL`

### Funcionalidades do Workflow

- **Processamento de Linguagem Natural**: Integração com OpenAI para respostas inteligentes
- **Detecção de Contexto**: Identifica pedidos de ajuda, clima, etc.
- **Logging**: Salva todas as interações em banco de dados
- **Respostas Personalizadas**: Diferentes tipos de resposta baseados no contexto

## Testes

### Executar Testes Automatizados

```bash
python test_alexa_request.py
```

### Testes Manuais

#### 1. Teste de Abertura
```json
{
  "request": {
    "type": "LaunchRequest"
  }
}
```

#### 2. Teste de Intent
```json
{
  "request": {
    "type": "IntentRequest",
    "intent": {
      "name": "UserInputIntent",
      "slots": {
        "userText": {
          "value": "Olá, como você está?"
        }
      }
    }
  }
}
```

## Deployment

### Opção 1: Heroku

```bash
# Instalar Heroku CLI
# Criar app
heroku create sua-alexa-skill

# Configurar variáveis
heroku config:set N8N_WEBHOOK_URL=https://sua-instancia-n8n.com/webhook/alexa-skill

# Deploy
git push heroku main
```

### Opção 2: AWS Lambda

1. Criar função Lambda
2. Fazer upload do código
3. Configurar trigger API Gateway
4. Atualizar endpoint na skill

### Opção 3: Servidor VPS

```bash
# Instalar dependências
sudo apt update
sudo apt install python3 python3-pip nginx

# Configurar nginx como proxy reverso
# Configurar SSL com Let's Encrypt
# Usar gunicorn para produção
```

## Monitoramento e Logs

### Logs da Aplicação

```bash
# Ver logs em tempo real
tail -f logs/alexa-skill.log
```

### Métricas Importantes

- **Tempo de Resposta**: < 8 segundos (limite da Alexa)
- **Taxa de Sucesso**: > 95%
- **Disponibilidade do n8n**: Monitorar endpoint de saúde

### Alertas

Configure alertas para:
- Falhas na integração com n8n
- Timeouts nas requisições
- Erros 5xx no servidor

## Troubleshooting

### Problemas Comuns

#### 1. Skill não responde
- Verificar se o servidor está rodando
- Confirmar URL do endpoint na configuração da skill
- Verificar logs de erro

#### 2. Integração n8n falha
- Verificar se o n8n está ativo
- Confirmar URL do webhook
- Verificar credenciais do OpenAI

#### 3. Timeouts
- Otimizar workflow do n8n
- Implementar cache para respostas frequentes
- Aumentar timeout na aplicação

### Logs de Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Próximos Passos

### Melhorias Planejadas

1. **Cache Redis**: Implementar cache para respostas frequentes
2. **Análise de Sentimento**: Detectar humor do usuário
3. **Personalização**: Respostas baseadas no histórico do usuário
4. **Múltiplos Idiomas**: Suporte para inglês e espanhol
5. **Integração com APIs**: Clima, notícias, calendário

### Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação da Amazon Alexa
- Verifique a documentação do n8n

## Recursos Úteis

- [Alexa Skills Kit Documentation](https://developer.amazon.com/docs/ask-overviews/build-skills-with-the-alexa-skills-kit.html)
- [n8n Documentation](https://docs.n8n.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

