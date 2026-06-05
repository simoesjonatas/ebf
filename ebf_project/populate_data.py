"""
Script para popular dados de exemplo no banco de dados.
Execute com: python manage.py shell < populate_data.py
"""

from django.contrib.auth.models import User
from accounts.models import Perfil
from responsaveis.models import Responsavel
from turmas.models import Turma, Professor
from criancas.models import Crianca, CriancaResponsavel
from datetime import date, timedelta
import uuid

def criar_usuarios_e_perfis():
    """Cria usuários e seus perfis"""
    
    # Criar admin
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@ebf.com', 'admin123')
        Perfil.objects.create(usuario=admin, tipo_perfil='admin')
        print("✓ Usuário admin criado")
    
    # Criar recepção
    if not User.objects.filter(username='recepcao@ebf.com').exists():
        recepcao = User.objects.create_user('recepcao@ebf.com', 'recepcao@ebf.com', 'recepcao123')
        recepcao.first_name = 'Maria'
        recepcao.last_name = 'Silva'
        recepcao.save()
        Perfil.objects.create(usuario=recepcao, tipo_perfil='recepcao')
        print("✓ Usuário recepção criado")
    
    # Criar checkout
    if not User.objects.filter(username='checkout@ebf.com').exists():
        checkout = User.objects.create_user('checkout@ebf.com', 'checkout@ebf.com', 'checkout123')
        checkout.first_name = 'João'
        checkout.last_name = 'Santos'
        checkout.save()
        Perfil.objects.create(usuario=checkout, tipo_perfil='checkout')
        print("✓ Usuário checkout criado")
    
    # Criar coordenação
    if not User.objects.filter(username='coordenacao@ebf.com').exists():
        coordenacao = User.objects.create_user('coordenacao@ebf.com', 'coordenacao@ebf.com', 'coord123')
        coordenacao.first_name = 'Ana'
        coordenacao.last_name = 'Coordenadora'
        coordenacao.save()
        Perfil.objects.create(usuario=coordenacao, tipo_perfil='coordenacao')
        print("✓ Usuário coordenação criado")
    
    # Criar responsável
    if not User.objects.filter(username='responsavel@ebf.com').exists():
        resp_user = User.objects.create_user('responsavel@ebf.com', 'responsavel@ebf.com', 'resp123')
        resp_user.first_name = 'Carlos'
        resp_user.last_name = 'Responsável'
        resp_user.save()
        Responsavel.objects.create(
            usuario=resp_user,
            nome_completo='Carlos Responsável',
            telefone='(11) 98765-4321',
            autorizacao_imagem=True,
            token_qr=str(uuid.uuid4())
        )
        Perfil.objects.create(usuario=resp_user, tipo_perfil='responsavel')
        print("✓ Usuário responsável criado")

def criar_turmas():
    """Cria turmas"""
    turmas_data = [
        {'nome': 'Berçário', 'faixa_etaria': '0-2 anos', 'sala_local': 'Sala 101'},
        {'nome': 'Mini', 'faixa_etaria': '2-3 anos', 'sala_local': 'Sala 102'},
        {'nome': 'Pré-escolar', 'faixa_etaria': '3-4 anos', 'sala_local': 'Sala 103'},
        {'nome': 'Maternal', 'faixa_etaria': '4-5 anos', 'sala_local': 'Sala 104'},
    ]
    
    for turma_data in turmas_data:
        if not Turma.objects.filter(nome=turma_data['nome']).exists():
            Turma.objects.create(**turma_data)
            print(f"✓ Turma '{turma_data['nome']}' criada")

def criar_criancas():
    """Cria crianças de exemplo"""
    try:
        responsavel = Responsavel.objects.get(usuario__email='responsavel@ebf.com')
    except Responsavel.DoesNotExist:
        print("✗ Responsável não encontrado")
        return
    
    turma = Turma.objects.first()
    
    criancas_data = [
        {'nome_completo': 'Maria Silva', 'data_nascimento': date(2022, 3, 15), 'alergias': 'Amendoim', 'cuidados_especiais': ''},
        {'nome_completo': 'João Silva', 'data_nascimento': date(2022, 7, 22), 'alergias': '', 'cuidados_especiais': 'Asma leve'},
    ]
    
    for crianca_data in criancas_data:
        if not Crianca.objects.filter(nome_completo=crianca_data['nome_completo']).exists():
            crianca = Crianca.objects.create(
                nome_completo=crianca_data['nome_completo'],
                data_nascimento=crianca_data['data_nascimento'],
                turma=turma,
                alergias=crianca_data['alergias'],
                cuidados_especiais=crianca_data['cuidados_especiais'],
                autorizacao_imagem=True,
                token_qr=str(uuid.uuid4()),
            )
            
            CriancaResponsavel.objects.create(
                crianca=crianca,
                responsavel=responsavel,
                parentesco='Pai',
                pode_fazer_checkin=True,
                pode_fazer_checkout=True,
                responsavel_principal=True,
                ativo=True
            )
            
            print(f"✓ Criança '{crianca_data['nome_completo']}' criada")

# comentar para rodar
if __name__ == '__main__':
    # Executa as funções de criação de dados
    print("\n=== Populando banco de dados ===\n")
    criar_usuarios_e_perfis()
    criar_turmas()
    criar_criancas()
    print("\n=== Concluído! ===\n")
    print("Credenciais padrão:")
    print("- Admin: admin / admin123")
    print("- Recepção: recepcao@ebf.com / recepcao123")
    print("- Checkout: checkout@ebf.com / checkout123")
    print("- Coordenação: coordenacao@ebf.com / coord123")
    print("- Responsável: responsavel@ebf.com / resp123")
