from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from datetime import date
from core.decorators import coordenacao_requerida
from core.utils import generate_qr_code, get_qr_payload
from .forms import (
    ResponsavelRegisterForm, StaffRegisterForm, StaffRoleForm, StyledPasswordChangeForm,
    UserLoginForm, PerfilForm, STAFF_PROFILE_CHOICES,
)
from .models import Perfil
from responsaveis.models import Responsavel
from criancas.models import Crianca
from presencas.models import PresencaDiaria


STAFF_PROFILE_TYPES = ['recepcao', 'checkin', 'professor', 'checkout', 'coordenacao', 'admin']

# Opções de função para promover/rebaixar um responsável (inclui voltar a "só responsável")
FUNCAO_CHOICES = [('responsavel', 'Somente responsável')] + STAFF_PROFILE_CHOICES
FUNCAO_VALIDAS = {valor for valor, _ in FUNCAO_CHOICES}


def register_responsavel(request):
    """Registro de responsável"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ResponsavelRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ResponsavelRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@coordenacao_requerida
def register_staff(request):
    """Cadastro separado de staff operacional."""
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Staff {user.get_full_name() or user.email} cadastrado com sucesso.')
            return redirect('accounts:profile')
    else:
        form = StaffRegisterForm()

    return render(request, 'accounts/staff_register.html', {'form': form})


@coordenacao_requerida
def listar_staff(request):
    """Administração de usuários operacionais."""
    termo = request.GET.get('q', '').strip()
    pagina = request.GET.get('page', 1)

    perfis = (
        Perfil.objects
        .filter(tipo_perfil__in=STAFF_PROFILE_TYPES)
        .select_related('usuario', 'usuario__responsavel')
        .annotate(total_criancas=Count(
            'usuario__responsavel__crianca_responsavel',
            filter=Q(usuario__responsavel__crianca_responsavel__ativo=True),
            distinct=True
        ))
        .order_by('tipo_perfil', 'usuario__first_name', 'usuario__email')
    )

    if termo:
        perfis = perfis.filter(
            Q(usuario__first_name__icontains=termo)
            | Q(usuario__last_name__icontains=termo)
            | Q(usuario__email__icontains=termo)
            | Q(usuario__username__icontains=termo)
            | Q(tipo_perfil__icontains=termo)
            | Q(usuario__responsavel__nome_completo__icontains=termo)
            | Q(usuario__responsavel__telefone__icontains=termo)
            | Q(usuario__responsavel__documento__icontains=termo)
        )

    paginator = Paginator(perfis, 25)
    page_obj = paginator.get_page(pagina)

    return render(request, 'accounts/listar_staff.html', {
        'termo': termo,
        'perfis': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'staff_profile_types': STAFF_PROFILE_TYPES,
    })


@coordenacao_requerida
@require_http_methods(["POST"])
def alterar_funcao_staff(request, perfil_id):
    """Alterar a função operacional de um usuário staff."""
    perfil = Perfil.objects.select_related('usuario').filter(
        id=perfil_id,
        tipo_perfil__in=STAFF_PROFILE_TYPES
    ).first()

    if not perfil:
        messages.error(request, 'Usuário staff não encontrado.')
        return redirect('accounts:staff_list')

    funcao_anterior = perfil.get_tipo_perfil_display()
    form = StaffRoleForm(request.POST, instance=perfil)
    if form.is_valid():
        atualizado = form.save(commit=False)
        removendo_o_proprio_acesso = (
            perfil.usuario_id == request.user.id
            and atualizado.tipo_perfil not in ['coordenacao', 'admin']
        )
        if removendo_o_proprio_acesso:
            messages.error(request, 'Peça para outro coordenador/admin alterar sua função para evitar perder o acesso.')
        else:
            atualizado.save()
            messages.success(
                request,
                f'Função de {perfil.usuario.get_full_name() or perfil.usuario.email} alterada de {funcao_anterior} para {atualizado.get_tipo_perfil_display()}.'
            )
    else:
        messages.error(request, 'Função inválida. Selecione uma função operacional.')

    querystring = request.GET.urlencode()
    destino = reverse('accounts:staff_list')
    if querystring:
        destino = f'{destino}?{querystring}'
    return redirect(destino)


@coordenacao_requerida
def listar_responsaveis(request):
    """Administração de usuários responsáveis."""
    termo = request.GET.get('q', '').strip()
    pagina = request.GET.get('page', 1)

    responsaveis = (
        Responsavel.objects
        .select_related('usuario', 'usuario__perfil')
        .annotate(total_criancas=Count(
            'crianca_responsavel',
            filter=Q(crianca_responsavel__ativo=True),
            distinct=True
        ))
        .order_by('nome_completo')
    )

    if termo:
        responsaveis = responsaveis.filter(
            Q(nome_completo__icontains=termo)
            | Q(usuario__first_name__icontains=termo)
            | Q(usuario__last_name__icontains=termo)
            | Q(usuario__email__icontains=termo)
            | Q(usuario__username__icontains=termo)
            | Q(telefone__icontains=termo)
            | Q(documento__icontains=termo)
        )

    paginator = Paginator(responsaveis, 25)
    page_obj = paginator.get_page(pagina)

    return render(request, 'accounts/listar_responsaveis.html', {
        'termo': termo,
        'responsaveis': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'funcao_choices': FUNCAO_CHOICES,
    })


@coordenacao_requerida
@require_http_methods(["POST"])
def alterar_perfil_responsavel(request, perfil_id):
    """Promove um responsável a staff (ou volta para 'somente responsável'),
    alterando o tipo_perfil. O vínculo de responsável é mantido."""
    perfil = Perfil.objects.select_related('usuario').filter(id=perfil_id).first()
    if not perfil:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('accounts:responsaveis_list')

    novo = request.POST.get('tipo_perfil', '')
    if novo not in FUNCAO_VALIDAS:
        messages.error(request, 'Função inválida.')
    elif perfil.usuario_id == request.user.id and novo not in ['coordenacao', 'admin']:
        messages.error(request, 'Você não pode rebaixar a sua própria conta. Peça a outro coordenador/admin.')
    else:
        anterior = perfil.get_tipo_perfil_display()
        perfil.tipo_perfil = novo
        perfil.save()
        nome = perfil.usuario.get_full_name() or perfil.usuario.email
        messages.success(request, f'{nome}: função alterada de {anterior} para {perfil.get_tipo_perfil_display()}.')

    querystring = request.GET.urlencode()
    destino = reverse('accounts:responsaveis_list')
    return redirect(f'{destino}?{querystring}' if querystring else destino)


def login_view(request):
    """Login de usuários"""
    if request.user.is_authenticated:
        return redirect('core:home')
    login_error = None
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Busca case-insensitive: o formulário já normalizou para lowercase,
            # e o iexact também encontra contas antigas gravadas com case misto.
            user = User.objects.filter(email__iexact=email).first()
            if user is not None:
                user_auth = authenticate(request, username=user.username, password=password)
                if user_auth is not None:
                    login(request, user_auth)
                    messages.success(request, f'Bem-vindo, {user.first_name}!')
                    return redirect('core:home')

            login_error = 'E-mail ou senha incorretos. Confira os dados e tente novamente.'
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'login_error': login_error})


def logout_view(request):
    """Logout de usuários"""
    logout(request)
    messages.success(request, 'Você foi desconectado.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Visualizar perfil do usuário"""
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(usuario=request.user, tipo_perfil='responsavel')

    context = {'perfil': perfil}

    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        responsavel = None

    if responsavel and responsavel.ativo:
        criancas = (
            Crianca.objects
            .filter(crianca_responsavel__responsavel=responsavel, crianca_responsavel__ativo=True)
            .select_related('turma')
            .distinct()
            .order_by('nome_completo')
        )
        presencas_hoje = {
            presenca.crianca_id: presenca
            for presenca in PresencaDiaria.objects.filter(crianca__in=criancas, data=date.today())
        }
        criancas_info = []
        for crianca in criancas:
            presenca = presencas_hoje.get(crianca.id)
            criancas_info.append({
                'crianca': crianca,
                'presenca': presenca,
                'status': presenca.get_status_display() if presenca else 'Não marcada',
            })

        context.update({
            'responsavel': responsavel,
            'qr_code_responsavel': generate_qr_code(get_qr_payload('responsavel', responsavel.token_qr)),
            'criancas_info': criancas_info,
        })

    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def perfil_edit_view(request):
    """Editar perfil"""
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(usuario=request.user, tipo_perfil='responsavel')

    if perfil.tipo_perfil not in ['coordenacao', 'admin']:
        messages.error(request, 'Apenas coordenação ou admin podem alterar perfil operacional.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, 'accounts/perfil_form.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def alterar_senha_view(request):
    """Permite que o próprio usuário troque sua senha a partir do perfil."""
    if request.method == 'POST':
        form = StyledPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # evita deslogar o usuário
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('accounts:profile')
    else:
        form = StyledPasswordChangeForm(user=request.user)

    return render(request, 'accounts/alterar_senha.html', {'form': form})
