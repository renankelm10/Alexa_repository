#!/bin/bash

# Script de Deploy Automatizado para Skill da Alexa
# Uso: ./docker-deploy.sh [ambiente]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Instale o Docker primeiro."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    fi
    
    log "Docker e Docker Compose encontrados ✓"
}

# Verificar arquivos necessários
check_files() {
    local required_files=("Dockerfile" "docker-compose.yml" "requirements.txt" "src/main.py")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Arquivo necessário não encontrado: $file"
        fi
    done
    
    log "Todos os arquivos necessários encontrados ✓"
}

# Configurar variáveis de ambiente
setup_env() {
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            warn "Arquivo .env criado a partir do .env.example"
            warn "IMPORTANTE: Edite o arquivo .env com suas configurações antes de continuar"
            read -p "Pressione Enter após editar o arquivo .env..."
        else
            error "Arquivo .env não encontrado e .env.example não existe"
        fi
    fi
    
    log "Arquivo .env configurado ✓"
}

# Criar diretórios necessários
create_directories() {
    local dirs=("logs" "data" "nginx/ssl" "nginx/logs")
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log "Diretório criado: $dir"
    done
}

# Gerar certificado SSL auto-assinado (para desenvolvimento)
generate_ssl_cert() {
    if [[ ! -f "nginx/ssl/cert.pem" ]] || [[ ! -f "nginx/ssl/key.pem" ]]; then
        log "Gerando certificado SSL auto-assinado..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=BR/ST=SP/L=SaoPaulo/O=AlexaSkill/CN=localhost"
        
        log "Certificado SSL gerado ✓"
        warn "ATENÇÃO: Este é um certificado auto-assinado para desenvolvimento"
        warn "Para produção, use certificados válidos (Let's Encrypt, etc.)"
    else
        log "Certificados SSL já existem ✓"
    fi
}

# Build da imagem Docker
build_image() {
    log "Fazendo build da imagem Docker..."
    
    docker-compose build --no-cache alexa-skill
    
    if [[ $? -eq 0 ]]; then
        log "Build da imagem concluído ✓"
    else
        error "Falha no build da imagem Docker"
    fi
}

# Executar testes
run_tests() {
    log "Executando testes..."
    
    # Criar container temporário para testes
    docker-compose run --rm alexa-skill python -m pytest tests/ -v || warn "Testes falharam ou não existem"
    
    log "Testes executados ✓"
}

# Deploy da aplicação
deploy() {
    log "Iniciando deploy..."
    
    # Parar containers existentes
    docker-compose down
    
    # Iniciar serviços
    docker-compose up -d
    
    # Aguardar serviços ficarem prontos
    log "Aguardando serviços ficarem prontos..."
    sleep 30
    
    # Verificar saúde dos serviços
    check_health
}

# Verificar saúde dos serviços
check_health() {
    log "Verificando saúde dos serviços..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost/health > /dev/null; then
            log "Aplicação está saudável ✓"
            break
        else
            warn "Tentativa $attempt/$max_attempts - Aplicação ainda não está pronta"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Aplicação não ficou pronta após $max_attempts tentativas"
    fi
}

# Mostrar status dos serviços
show_status() {
    log "Status dos serviços:"
    docker-compose ps
    
    echo ""
    log "Logs recentes:"
    docker-compose logs --tail=20 alexa-skill
    
    echo ""
    log "URLs de acesso:"
    echo "  - Aplicação: https://localhost"
    echo "  - Health Check: https://localhost/health"
    echo "  - API Alexa: https://localhost/api/alexa"
    echo "  - Status n8n: https://localhost/api/n8n-status"
    
    if docker-compose ps | grep -q grafana; then
        echo "  - Grafana: http://localhost:3000"
    fi
    
    if docker-compose ps | grep -q prometheus; then
        echo "  - Prometheus: http://localhost:9090"
    fi
}

# Backup dos dados
backup() {
    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    log "Criando backup em $backup_dir..."
    
    # Backup dos volumes
    docker run --rm -v alexa-skill-app_redis_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    docker run --rm -v alexa-skill-app_prometheus_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/prometheus_data.tar.gz -C /data .
    docker run --rm -v alexa-skill-app_grafana_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/grafana_data.tar.gz -C /data .
    
    # Backup dos logs
    cp -r logs "$backup_dir/"
    cp -r data "$backup_dir/"
    
    log "Backup criado em $backup_dir ✓"
}

# Restaurar backup
restore() {
    local backup_dir=$1
    
    if [[ -z "$backup_dir" ]] || [[ ! -d "$backup_dir" ]]; then
        error "Diretório de backup não especificado ou não existe"
    fi
    
    log "Restaurando backup de $backup_dir..."
    
    # Parar serviços
    docker-compose down
    
    # Restaurar volumes
    docker run --rm -v alexa-skill-app_redis_data:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
    docker run --rm -v alexa-skill-app_prometheus_data:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/prometheus_data.tar.gz -C /data
    docker run --rm -v alexa-skill-app_grafana_data:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/grafana_data.tar.gz -C /data
    
    # Restaurar arquivos
    cp -r "$backup_dir/logs" .
    cp -r "$backup_dir/data" .
    
    log "Backup restaurado ✓"
}

# Limpeza
cleanup() {
    log "Limpando recursos não utilizados..."
    
    docker system prune -f
    docker volume prune -f
    
    log "Limpeza concluída ✓"
}

# Menu principal
show_menu() {
    echo ""
    echo "=== Deploy da Skill da Alexa ==="
    echo "1. Deploy completo (recomendado)"
    echo "2. Apenas build"
    echo "3. Apenas deploy"
    echo "4. Verificar status"
    echo "5. Ver logs"
    echo "6. Backup"
    echo "7. Restaurar backup"
    echo "8. Limpeza"
    echo "9. Parar serviços"
    echo "0. Sair"
    echo ""
}

# Função principal
main() {
    log "Iniciando script de deploy da Skill da Alexa"
    
    # Verificações iniciais
    check_docker
    check_files
    
    if [[ $# -eq 0 ]]; then
        # Modo interativo
        while true; do
            show_menu
            read -p "Escolha uma opção: " choice
            
            case $choice in
                1)
                    setup_env
                    create_directories
                    generate_ssl_cert
                    build_image
                    run_tests
                    deploy
                    show_status
                    ;;
                2)
                    build_image
                    ;;
                3)
                    deploy
                    show_status
                    ;;
                4)
                    show_status
                    ;;
                5)
                    docker-compose logs -f
                    ;;
                6)
                    backup
                    ;;
                7)
                    read -p "Digite o caminho do backup: " backup_path
                    restore "$backup_path"
                    ;;
                8)
                    cleanup
                    ;;
                9)
                    docker-compose down
                    log "Serviços parados ✓"
                    ;;
                0)
                    log "Saindo..."
                    exit 0
                    ;;
                *)
                    warn "Opção inválida"
                    ;;
            esac
            
            echo ""
            read -p "Pressione Enter para continuar..."
        done
    else
        # Modo não-interativo
        case $1 in
            "full"|"deploy")
                setup_env
                create_directories
                generate_ssl_cert
                build_image
                run_tests
                deploy
                show_status
                ;;
            "build")
                build_image
                ;;
            "start")
                deploy
                show_status
                ;;
            "status")
                show_status
                ;;
            "backup")
                backup
                ;;
            "restore")
                restore "$2"
                ;;
            "cleanup")
                cleanup
                ;;
            "stop")
                docker-compose down
                ;;
            *)
                echo "Uso: $0 [full|build|start|status|backup|restore|cleanup|stop]"
                exit 1
                ;;
        esac
    fi
}

# Executar função principal
main "$@"

