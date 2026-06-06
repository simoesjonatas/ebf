#!/bin/bash

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== PIBVP EBF Deploy Script ===${NC}\n"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Erro: Docker não está instalado${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Erro: Docker Compose não está instalado${NC}"
    exit 1
fi

# Função para exibir menu
show_menu() {
    echo -e "${YELLOW}Escolha uma opção:${NC}"
    echo "1) Iniciar aplicação (build + up)"
    echo "2) Parar aplicação"
    echo "3) Ver logs (web)"
    echo "4) Criar superuser"
    echo "5) Rodar migrations"
    echo "6) Coletar arquivos estáticos"
    echo "7) Executar comando Django customizado"
    echo "8) Backup do banco de dados"
    echo "9) Restaurar banco de dados"
    echo "10) Limpeza de sistema Docker"
    echo "11) Sair"
    echo ""
    read -p "Opção: " choice
}

# Função para iniciar
start() {
    echo -e "${YELLOW}Construindo e iniciando containers...${NC}"
    docker-compose up -d --build
    echo -e "${GREEN}✓ Aplicação iniciada com sucesso!${NC}"
    echo "URL: http://localhost:8180"
    echo "Domínio: https://ebf.simoesti.com.br"
}

# Função para parar
stop() {
    echo -e "${YELLOW}Parando containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Containers parados${NC}"
}

# Função para logs
logs() {
    docker-compose logs -f web
}

# Função para criar superuser
create_superuser() {
    echo -e "${YELLOW}Criando superuser...${NC}"
    docker-compose exec web python manage.py createsuperuser
}

# Função para migrations
migrate() {
    echo -e "${YELLOW}Executando migrations...${NC}"
    docker-compose exec web python manage.py migrate
    echo -e "${GREEN}✓ Migrations executadas${NC}"
}

# Função para coletar estáticos
collectstatic() {
    echo -e "${YELLOW}Coletando arquivos estáticos...${NC}"
    docker-compose exec web python manage.py collectstatic --clear --noinput
    echo -e "${GREEN}✓ Estáticos coletados${NC}"
}

# Função para comando customizado
custom_command() {
    read -p "Digite o comando Django (ex: shell, dbshell, etc): " cmd
    docker-compose exec web python manage.py $cmd
}

# Função para backup
backup() {
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="backup_ebf_${timestamp}.sql"
    echo -e "${YELLOW}Criando backup em ${backup_file}...${NC}"
    docker-compose exec db pg_dump -U ebf_user -d ebf_db > "$backup_file"
    echo -e "${GREEN}✓ Backup criado: ${backup_file}${NC}"
}

# Função para restaurar
restore() {
    read -p "Digite o caminho do arquivo de backup: " backup_path
    if [ ! -f "$backup_path" ]; then
        echo -e "${RED}Arquivo não encontrado: $backup_path${NC}"
        return 1
    fi
    echo -e "${YELLOW}Restaurando banco de dados...${NC}"
    cat "$backup_path" | docker-compose exec -T db psql -U ebf_user -d ebf_db
    echo -e "${GREEN}✓ Banco restaurado${NC}"
}

# Função para limpeza
cleanup() {
    echo -e "${YELLOW}Executando limpeza do Docker...${NC}"
    docker system prune -a --volumes -f
    echo -e "${GREEN}✓ Limpeza concluída${NC}"
}

# Menu principal
while true; do
    show_menu
    case $choice in
        1) start ;;
        2) stop ;;
        3) logs ;;
        4) create_superuser ;;
        5) migrate ;;
        6) collectstatic ;;
        7) custom_command ;;
        8) backup ;;
        9) restore ;;
        10) cleanup ;;
        11) echo -e "${GREEN}Saindo...${NC}"; exit 0 ;;
        *) echo -e "${RED}Opção inválida${NC}" ;;
    esac
    echo ""
    read -p "Pressione ENTER para continuar..."
done
