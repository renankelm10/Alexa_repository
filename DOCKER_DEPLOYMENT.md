# Guia de Deployment Docker - Skill da Alexa

## Visão Geral

Este guia fornece instruções completas para fazer o deployment da skill da Alexa usando Docker em qualquer VPS. A solução é containerizada e inclui todos os componentes necessários: aplicação Flask, Nginx como proxy reverso, Redis para cache, e opcionalmente Prometheus/Grafana para monitoramento.

## Pré-requisitos

### Requisitos do Servidor

- **Sistema Operacional**: Ubuntu 20.04+ (recomendado) ou qualquer distribuição Linux com suporte ao Docker
- **RAM**: Mínimo 2GB, recomendado 4GB+
- **Armazenamento**: Mínimo 20GB de espaço livre
- **CPU**: 2 cores recomendado
- **Rede**: Porta 80 e 443 abertas para tráfego HTTP/HTTPS

### Software Necessário

1. **Docker** (versão 20.10+)
2. **Docker Compose** (versão 2.0+)
3. **Git** para clonar o repositório
4. **Curl** para testes

## Instalação do Docker

### Ubuntu/Debian

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório do Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Reiniciar sessão ou executar
newgrp docker

# Verificar instalação
docker --version
docker compose version
```

### CentOS/RHEL

```bash
# Instalar Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo
sudo usermod -aG docker $USER
```

## Configuração do Projeto

### 1. Preparar o Ambiente

```bash
# Clonar ou transferir o projeto para o servidor
# Se usando Git:
git clone https://github.com/seu-usuario/alexa-skill-app.git
cd alexa-skill-app

# Ou se transferindo arquivos:
scp -r alexa-skill-app/ usuario@seu-servidor:/home/usuario/
ssh usuario@seu-servidor
cd alexa-skill-app
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

**Configurações importantes no arquivo .env:**

```bash
# OBRIGATÓRIO: Alterar estas configurações
SECRET_KEY=sua-chave-secreta-super-segura-aqui
N8N_WEBHOOK_URL=https://sua-instancia-n8n.com/webhook/alexa-skill
DOMAIN_NAME=seu-dominio.com

# Opcional: Configurações avançadas
REDIS_URL=redis://redis:6379/0
GRAFANA_PASSWORD=senha-segura-grafana
LOG_LEVEL=INFO
```

### 3. Configurar SSL

#### Opção A: Certificado Auto-assinado (Desenvolvimento)

O script de deploy criará automaticamente um certificado auto-assinado.

#### Opção B: Let's Encrypt (Produção)

```bash
# Instalar Certbot
sudo apt install -y certbot

# Obter certificado (substitua seu-dominio.com)
sudo certbot certonly --standalone -d seu-dominio.com

# Copiar certificados para o projeto
sudo cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem
```

#### Opção C: Certificado Próprio

```bash
# Copiar seus certificados
cp seu-certificado.pem nginx/ssl/cert.pem
cp sua-chave-privada.pem nginx/ssl/key.pem
```

## Deploy Automatizado

### Usando o Script de Deploy

O projeto inclui um script automatizado que facilita todo o processo:

```bash
# Tornar executável (se necessário)
chmod +x docker-deploy.sh

# Deploy completo (recomendado para primeira vez)
./docker-deploy.sh full

# Ou modo interativo
./docker-deploy.sh
```

### Deploy Manual

Se preferir fazer o deploy manualmente:

```bash
# 1. Criar diretórios necessários
mkdir -p logs data nginx/ssl nginx/logs

# 2. Build da imagem
docker compose build

# 3. Iniciar serviços
docker compose up -d

# 4. Verificar status
docker compose ps

# 5. Verificar logs
docker compose logs -f alexa-skill
```

## Configuração do Nginx

### Personalizar Configuração

O arquivo `nginx/nginx.conf` pode ser personalizado conforme necessário:

```bash
# Editar configuração do Nginx
nano nginx/nginx.conf

# Reiniciar apenas o Nginx
docker compose restart nginx
```

### Configurações Importantes

1. **Rate Limiting**: Configurado para proteger contra abuso
2. **SSL/TLS**: Configurações seguras com TLS 1.2+
3. **Headers de Segurança**: HSTS, X-Frame-Options, etc.
4. **Timeouts**: Otimizados para requisições da Alexa (< 8s)

## Monitoramento

### Logs da Aplicação

```bash
# Ver logs em tempo real
docker compose logs -f alexa-skill

# Ver logs específicos
docker compose logs alexa-skill --tail=100

# Ver logs do Nginx
docker compose logs nginx --tail=50
```

### Health Checks

```bash
# Verificar saúde da aplicação
curl https://seu-dominio.com/health

# Verificar status do n8n
curl https://seu-dominio.com/api/n8n-status

# Status dos containers
docker compose ps
```

### Métricas (Opcional)

Se habilitou Prometheus e Grafana:

```bash
# Acessar Grafana
# URL: http://seu-dominio.com:3000
# Usuário: admin
# Senha: definida no .env (GRAFANA_PASSWORD)

# Acessar Prometheus
# URL: http://seu-dominio.com:9090
```

## Manutenção

### Atualizações

```bash
# Parar serviços
docker compose down

# Atualizar código (se usando Git)
git pull

# Rebuild e restart
docker compose build --no-cache
docker compose up -d

# Verificar se tudo está funcionando
./docker-deploy.sh status
```

### Backup

```bash
# Backup automático usando o script
./docker-deploy.sh backup

# Backup manual
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
docker run --rm -v alexa-skill-app_redis_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
cp -r logs data backup/
```

### Restauração

```bash
# Restaurar usando o script
./docker-deploy.sh restore backup/20250902_120000

# Restauração manual
docker compose down
# ... restaurar arquivos ...
docker compose up -d
```

### Limpeza

```bash
# Limpar recursos não utilizados
./docker-deploy.sh cleanup

# Ou manualmente
docker system prune -f
docker volume prune -f
```

## Configuração da Skill na Amazon

### 1. Endpoint da Skill

No console da Amazon Developer:

1. Vá para "Build" > "Endpoint"
2. Selecione "HTTPS"
3. Configure:
   - **Default Region**: `https://seu-dominio.com/api/alexa`
   - **SSL Certificate**: Selecione a opção apropriada baseada no seu certificado

### 2. Teste da Skill

```bash
# Testar endpoint localmente
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

## Troubleshooting

### Problemas Comuns

#### 1. Container não inicia

```bash
# Verificar logs
docker compose logs alexa-skill

# Verificar configuração
docker compose config

# Verificar recursos
docker system df
```

#### 2. SSL/HTTPS não funciona

```bash
# Verificar certificados
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Testar SSL
openssl s_client -connect seu-dominio.com:443

# Verificar configuração do Nginx
docker compose exec nginx nginx -t
```

#### 3. Aplicação lenta

```bash
# Verificar recursos
docker stats

# Verificar logs de performance
docker compose logs alexa-skill | grep "duration"

# Verificar conectividade com n8n
curl -w "@curl-format.txt" -o /dev/null -s https://seu-n8n.com/webhook/test
```

#### 4. Rate Limiting

```bash
# Verificar logs do Nginx
docker compose logs nginx | grep "limiting"

# Ajustar configuração se necessário
nano nginx/nginx.conf
docker compose restart nginx
```

### Comandos Úteis

```bash
# Entrar no container da aplicação
docker compose exec alexa-skill bash

# Entrar no container do Nginx
docker compose exec nginx sh

# Verificar conectividade de rede
docker compose exec alexa-skill ping nginx
docker compose exec alexa-skill curl http://nginx/health

# Verificar variáveis de ambiente
docker compose exec alexa-skill env | grep N8N

# Reiniciar apenas um serviço
docker compose restart alexa-skill

# Ver uso de recursos
docker compose top
```

## Segurança

### Configurações de Segurança

1. **Firewall**: Configure apenas portas 80, 443 e SSH
2. **SSL**: Use certificados válidos em produção
3. **Secrets**: Nunca commite arquivos .env
4. **Updates**: Mantenha Docker e sistema atualizados
5. **Monitoring**: Configure alertas para falhas

### Hardening do Servidor

```bash
# Configurar firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Configurar fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# Desabilitar root login SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart ssh
```

## Performance

### Otimizações

1. **Resources**: Ajustar limites de CPU/memória no docker-compose.yml
2. **Cache**: Redis configurado para cache de respostas
3. **Connection Pooling**: Nginx configurado com keep-alive
4. **Compression**: Gzip habilitado no Nginx

### Monitoramento de Performance

```bash
# Verificar uso de recursos
docker stats --no-stream

# Verificar tempo de resposta
curl -w "@curl-format.txt" -o /dev/null -s https://seu-dominio.com/api/health

# Verificar logs de performance
docker compose logs alexa-skill | grep -E "(duration|time)"
```

## Escalabilidade

### Escalar Horizontalmente

```bash
# Aumentar número de workers da aplicação
docker compose up -d --scale alexa-skill=3

# Usar load balancer (nginx já configurado)
# Adicionar mais instâncias conforme necessário
```

### Escalar Verticalmente

```bash
# Editar docker-compose.yml
# Adicionar limites de recursos:
# deploy:
#   resources:
#     limits:
#       cpus: '2.0'
#       memory: 2G
#     reservations:
#       cpus: '1.0'
#       memory: 1G
```

## Conclusão

Este guia fornece uma solução completa para deploy da skill da Alexa usando Docker. A configuração é robusta, escalável e adequada tanto para desenvolvimento quanto para produção.

### Próximos Passos

1. Configure monitoramento avançado
2. Implemente CI/CD pipeline
3. Configure backup automático
4. Adicione mais funcionalidades à skill
5. Otimize performance baseado no uso real

Para suporte adicional, consulte os logs da aplicação e a documentação oficial do Docker e da Amazon Alexa.

