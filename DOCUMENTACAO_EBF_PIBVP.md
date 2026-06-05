# Documentação Principal - EBF PIBVP

## 1. Visão geral

O projeto **EBF PIBVP** é um sistema web em Django para apoiar a Escola Bíblica de Férias da Igreja Presbiteriana da Bela Vista. Ele centraliza o cadastro de responsáveis e crianças, organiza turmas, controla check-in e check-out por QR Code, gera etiquetas de identificação e disponibiliza relatórios para a coordenação.

O objetivo principal é aumentar a segurança operacional durante a EBF: somente responsáveis autorizados podem fazer entrada ou retirada, cada ação relevante fica registrada e crianças com alergias ou cuidados especiais ficam visíveis para a equipe. Os QR Codes não armazenam URLs navegáveis; eles carregam apenas chaves internas seguras.

## 2. Tecnologias utilizadas

- Python 3.9
- Django 4.2
- SQLite para ambiente local
- Bootstrap 5 para interface
- Bootstrap Icons
- qrcode para geração de QR Codes
- jsQR para leitura de QR Code pela câmera no navegador
- reportlab para geração deste PDF

## 3. Estrutura do projeto

```text
EBF/
├── ebf_project/
│   ├── accounts/        # Login, cadastro e perfil de usuário
│   ├── core/            # Home, auditoria, utilitários e permissões
│   ├── criancas/        # Cadastro e vínculo de crianças
│   ├── responsaveis/    # Dados dos responsáveis e área do responsável
│   ├── turmas/          # Turmas e professores
│   ├── presencas/       # Check-in, check-out e presença diária
│   ├── etiquetas/       # Geração/listagem de etiquetas
│   ├── dashboard/       # Relatórios e indicadores da coordenação
│   ├── config/          # Configuração principal Django
│   ├── templates/       # Todos os HTMLs do sistema
│   ├── static/          # Arquivos estáticos locais
│   ├── manage.py
│   ├── requirements.txt
│   └── populate_data.py
├── DOC/
│   └── documentacao_ebf_pibvp.pdf
├── DOCUMENTACAO_EBF_PIBVP.md
├── INICIO_RAPIDO.md
├── ESTRUTURA_PROJETO.md
└── CHECKLIST_COMPLETO.md
```

## 4. Apps e responsabilidades

### accounts

Gerencia autenticação, registro de responsáveis, login por e-mail, logout, recuperação de senha, perfil de usuário e administração de usuários staff/responsáveis. O modelo `Perfil` define o tipo de acesso do usuário. Quando o usuário também possui cadastro de responsável, a página de perfil exibe QR Code do responsável e crianças vinculadas. O cadastro de usuários exige aceite dos Termos de Uso e Política de Privacidade/LGPD.

### core

Contém a home dinâmica por perfil, página de acesso negado, decorators de permissão, contexto global do perfil logado, geração de QR Code e auditoria.

### responsaveis

Controla os dados do responsável, dashboard do responsável, lista de crianças vinculadas, detalhe da criança e edição de dados pessoais.

### criancas

Faz cadastro, edição e vínculo de responsáveis autorizados por criança. Também guarda dados sensíveis para segurança, como alergias, restrições alimentares e cuidados especiais.

Staff autorizado acessa `/criancas/buscar/` para localizar crianças por nome, código, turma, responsável, telefone ou e-mail. A tela mostra foto, turma, alertas e responsáveis autorizados para conferência operacional.

### turmas

Organiza turmas por nome, faixa etária, sala/local e professores vinculados.

A coordenação/admin gerencia turmas em `/turmas/`, com cadastro, edição e ativação/desativação. A faixa etária cadastrada nas turmas é usada para sugerir a turma automaticamente no cadastro da criança.

### presencas

Registra check-in e check-out diário, incluindo horário, operador, responsável utilizado na entrada ou retirada e observações. No check-in, a presença diária recebe um token temporário de check-out com validade. Também controla QR Codes temporários de operação em lote para check-in/check-out de múltiplas crianças com um único QR.

### etiquetas

Gera etiqueta após check-in, exibe QR Code temporário de check-out e permite marcar a etiqueta como impressa.

### dashboard

Fornece indicadores e relatórios: presença por dia, crianças por turma, crianças com restrições e histórico de entrada/saída.

## 5. Perfis de usuário

| Perfil | Permissões principais |
|---|---|
| Responsável | Cadastrar crianças, editar dados permitidos, visualizar QR Codes e status das próprias crianças. Esta capacidade existe quando o usuário possui um registro em `Responsavel` |
| Recepção | Pesquisar crianças, realizar check-in, realizar check-out e gerar/listar etiquetas |
| Check-in | Pesquisar crianças, realizar somente check-in e gerar/listar etiquetas |
| Checkout | Pesquisar crianças e registrar somente retirada/check-out |
| Coordenação | Acesso completo ao sistema, incluindo check-in, check-out, dashboard, turmas e administração de usuários |
| Professor | Pesquisar crianças para consulta operacional |
| Admin | Acesso completo ao sistema e administração pelo Django Admin |

## 6. Fluxo de cadastro

1. O responsável cria uma conta em `/auth/register/`.
2. O sistema cria automaticamente um usuário, um responsável e um perfil do tipo `Responsável`.
3. O responsável acessa `/criancas/criar/` para cadastrar uma criança.
4. É obrigatório enviar uma foto da criança em formato visual 3x4, usada para conferência de entrada e saída.
5. As fotos ficam organizadas em `media/criancas/fotos/<id-da-crianca>/nome-do-arquivo`.
6. A turma não é escolhida manualmente; o sistema usa a data de nascimento para procurar uma turma ativa com faixa etária compatível.
7. A criança recebe um código interno, token QR e vínculo com o responsável principal.
8. Outro login pode apontar para a mesma criança quando o outro adulto também possui cadastro de responsável e é vinculado em `/criancas/<id>/adicionar-responsavel/`. A tela não lista usuários do sistema; o vínculo é feito por e-mail, telefone ou documento do responsável.
9. No detalhe da criança, o responsável principal visualiza todos os responsáveis ativos, pode alterar permissões e pode revogar acessos.

## 6.1. Gestão de responsáveis da criança

Cada criança pode ter múltiplos responsáveis vinculados por `CriancaResponsavel`. O vínculo guarda:

- parentesco;
- permissão de check-in;
- permissão de check-out;
- permissão de editar dados;
- indicação de responsável principal;
- status ativo/revogado.

O responsável principal pode gerenciar os vínculos na tela de detalhe da criança. Revogar acesso não apaga o registro; apenas marca o vínculo como inativo e remove os direitos operacionais, preservando histórico e auditoria.

O sistema impede revogar ou desativar o único responsável principal ativo da criança. Antes disso, outro responsável precisa ser definido como principal.

O parentesco usa opções fixas, como Pai, Mãe, Tio, Tia, Avô, Avó e Tutor legal, evitando variações de digitação.

## 6.2. Fluxo de staff

O cadastro de pais/responsáveis é separado do cadastro de staff. A coordenação acessa `/auth/staff/register/` para criar usuários operacionais.

No cadastro de staff é possível marcar que a pessoa também é responsável por criança. Nesse caso, o mesmo usuário recebe:

- um `Perfil` operacional, como Recepção, Check-in, Checkout ou Coordenação;
- um registro em `Responsavel`, permitindo acessar crianças vinculadas e cadastrar filhos.

Na prática, a pessoa troca de contexto pelos atalhos da interface: ferramentas operacionais aparecem pelo perfil de staff, e as crianças aparecem quando o usuário também tem cadastro de responsável.

Qualquer usuário logado, independente do cargo, também pode ativar sua área de responsável em `/responsaveis/ativar/`. Isso permite que recepção, check-in, checkout, professor, coordenação ou admin tenham crianças associadas sem trocar o perfil operacional.

## 6.3. Administração de usuários

A coordenação/admin possui duas telas separadas para visualizar cadastros:

- `/auth/staff/` lista usuários operacionais, com busca por nome, e-mail, função, telefone ou documento. A lista mostra status, último acesso e se o staff também tem cadastro de responsável. A função operacional pode ser alterada diretamente nessa tela.
- `/auth/responsaveis/` lista responsáveis cadastrados, com busca por nome, e-mail, telefone ou documento. A lista mostra contato, quantidade de crianças vinculadas, status, autorização de imagem e quando o responsável também possui perfil operacional.

As duas telas são paginadas e restritas a usuários com perfil `Coordenação` ou `Admin`.

## 7. Fluxo de check-in

1. A recepção, check-in, coordenação ou admin acessa `/presencas/checkin/qr/`.
2. O QR Code da criança ou do responsável é escaneado. O QR contém somente uma chave interna, sem URL.
3. Se for QR de criança, o check-in individual é feito.
4. Se for QR de responsável, o sistema lista as crianças autorizadas para entrada.
5. A presença diária recebe status `PRESENTE`.
6. A etiqueta é criada automaticamente com um QR Code temporário de check-out e pode ser impressa.

### 7.1. Check-in em lote com QR temporário

O responsável acessa `/responsaveis/qrcode/checkin/`, seleciona uma ou mais crianças autorizadas para entrada e gera um único QR Code temporário. Esse QR contém apenas uma chave interna `EBF:CHECKIN_LOTE:<token>`, sem URL, expira em 30 minutos e é marcado como usado após a confirmação pela equipe autorizada para check-in.

## 8. Fluxo de check-out

1. A recepção, checkout, coordenação ou admin acessa `/presencas/checkout/qr/`.
2. A equipe pode escanear o QR Code do responsável ou o QR Code temporário impresso na etiqueta da criança.
3. Se o QR for do responsável, o sistema lista apenas crianças presentes e autorizadas para aquele responsável.
4. Se o QR for temporário da etiqueta, o sistema localiza a presença do dia, valida a expiração e exige a escolha de um responsável autorizado para retirada.
5. A equipe confirma a retirada.
6. A presença recebe status `RETIRADA`, horário de saída e responsável de retirada.

### 8.1. Check-out em lote com QR temporário

O responsável acessa `/responsaveis/qrcode/checkout/`, seleciona uma ou mais crianças presentes e autorizadas para retirada e gera um único QR Code temporário. Esse QR contém apenas uma chave interna `EBF:CHECKOUT_LOTE:<token>`, sem URL, expira em 30 minutos e é marcado como usado após a confirmação pela equipe autorizada para check-out.

## 9. Rotas principais

### Autenticação

- `/auth/login/` - Login
- `/auth/register/` - Cadastro de responsável
- `/auth/staff/` - Administração de usuários staff
- `/auth/staff/register/` - Cadastro de staff pela coordenação
- `/auth/responsaveis/` - Administração de usuários responsáveis
- `/auth/senha/esqueci/` - Solicitar link de redefinição de senha
- `/auth/senha/esqueci/done/` - Confirmação de envio do link
- `/auth/senha/redefinir/<uidb64>/<token>/` - Criar nova senha a partir do link
- `/auth/senha/redefinir/concluido/` - Confirmação de senha redefinida
- `/auth/logout/` - Logout
- `/auth/profile/` - Perfil do usuário
- `/auth/profile/edit/` - Edição do perfil
- `/termos-de-uso/` - Termos de Uso e Política de Privacidade/LGPD

### Responsáveis e crianças

- `/criancas/buscar/` - Pesquisa operacional de crianças para staff
- `/criancas/<id>/staff/` - Detalhe operacional da criança para staff
- `/responsaveis/dashboard/` - Dashboard do responsável
- `/responsaveis/ativar/` - Ativar área de responsável para qualquer usuário logado
- `/responsaveis/qrcode/checkin/` - Gerar QR temporário de check-in em lote
- `/responsaveis/qrcode/checkout/` - Gerar QR temporário de check-out em lote
- `/responsaveis/minhas-criancas/` - Crianças vinculadas
- `/responsaveis/crianca/<id>/` - Detalhe da criança
- `/responsaveis/editar-perfil/` - Dados do responsável
- `/criancas/criar/` - Cadastro de criança
- `/criancas/<id>/editar/` - Edição da criança
- `/criancas/<id>/adicionar-responsavel/` - Vínculo de responsável autorizado
- `/criancas/responsavel/<vinculo_id>/editar/` - Alterar permissões de um responsável vinculado
- `/criancas/responsavel/<vinculo_id>/revogar/` - Revogar acesso de um responsável vinculado

### Presenças e etiquetas

- `/presencas/checkin/qr/` - Leitor QR de check-in
- `/presencas/checkin/crianca/<id>/` - Check-in individual
- `/presencas/checkin/responsavel/<id>/` - Check-in em lote
- `/presencas/checkin/lote/<id>/` - Confirmação de check-in por QR temporário em lote
- `/presencas/checkout/qr/` - Leitor QR de check-out
- `/presencas/checkout/responsavel/<id>/` - Retirada por responsável
- `/presencas/checkout/lote/<id>/` - Confirmação de check-out por QR temporário em lote
- `/etiquetas/gerar/<presenca_id>/` - Gerar/visualizar etiqueta
- `/etiquetas/listar-dia/` - Etiquetas do dia

### Coordenação

- `/dashboard/` - Dashboard geral
- `/dashboard/presenca-por-dia/` - Relatório por data
- `/dashboard/criancas-por-turma/` - Crianças por turma
- `/dashboard/criancas-com-restricoes/` - Restrições e cuidados especiais
- `/dashboard/historico-checkin-checkout/` - Histórico de entradas e saídas
- `/turmas/` - Listar turmas
- `/turmas/criar/` - Cadastrar turma
- `/turmas/<id>/editar/` - Editar turma
- `/turmas/<id>/alternar/` - Ativar/desativar turma

## 10. Instalação local

```bash
cd /Users/jonatasluisramossimoes/Documents/Jonatas/Pessoal/PIBVP/EBF/ebf_project
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py shell < populate_data.py
python manage.py runserver
```

Acesse em:

```text
http://localhost:8000
```

## 11. Credenciais de teste

Quando `populate_data.py` é executado, os usuários de teste ficam disponíveis:

| Perfil | Usuário/e-mail | Senha |
|---|---|---|
| Admin | admin | admin123 |
| Recepção | recepcao@ebf.com | recepcao123 |
| Check-in | criar pela tela de staff | definir no cadastro |
| Checkout | checkout@ebf.com | checkout123 |
| Coordenação | coordenacao@ebf.com | coord123 |
| Responsável | responsavel@ebf.com | resp123 |

## 12. Segurança e auditoria

- Login obrigatório nas áreas internas.
- Cadastro de responsável e cadastro de staff exigem aceite dos Termos de Uso e Política de Privacidade/LGPD.
- Administração de usuários staff e responsáveis restrita à coordenação/admin.
- Login possui link "Esqueci a senha" e botão para visualizar/ocultar senha.
- Redefinição de senha usa tokens temporários do Django enviados por e-mail.
- Em ambiente local, o backend de e-mail padrão imprime o link no console.
- Permissões por perfil usando decorators.
- QR Codes usam tokens aleatórios, sem dados pessoais expostos.
- QR Codes carregam apenas chaves internas como `EBF:RESP:<token>`, `EBF:CRI:<token>`, `EBF:CHECKOUT:<token>`, `EBF:CHECKIN_LOTE:<token>` ou `EBF:CHECKOUT_LOTE:<token>`, sem link/URL.
- QR de checkout da etiqueta é temporário, gerado no check-in e validado por presença/status/expiração.
- QR de operação em lote expira em 30 minutos e é invalidado após o uso.
- Responsáveis só acessam crianças vinculadas a eles.
- Check-out só aparece para crianças presentes e responsáveis autorizados.
- Ações importantes registram auditoria no banco.
- Proteção CSRF nos formulários.

## 13. HTMLs criados no projeto

Todos os templates referenciados pelas views estão presentes:

- `accounts/login.html`
- `accounts/register.html`
- `accounts/listar_staff.html`
- `accounts/listar_responsaveis.html`
- `includes/paginacao.html`
- `accounts/password_reset_form.html`
- `accounts/password_reset_done.html`
- `accounts/password_reset_confirm.html`
- `accounts/password_reset_complete.html`
- `accounts/password_reset_email.html`
- `accounts/password_reset_subject.txt`
- `accounts/profile.html`
- `accounts/perfil_form.html`
- `core/home.html`
- `core/access_denied.html`
- `core/termos_uso.html`
- `responsaveis/dashboard.html`
- `responsaveis/gerar_qr_lote.html`
- `responsaveis/minhas_criancas.html`
- `responsaveis/detalhe_crianca.html`
- `responsaveis/editar_perfil.html`
- `criancas/criar_crianca.html`
- `criancas/editar_crianca.html`
- `criancas/adicionar_responsavel.html`
- `presencas/leitura_qr_checkin.html`
- `presencas/checkin_responsavel.html`
- `presencas/checkin_lote.html`
- `presencas/leitura_qr_checkout.html`
- `presencas/checkout_responsavel.html`
- `presencas/checkout_lote.html`
- `etiquetas/gerar_etiqueta.html`
- `etiquetas/listar_etiquetas_dia.html`
- `dashboard/dashboard.html`
- `dashboard/presenca_por_dia.html`
- `dashboard/criancas_por_turma.html`
- `dashboard/criancas_com_restricoes.html`
- `dashboard/historico_checkin_checkout.html`

## 14. Melhorias aplicadas nesta revisão

- Criação dos templates faltantes.
- Melhoria visual no layout base, navegação por perfil, cards, estados vazios e botões.
- Separação do cadastro de staff do cadastro de responsáveis.
- Permissão de responsável baseada no registro `Responsavel`, permitindo staff também ser responsável.
- Cadastro de criança sem escolha manual de turma, com sugestão automática por idade.
- Tela de detalhe da criança agora mostra responsáveis vinculados, permissões, edição de direitos e revogação de acesso.
- Correção do uso do campo `Perfil.usuario` no cadastro e na criação automática de perfil.
- Validação com `python manage.py check`.
- Geração desta documentação principal em Markdown e PDF.

## 15. Próximos passos recomendados

- Criar testes automatizados para os fluxos de cadastro, check-in e check-out.
- Implementar telas específicas para professores por turma.
- Trocar SQLite por PostgreSQL em produção.
- Configurar armazenamento de estáticos e mídia para deploy.
- Revisar LGPD e política de retenção de dados antes de uso real.
