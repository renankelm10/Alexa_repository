# Guia de Deployment - Skill da Alexa com n8n

## Visão Geral do Deployment

Este guia fornece instruções detalhadas para fazer o deployment da skill da Alexa em diferentes ambientes, desde desenvolvimento até produção.

## Pré-requisitos

### Contas e Serviços Necessários

1. **Amazon Developer Account**
   - Conta gratuita no [Amazon Developer Console](https://developer.amazon.com/)
   - Acesso ao Alexa Skills Kit

2. **Servidor para Hosting**
   - VPS, AWS, Heroku, ou similar
   - Suporte a Python 3.11+
   - Certificado SSL válido

3. **Instância n8n**
   - n8n Cloud ou self-hosted
   - URL pública acessível
   - Credenciais configuradas (OpenAI, etc.)

## Opção 1: Deployment no Heroku (Recomendado para Iniciantes)

### Passo 1: Preparar o Projeto

```bash
# Criar arquivo Procfile
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT src.main:app" > Procfile

# Adicionar gunicorn ao requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt

# Criar arquivo runtime.txt
echo "python-3.11.0" > runtime.txt
```

### Passo 2: Configurar Git

```bash
# Inicializar repositório
git init
git add .
git commit -m "Initial commit"

# Conectar com Heroku
heroku login
heroku create sua-alexa-skill-app
```

### Passo 3: Configurar Variáveis de Ambiente

```bash
# Configurar URL do n8n
heroku config:set N8N_WEBHOOK_URL=https://sua-instancia-n8n.com/webhook/alexa-skill

# Configurar chave secreta
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Configurar ambiente
heroku config:set FLASK_ENV=production
```

### Passo 4: Deploy

```bash
# Fazer deploy
git push heroku main

# Verificar logs
heroku logs --tail

# Abrir aplicação
heroku open
```

### Passo 5: Testar

```bash
# Testar endpoint de saúde
curl https://sua-alexa-skill-app.herokuapp.com/api/health

# Testar integração n8n
curl https://sua-alexa-skill-app.herokuapp.com/api/n8n-status
```

## Opção 2: Deployment na AWS (Produção)

### Usando AWS Lambda + API Gateway

#### Passo 1: Preparar o Código

```python
# Criar arquivo lambda_handler.py
import json
from src.main import app

def lambda_handler(event, context):
    # Converter evento do API Gateway para formato Flask
    from werkzeug.serving import WSGIRequestHandler
    from werkzeug.test import Client
    
    client = Client(app)
    
    # Processar requisição
    response = client.open(
        path=event['path'],
        method=event['httpMethod'],
        headers=event.get('headers', {}),
        data=event.get('body', '')
    )
    
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }
```

#### Passo 2: Criar Package de Deploy

```bash
# Instalar dependências em diretório local
pip install -r requirements.txt -t ./package

# Copiar código da aplicação
cp -r src/ package/
cp lambda_handler.py package/

# Criar ZIP
cd package
zip -r ../alexa-skill-lambda.zip .
cd ..
```

#### Passo 3: Configurar Lambda

```bash
# Criar função Lambda
aws lambda create-function \
  --function-name alexa-skill \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://alexa-skill-lambda.zip

# Configurar variáveis de ambiente
aws lambda update-function-configuration \
  --function-name alexa-skill \
  --environment Variables='{
    "N8N_WEBHOOK_URL":"https://sua-instancia-n8n.com/webhook/alexa-skill",
    "SECRET_KEY":"sua-chave-secreta"
  }'
```

#### Passo 4: Configurar API Gateway

```bash
# Criar API
aws apigateway create-rest-api --name alexa-skill-api

# Configurar recursos e métodos
# (Usar console AWS para configuração detalhada)
```

### Usando EC2

#### Passo 1: Configurar Servidor

```bash
# Conectar ao EC2
ssh -i sua-chave.pem ubuntu@seu-ip-ec2

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install python3 python3-pip python3-venv nginx supervisor -y
```

#### Passo 2: Configurar Aplicação

```bash
# Clonar código
git clone https://github.com/seu-usuario/alexa-skill-app.git
cd alexa-skill-app

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn
```

#### Passo 3: Configurar Nginx

```nginx
# /etc/nginx/sites-available/alexa-skill
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/alexa-skill /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Passo 4: Configurar SSL

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

#### Passo 5: Configurar Supervisor

```ini
# /etc/supervisor/conf.d/alexa-skill.conf
[program:alexa-skill]
command=/home/ubuntu/alexa-skill-app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 src.main:app
directory=/home/ubuntu/alexa-skill-app
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/alexa-skill.log
environment=N8N_WEBHOOK_URL="https://sua-instancia-n8n.com/webhook/alexa-skill"
```

```bash
# Atualizar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start alexa-skill
```

## Opção 3: Deployment com Docker

### Passo 1: Criar Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src/
COPY *.json ./

# Expor porta
EXPOSE 5000

# Comando para iniciar aplicação
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
```

### Passo 2: Criar docker-compose.yml

```yaml
version: '3.8'

services:
  alexa-skill:
    build: .
    ports:
      - "5000:5000"
    environment:
      - N8N_WEBHOOK_URL=https://sua-instancia-n8n.com/webhook/alexa-skill
      - SECRET_KEY=sua-chave-secreta
      - FLASK_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - alexa-skill
    restart: unless-stopped
```

### Passo 3: Deploy

```bash
# Build e start
docker-compose up -d

# Verificar logs
docker-compose logs -f alexa-skill

# Verificar status
docker-compose ps
```

## Configuração da Skill na Amazon

### Passo 1: Criar Skill

1. Acesse [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Clique em "Create Skill"
3. Configure:
   - **Skill name**: Assistente Conversacional
   - **Primary locale**: Portuguese (BR)
   - **Model**: Custom
   - **Hosting method**: Provision your own

### Passo 2: Configurar Interaction Model

```bash
# Copiar conteúdo do interaction_model.json
# Colar no JSON Editor da skill
# Salvar e fazer build do modelo
```

### Passo 3: Configurar Endpoint

1. Vá para "Build" > "Endpoint"
2. Selecione "HTTPS"
3. Configure:
   - **Default Region**: `https://seu-dominio.com/api/alexa`
   - **SSL Certificate**: "My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"

### Passo 4: Configurar Account Linking (Opcional)

Se precisar de autenticação de usuário:

1. Vá para "Build" > "Account Linking"
2. Configure OAuth 2.0
3. Adicione scopes necessários

## Configuração do n8n

### Deploy do n8n na Nuvem

#### Opção 1: n8n Cloud

1. Acesse [n8n.cloud](https://n8n.cloud)
2. Crie uma conta
3. Importe o workflow do arquivo `n8n_workflow_example.json`
4. Configure credenciais (OpenAI, etc.)
5. Ative o workflow
6. Copie a URL do webhook

#### Opção 2: Self-hosted

```bash
# Usando Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e WEBHOOK_URL=https://seu-dominio-n8n.com/ \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Ou usando npm
npm install n8n -g
n8n start --tunnel
```

### Configurar Webhook

1. Acesse interface do n8n
2. Importe workflow
3. Configure URL pública
4. Ative workflow
5. Teste webhook

## Monitoramento e Logs

### Configurar Logging

```python
# src/config/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/alexa-skill.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Alexa Skill startup')
```

### Configurar Métricas

```python
# src/middleware/metrics.py
from flask import request, g
import time
import logging

metrics_logger = logging.getLogger('metrics')

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    
    metrics_logger.info({
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'duration': duration,
        'user_agent': request.headers.get('User-Agent'),
        'ip': request.remote_addr
    })
    
    return response
```

### Configurar Alertas

```bash
# Script de monitoramento
#!/bin/bash
# monitor.sh

URL="https://seu-dominio.com/api/health"
WEBHOOK_SLACK="https://hooks.slack.com/services/..."

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $response != "200" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 Alexa Skill está fora do ar!"}' \
        $WEBHOOK_SLACK
fi
```

```bash
# Adicionar ao crontab
crontab -e
# */5 * * * * /path/to/monitor.sh
```

## Testes de Produção

### Teste de Carga

```python
# load_test.py
import requests
import threading
import time
import json

def test_request():
    url = "https://seu-dominio.com/api/alexa"
    data = {
        "version": "1.0",
        "session": {"sessionId": "test"},
        "request": {
            "type": "LaunchRequest",
            "requestId": "test",
            "timestamp": "2025-09-02T19:00:00Z"
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}, Time: {response.elapsed.total_seconds()}")
    except Exception as e:
        print(f"Error: {e}")

# Executar 100 requisições simultâneas
threads = []
for i in range(100):
    t = threading.Thread(target=test_request)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### Teste de Integração

```bash
# Testar fluxo completo
curl -X POST https://seu-dominio.com/api/alexa \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "session": {
      "sessionId": "test-session",
      "new": true
    },
    "request": {
      "type": "LaunchRequest",
      "requestId": "test-request",
      "timestamp": "2025-09-02T19:00:00Z"
    }
  }'
```

## Backup e Recuperação

### Backup do Código

```bash
# Script de backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_alexa_skill_$DATE.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  alexa-skill-app/
```

### Backup do n8n

```bash
# Backup dos workflows
curl -X GET https://seu-n8n.com/api/v1/workflows \
  -H "Authorization: Bearer SEU_TOKEN" \
  > workflows_backup.json
```

### Plano de Recuperação

1. **Falha do Servidor**:
   - Provisionar novo servidor
   - Restaurar código do backup
   - Reconfigurar DNS
   - Testar endpoints

2. **Falha do n8n**:
   - Restaurar instância do n8n
   - Importar workflows do backup
   - Reconfigurar credenciais
   - Testar integração

3. **Falha da Skill**:
   - Verificar logs da Amazon
   - Reconfigurar endpoint se necessário
   - Testar no simulador

## Checklist de Deploy

### Pré-Deploy

- [ ] Código testado localmente
- [ ] Testes automatizados passando
- [ ] Variáveis de ambiente configuradas
- [ ] SSL configurado
- [ ] n8n funcionando
- [ ] Backup realizado

### Deploy

- [ ] Aplicação deployada
- [ ] Endpoint acessível
- [ ] Health check funcionando
- [ ] Integração n8n testada
- [ ] Logs configurados

### Pós-Deploy

- [ ] Skill configurada na Amazon
- [ ] Testes de integração realizados
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Documentação atualizada

## Troubleshooting de Deploy

### Problemas Comuns

1. **SSL Certificate Error**
   ```bash
   # Verificar certificado
   openssl s_client -connect seu-dominio.com:443
   ```

2. **Timeout na Alexa**
   ```bash
   # Verificar tempo de resposta
   curl -w "@curl-format.txt" -o /dev/null -s https://seu-dominio.com/api/alexa
   ```

3. **n8n Não Responde**
   ```bash
   # Testar webhook
   curl -X POST https://seu-n8n.com/webhook/alexa-skill \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

### Logs Importantes

```bash
# Logs da aplicação
tail -f /var/log/alexa-skill.log

# Logs do nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Logs do sistema
journalctl -u alexa-skill -f
```

## Conclusão

Este guia fornece todas as informações necessárias para fazer o deploy da skill da Alexa em diferentes ambientes. Escolha a opção que melhor se adequa às suas necessidades e recursos disponíveis.

Para suporte adicional, consulte a documentação oficial da Amazon Alexa e do n8n.

