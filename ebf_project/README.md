# EBF PIBVP - Sistema de Controle de Crianças

Sistema Django para controlar o cadastro, presença e saída de crianças na Escola Bíblica de Férias (EBF) da Igreja Presbiteriana da Bela Vista (PIBVP).

## 📋 Funcionalidades

### Gerenciamento
- ✅ Cadastro de crianças com dados pessoais, alergias, restrições alimentares e cuidados especiais
- ✅ Cadastro de responsáveis com autorizações específicas (check-in, checkout, edição)
- ✅ Cadastro de turmas e professores
- ✅ Autorizações granulares de quem pode fazer o quê

### Presença
- ✅ Check-in via QR Code (individual ou em lote)
- ✅ Check-out seguro com registro de responsável que retirou
- ✅ Geração automática de etiquetas após check-in
- ✅ Histórico completo de presença e saída

### Relatórios
- ✅ Dashboard com estatísticas em tempo real
- ✅ Presença por dia
- ✅ Crianças por turma
- ✅ Crianças com alergias/restrições
- ✅ Histórico de check-in/checkout

### Perfis de Usuário
- **Responsável**: Cadastra crianças, visualiza status, QR Codes próprio
- **Recepção**: Realiza check-in de crianças
- **Professor**: Visualiza dados das turmas
- **Checkout**: Autoriza saída de crianças
- **Coordenação**: Acessa todos os relatórios e dashboard
- **Admin**: Acesso completo ao sistema

## 🚀 Instalação

### 1. Clone o repositório
```bash
cd /Users/jonatasluisramossimoes/Documents/Jonatas/Pessoal/PIBVP/EBF/ebf_project
```

### 2. Ative o ambiente virtual
```bash
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute as migrações
```bash
python manage.py migrate
```

### 5. Crie um superusuário (opcional, se não usar populate)
```bash
python manage.py createsuperuser
```

### 6. Popular dados de exemplo (opcional)
```bash
python manage.py shell < populate_data.py
```

### 7. Inicie o servidor
```bash
python manage.py runserver
```

Acesse em: http://localhost:8000

## 📱 Credenciais de Teste

Se usou o script populate_data.py:

| Perfil | E-mail | Senha |
|--------|--------|-------|
| Admin | admin | admin123 |
| Recepção | recepcao@ebf.com | recepcao123 |
| Checkout | checkout@ebf.com | checkout123 |
| Coordenação | coordenacao@ebf.com | coord123 |
| Responsável | responsavel@ebf.com | resp123 |

## 📁 Estrutura do Projeto

```
ebf_project/
├── config/                 # Configuração principal do Django
├── templates/              # Templates HTML globais
│   ├── base.html
│   ├── core/
│   ├── accounts/
│   ├── responsaveis/
│   ├── criancas/
│   ├── presencas/
│   ├── etiquetas/
│   └── dashboard/
├── accounts/              # Autenticação e perfis de usuário
│   ├── models.py         # Modelo Perfil
│   ├── views.py          # Login, register, profile
│   ├── forms.py
│   └── urls.py
├── core/                  # App auxiliar
│   ├── models.py         # Modelos base e auditoria
│   ├── utils.py          # Funções utilitárias (QR code, auditoria)
│   ├── decorators.py     # Decorators de permissão
│   └── views.py
├── responsaveis/         # Gerenciamento de responsáveis
│   ├── models.py         # Modelo Responsavel
│   ├── views.py
│   └── forms.py
├── criancas/             # Gerenciamento de crianças
│   ├── models.py         # Modelos Crianca, CriancaResponsavel
│   ├── views.py
│   └── forms.py
├── turmas/               # Gerenciamento de turmas
│   ├── models.py         # Modelos Turma, Professor
│   └── admin.py
├── presencas/            # Controle de presença
│   ├── models.py         # Modelo PresencaDiaria
│   ├── views.py          # Check-in, checkout
│   └── forms.py
├── etiquetas/            # Geração de etiquetas
│   ├── models.py         # Modelo Etiqueta
│   └── views.py
├── dashboard/            # Relatórios e estatísticas
│   └── views.py
├── static/               # CSS, JS, imagens
└── requirements.txt      # Dependências
```

## 🔐 Modelos de Dados

### Perfil (User Profile)
- Usuario (FK: User)
- Tipo de perfil (responsavel, recepcao, professor, checkout, coordenacao, admin)

### Responsavel
- Usuario (OneToOne: User)
- Nome completo
- Telefone
- Documento (CPF)
- Token QR Code único
- Autorização de imagem

### Crianca
- Nome completo
- Data de nascimento (calcula idade automaticamente)
- Turma (FK)
- Alergias, restrições alimentares, cuidados especiais
- Autorização de imagem
- Código interno (EBF-000001, etc)
- Token QR Code único

### CriancaResponsavel (Many-to-Many through)
- Criança
- Responsável
- Parentesco
- Permissões: pode_fazer_checkin, pode_fazer_checkout, pode_editar_dados
- Responsável principal: Sim/Não

### Turma
- Nome
- Faixa etária
- Sala/Local
- Professores (M2M)

### Professor
- Usuario (OneToOne: User)
- Nome
- Telefone
- Função
- Turmas vinculadas (M2M)

### PresencaDiaria
- Criança (FK)
- Data (unique_together: criança + data)
- Status: NAO_CHEGOU, PRESENTE, RETIRADA, AUSENTE
- Check-in: horário, usuário, responsável
- Check-out: horário, usuário, responsável
- Observações

### Etiqueta
- Presença (OneToOne)
- Criança (FK)
- Data de geração
- Usuário que gerou
- Impressa: Sim/Não

### Auditoria (log de ações)
- Usuário
- Ação (CRIAR, ATUALIZAR, DELETAR, CHECKIN, CHECKOUT)
- Modelo e ID do objeto
- Descrição
- IP Address
- Data/Hora

## 🔗 URLs Principais

### Autenticação
- `/auth/login/` - Login
- `/auth/register/` - Registro de responsável
- `/auth/logout/` - Logout
- `/auth/profile/` - Visualizar perfil

### Responsável
- `/responsaveis/dashboard/` - Dashboard do responsável
- `/responsaveis/minhas-criancas/` - Lista de crianças
- `/responsaveis/crianca/<id>/` - Detalhe da criança (com QR Code)
- `/criancas/criar/` - Criar criança
- `/criancas/<id>/editar/` - Editar criança

### Recepção (Check-in)
- `/presencas/checkin/qr/` - Leitor de QR Code
- `/presencas/checkin/crianca/<id>/` - Check-in individual
- `/presencas/checkin/responsavel/<id>/` - Check-in em lote
- `/etiquetas/listar-dia/` - Listar etiquetas do dia

### Checkout
- `/presencas/checkout/qr/` - Leitor de QR Code para checkout
- `/presencas/checkout/responsavel/<id>/` - Checkout em lote

### Coordenação
- `/dashboard/` - Dashboard principal
- `/dashboard/presenca-por-dia/` - Relatório de presença
- `/dashboard/criancas-por-turma/` - Crianças por turma
- `/dashboard/criancas-com-restricoes/` - Alergias e restrições
- `/dashboard/historico-checkin-checkout/` - Histórico

### Admin
- `/admin/` - Painel administrativo

## 🛡️ Segurança

- ✅ Login obrigatório para áreas administrativas
- ✅ Verificação de permissões baseada em decorators
- ✅ Tokens únicos e aleatórios para QR Codes (não contêm dados pessoais)
- ✅ Registro de auditoria de todas as ações importantes
- ✅ Responsáveis só veem seus dados e crianças
- ✅ Professores só veem dados das suas turmas
- ✅ Separação clara de permissões por perfil

## 📊 Fluxo de Check-in

1. **Recepção** escaneie o QR Code
2. Se for **criança individual**: registra presença imediatamente
3. Se for **responsável**: exibe lista de crianças que pode fazer check-in
4. **Seleciona** uma ou mais crianças
5. Sistema registra **presença individualmente**
6. **Gera etiqueta automaticamente** para cada criança
7. Etiqueta é **exibida para impressão**

## 📊 Fluxo de Check-out

1. **Checkout** escaneie o QR Code do responsável
2. Sistema verifica:
   - Crianças presentes naquela criança
   - Responsável está autorizado a retirar
   - Nenhuma já foi retirada
3. **Seleciona** crianças para retirada
4. Sistema registra:
   - Horário de saída
   - Responsável que retirou
   - Usuário da equipe que liberou
5. Status muda para **RETIRADA**

## 📝 Etiqueta

A etiqueta gerada após check-in contém:
- Logo/Nome: "EBF PIBVP"
- Nome da criança
- Turma
- Código interno (EBF-000001)
- QR Code da criança
- Aviso discreto se houver alergias ou observações importantes

## 🚀 Deploy

Para fazer deploy em produção:

1. Configure variáveis de ambiente em `.env`:
   ```
   SECRET_KEY=sua-chave-segura
   DEBUG=False
   ALLOWED_HOSTS=seu-dominio.com
   DATABASE_URL=sua-url-banco-dados
   ```

2. Use um banco de dados robusto (PostgreSQL recomendado):
   ```bash
   pip install psycopg2
   ```

3. Configure um servidor web (Gunicorn + Nginx recomendado):
   ```bash
   pip install gunicorn
   gunicorn config.wsgi:application
   ```

4. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

## 📚 Tecnologias Usadas

- **Django 4.2** - Framework web
- **Bootstrap 5** - UI Framework
- **QRCode** - Geração de QR Codes
- **SQLite** (dev) / PostgreSQL (prod) - Banco de dados

## 🤝 Contribuindo

Para contribuir com melhorias:

1. Crie uma branch para sua feature
2. Faça commit das mudanças
3. Envie um pull request

## 📞 Suporte

Para dúvidas ou problemas, entre em contato com a coordenação da EBF.

## 📄 Licença

Este projeto está sob licença propriedária da PIBVP.

---

**Última atualização:** Junho 2024
