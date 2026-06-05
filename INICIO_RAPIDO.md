# 🚀 INÍCIO RÁPIDO - EBF PIBVP

## Primeira Vez - Setup Completo

```bash
# 1. Entrar na pasta do projeto
cd /Users/jonatasluisramossimoes/Documents/Jonatas/Pessoal/PIBVP/EBF/ebf_project

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Popular dados de exemplo (OPCIONAL mas recomendado!)
python manage.py shell < populate_data.py

# 4. Rodar servidor
python manage.py runserver

# 5. Abrir navegador
# http://localhost:8000
```

---

## Próximas Vezes - Setup Rápido

```bash
cd /Users/jonatasluisramossimoes/Documents/Jonatas/Pessoal/PIBVP/EBF/ebf_project
source venv/bin/activate
python manage.py runserver
```

---

## 🔐 Credenciais de Teste

Após rodar populate_data.py, use:

| Perfil | E-mail | Senha |
|--------|--------|-------|
| **Admin** | admin | admin123 |
| **Responsável** | responsavel@ebf.com | resp123 |
| **Recepção** | recepcao@ebf.com | recepcao123 |
| **Checkout** | checkout@ebf.com | checkout123 |
| **Coordenação** | coordenacao@ebf.com | coord123 |

---

## 📱 Rotas Principais

### Público
- `/` - Home (sem login)
- `/auth/login/` - Fazer login
- `/auth/register/` - Cadastrar responsável

### Responsável (após login)
- `/responsaveis/dashboard/` - Dashboard
- `/responsaveis/minhas-criancas/` - Ver crianças
- `/criancas/criar/` - Cadastrar criança

### Recepção
- `/presencas/checkin/qr/` - **Leitura QR Check-in** (câmera!)

### Checkout  
- `/presencas/checkout/qr/` - **Leitura QR Checkout** (câmera!)

### Coordenação
- `/dashboard/` - Dashboard principal
- `/dashboard/presenca-por-dia/` - Relatório
- `/dashboard/criancas-com-restricoes/` - Alergias

### Admin
- `/admin/` - Painel administrativo

---

## 🎯 Fluxo Básico de Teste

### 1. Responsável cadastra criança
```
1. Faz login: responsavel@ebf.com / resp123
2. Clica em "Cadastrar Criança"
3. Preenche dados (nome, data nasc, turma)
4. Clica em "Cadastrar"
```

### 2. Recepção faz check-in
```
1. Faz login: recepcao@ebf.com / recepcao123
2. Clica em "Abrir Leitor QR Code"
3. Escaneia QR Code da criança
4. Confirma check-in
5. Etiqueta é gerada para impressão
```

### 3. Checkout faz retirada
```
1. Faz login: checkout@ebf.com / checkout123
2. Clica em "Abrir Leitor QR Code"
3. Escaneia QR Code do RESPONSÁVEL
4. Seleciona criança(s) para retirada
5. Confirma checkout
```

### 4. Coordenação vê dashboard
```
1. Faz login: coordenacao@ebf.com / coord123
2. Vê estatísticas em tempo real
3. Acessa relatórios diversos
```

---

## 🆘 Problemas Comuns

### "Module not found" ou erros de importação
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Banco de dados vazio / sem dados
```bash
python manage.py shell < populate_data.py
```

### Porta 8000 já está em uso
```bash
python manage.py runserver 8001
# ou especificar IP
python manage.py runserver 127.0.0.1:8080
```

### Esquecer de fazer migrate
```bash
python manage.py migrate
```

---

## 📚 Documentação Completa

Veja `README.md` para documentação completa do projeto.

---

## 💡 Dicas

- **QR Codes**: São gerados automaticamente para cada criança e responsável
- **Etiquetas**: São criadas automaticamente após check-in
- **Auditoria**: Todas as ações são registradas (veja em Admin > Auditoria)
- **Bootstrap 5**: Interface responsiva em móveis e desktops
- **Admin**: Pode gerenciar tudo em /admin/ (crie mais usuários, turmas, etc)

---

## 🔧 Manutenção

### Ver logs
```bash
# Em desenvolvimento, os logs aparecem na console do runserver
python manage.py runserver
```

### Fazer backup do banco
```bash
cp db.sqlite3 db.backup.sqlite3
```

### Criar novo admin
```bash
python manage.py createsuperuser
```

### Resetar dados
```bash
rm db.sqlite3
python manage.py migrate
python manage.py shell < populate_data.py
```

---

**Pronto para usar! 🎉**

Qualquer dúvida, verifique a documentação em `README.md`.
