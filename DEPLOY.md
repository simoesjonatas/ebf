# Guia de Deploy - PIBVP EBF

## Pré-requisitos

- Docker e Docker Compose instalados
- Acesso ao servidor com as portas 8180, 8189 e 5433 disponíveis

## Configuração Inicial

### 1. Ajustar variáveis de ambiente

Editar o arquivo `.env` com as configurações reais:

```bash
# Django Configuration
DEBUG=False
SECRET_KEY=gerar-uma-chave-secreta-aleatoria-longa
ALLOWED_HOSTS=ebf.simoesti.com.br,localhost,127.0.0.1

# Database Configuration
POSTGRES_DB=ebf_db
POSTGRES_USER=ebf_user
POSTGRES_PASSWORD=sua-senha-postgres-segura

# Email Configuration (opcional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app
```

**⚠️ Importante**: Para gerar uma SECRET_KEY segura:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 2. Configurar DNS/Proxy Reverso

Como você já tem nginx-proxy-manager rodando na porta 443, adicione um novo host:

**Configuração esperada no nginx-proxy-manager:**
- Domain: `ebf.simoesti.com.br`
- Scheme: `http`
- Forward Hostname/IP: `localhost` ou seu IP
- Forward Port: `8189`
- SSL Certificate: Usar certificado wildcard já configurado

### 3. Iniciar os containers

```bash
# Construir e iniciar
docker-compose up -d

# Ou para rebuild
docker-compose up -d --build

# Visualizar logs
docker-compose logs -f web
docker-compose logs -f db
```

### 4. Verificar status

```bash
# Verificar containers rodando
docker ps | grep ebf

# Verificar saúde do banco
docker-compose exec db pg_isready -U ebf_user -d ebf_db

# Testar acesso
curl http://localhost:8180
curl https://ebf.simoesti.com.br
```

## Portas Utilizadas

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Django (web) | 8180 | Acesso direto à aplicação |
| Nginx | 8189 | Servidor web com proxy reverso |
| PostgreSQL | 5433 | Banco de dados |

## Estrutura de Volumes

```
postgres_data/     → Dados do PostgreSQL
static_volume/     → Arquivos estáticos (CSS, JS, imagens)
media_volume/       → Upload de usuários (imagens, documentos)
```

## Operações Comuns

### Acessar banco de dados

```bash
docker-compose exec db psql -U ebf_user -d ebf_db
```

### Rodar comando Django

```bash
docker-compose exec web python manage.py <comando>

# Exemplos:
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
```

### Ver logs em tempo real

```bash
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Parar containers

```bash
docker-compose down

# Manter volumes (dados persistem)
docker-compose down

# Remover tudo incluindo volumes
docker-compose down -v
```

### Backup do banco

```bash
docker-compose exec db pg_dump -U ebf_user -d ebf_db > backup.sql
```

### Restaurar banco

```bash
cat backup.sql | docker-compose exec -T db psql -U ebf_user -d ebf_db
```

## Troubleshooting

### Erro de conexão com banco

```bash
# Verificar se container está healthy
docker-compose ps

# Verificar logs do banco
docker-compose logs db
```

### Erro de permissão em estaticos

```bash
# Coletar estáticos novamente
docker-compose exec web python manage.py collectstatic --clear --noinput
```

### Erro 502 Bad Gateway

Verificar se a aplicação está rodando:
```bash
docker-compose logs web | tail -20
```

### Limpar cache/containers

```bash
docker system prune -a
docker volume prune
```

## Acesso à Aplicação

- **URL de Produção**: https://ebf.simoesti.com.br
- **URL de Desenvolvimento**: http://localhost:8180
- **Admin Django**: https://ebf.simoesti.com.br/admin

## Próximas Etapas

1. ✅ Criar superuser: `docker-compose exec web python manage.py createsuperuser`
2. ✅ Acessar painel admin
3. ✅ Configurar domínio no nginx-proxy-manager
4. ✅ Configurar SSL/HTTPS
5. ✅ Fazer backup de dados regularmente
6. ✅ Configurar monitoramento e logs (opcional)

## Segurança

- [ ] Mudar DEBUG para False em produção (já está no .env)
- [ ] Usar SECRET_KEY única e complexa
- [ ] Usar senha forte para PostgreSQL
- [ ] Configurar HTTPS/SSL (via nginx-proxy-manager)
- [ ] Limitar ALLOWED_HOSTS apenas aos domínios necessários
- [ ] Configurar CSRF_TRUSTED_ORIGINS se necessário
- [ ] Implementar rate limiting no nginx
