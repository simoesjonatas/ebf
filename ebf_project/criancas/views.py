from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.decorators import responsavel_requerido, perfil_requerido
from core.utils import registrar_auditoria
from .models import Crianca, CriancaResponsavel
from .forms import CriancaForm, CriancaResponsavelForm, CriancaResponsavelPermissoesForm
from responsaveis.models import Responsavel
from datetime import date


def _usuario_pode_gerenciar_responsaveis(user, crianca):
    try:
        responsavel = user.responsavel
    except Responsavel.DoesNotExist:
        return False

    return CriancaResponsavel.objects.filter(
        crianca=crianca,
        responsavel=responsavel,
        responsavel_principal=True,
        ativo=True
    ).exists()


@perfil_requerido(['recepcao', 'checkin', 'checkout', 'professor', 'coordenacao', 'admin'])
def buscar_criancas(request):
    termo = request.GET.get('q', '').strip()
    pagina = request.GET.get('page', 1)
    criancas = Crianca.objects.none()

    if termo:
        criancas = (
            Crianca.objects
            .filter(ativa=True)
            .filter(
                Q(nome_completo__icontains=termo)
                | Q(codigo_interno__icontains=termo)
                | Q(turma__nome__icontains=termo)
                | Q(crianca_responsavel__responsavel__nome_completo__icontains=termo)
                | Q(crianca_responsavel__responsavel__telefone__icontains=termo)
                | Q(crianca_responsavel__responsavel__usuario__email__icontains=termo)
            )
            .select_related('turma')
            .distinct()
            .order_by('nome_completo')
        )

    paginator = Paginator(criancas, 20)
    page_obj = paginator.get_page(pagina)

    return render(request, 'criancas/buscar_criancas.html', {
        'termo': termo,
        'criancas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
    })


@perfil_requerido(['recepcao', 'checkin', 'checkout', 'professor', 'coordenacao', 'admin'])
def detalhe_crianca_staff(request, crianca_id):
    crianca = get_object_or_404(Crianca.objects.select_related('turma'), id=crianca_id, ativa=True)
    hoje = date.today()
    from presencas.models import PresencaDiaria
    presenca_hoje = PresencaDiaria.objects.filter(crianca=crianca, data=hoje).first()
    # Histórico dos dias em que a criança entrou/saiu (mais recentes primeiro)
    historico_presencas = (
        PresencaDiaria.objects
        .filter(crianca=crianca, status__in=['PRESENTE', 'RETIRADA'])
        .order_by('-data')[:30]
    )
    responsaveis = (
        CriancaResponsavel.objects
        .filter(crianca=crianca, ativo=True)
        .select_related('responsavel', 'responsavel__usuario')
        .order_by('-responsavel_principal', 'responsavel__nome_completo')
    )

    registrar_auditoria(
        request.user,
        'VISUALIZAR',
        'Crianca',
        crianca.id,
        f'Staff visualizou dados de {crianca.nome_completo}'
    )

    return render(request, 'criancas/detalhe_staff.html', {
        'crianca': crianca,
        'presenca_hoje': presenca_hoje,
        'historico_presencas': historico_presencas,
        'responsaveis': responsaveis,
    })


@responsavel_requerido
def criar_crianca(request):
    """Criar nova criança"""
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CriancaForm(request.POST, request.FILES)
        if form.is_valid():
            crianca = form.save()
            
            # Vincular responsável como principal
            CriancaResponsavel.objects.create(
                crianca=crianca,
                responsavel=responsavel,
                parentesco='Responsável',
                pode_fazer_checkin=True,
                pode_fazer_checkout=True,
                pode_editar_dados=True,
                responsavel_principal=True,
                ativo=True
            )
            
            registrar_auditoria(
                request.user,
                'CRIAR',
                'Crianca',
                crianca.id,
                f'Criança {crianca.nome_completo} criada'
            )
            
            messages.success(request, f'Criança {crianca.nome_completo} cadastrada com sucesso!')
            return redirect('responsaveis:minhas_criancas')
    else:
        form = CriancaForm()
    
    context = {'form': form}
    return render(request, 'criancas/criar_crianca.html', context)


@responsavel_requerido
def editar_crianca(request, crianca_id):
    """Editar dados da criança"""
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    crianca = get_object_or_404(Crianca, id=crianca_id)
    
    # Verificar permissão
    if not CriancaResponsavel.objects.filter(
        crianca=crianca,
        responsavel=responsavel,
        pode_editar_dados=True,
        ativo=True
    ).exists():
        messages.error(request, 'Você não tem permissão para editar esta criança.')
        return redirect('responsaveis:minhas_criancas')
    
    if request.method == 'POST':
        form = CriancaForm(request.POST, request.FILES, instance=crianca)
        if form.is_valid():
            form.save()
            registrar_auditoria(
                request.user,
                'ATUALIZAR',
                'Crianca',
                crianca.id,
                f'Dados de {crianca.nome_completo} atualizados'
            )
            messages.success(request, 'Dados da criança atualizados com sucesso!')
            return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)
    else:
        form = CriancaForm(instance=crianca)
    
    context = {
        'form': form,
        'crianca': crianca,
    }
    return render(request, 'criancas/editar_crianca.html', context)


@responsavel_requerido
def adicionar_responsavel(request, crianca_id):
    """Adicionar outro responsável autorizado à criança"""
    try:
        responsavel_principal = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    crianca = get_object_or_404(Crianca, id=crianca_id)
    
    # Verificar se é o responsável principal
    if not CriancaResponsavel.objects.filter(
        crianca=crianca,
        responsavel=responsavel_principal,
        responsavel_principal=True,
        ativo=True
    ).exists():
        messages.error(request, 'Apenas o responsável principal pode adicionar outros responsáveis.')
        return redirect('responsaveis:minhas_criancas')
    
    if request.method == 'POST':
        form = CriancaResponsavelForm(request.POST, crianca=crianca)
        if form.is_valid():
            crianca_responsavel = form.save(commit=False)
            crianca_responsavel.crianca = crianca
            vinculo_existente = CriancaResponsavel.objects.filter(
                crianca=crianca,
                responsavel=crianca_responsavel.responsavel
            ).first()

            if vinculo_existente:
                vinculo_existente.parentesco = crianca_responsavel.parentesco
                vinculo_existente.pode_fazer_checkin = crianca_responsavel.pode_fazer_checkin
                vinculo_existente.pode_fazer_checkout = crianca_responsavel.pode_fazer_checkout
                vinculo_existente.pode_editar_dados = crianca_responsavel.pode_editar_dados
                vinculo_existente.responsavel_principal = crianca_responsavel.responsavel_principal
                vinculo_existente.ativo = True
                vinculo_existente.save()
                crianca_responsavel = vinculo_existente
            else:
                crianca_responsavel.save()
            
            registrar_auditoria(
                request.user,
                'CRIAR',
                'CriancaResponsavel',
                crianca_responsavel.id,
                f'Responsável {crianca_responsavel.responsavel.nome_completo} adicionado'
            )
            
            messages.success(request, 'Responsável adicionado com sucesso!')
            return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)
    else:
        form = CriancaResponsavelForm(crianca=crianca)
    
    context = {
        'form': form,
        'crianca': crianca,
    }
    return render(request, 'criancas/adicionar_responsavel.html', context)


@responsavel_requerido
def editar_responsavel(request, vinculo_id):
    """Editar permissões de um responsável vinculado à criança."""
    vinculo = get_object_or_404(
        CriancaResponsavel.objects.select_related('crianca', 'responsavel'),
        id=vinculo_id
    )
    crianca = vinculo.crianca

    if not _usuario_pode_gerenciar_responsaveis(request.user, crianca):
        messages.error(request, 'Apenas o responsável principal pode alterar permissões.')
        return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)

    if request.method == 'POST':
        form = CriancaResponsavelPermissoesForm(request.POST, instance=vinculo)
        if form.is_valid():
            atualizado = form.save(commit=False)
            deixara_sem_principal = (
                vinculo.responsavel_principal
                and (not atualizado.responsavel_principal or not atualizado.ativo)
                and not CriancaResponsavel.objects.filter(
                    crianca=crianca,
                    responsavel_principal=True,
                    ativo=True
                ).exclude(id=vinculo.id).exists()
            )
            if deixara_sem_principal:
                messages.error(request, 'Defina outro responsável principal antes de remover este como principal.')
                return redirect('criancas:editar_responsavel', vinculo_id=vinculo.id)
            atualizado.save()
            registrar_auditoria(
                request.user,
                'ATUALIZAR',
                'CriancaResponsavel',
                vinculo.id,
                f'Permissões de {vinculo.responsavel.nome_completo} alteradas para {crianca.nome_completo}'
            )
            messages.success(request, 'Permissões atualizadas com sucesso.')
            return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)
    else:
        form = CriancaResponsavelPermissoesForm(instance=vinculo)

    context = {
        'form': form,
        'vinculo': vinculo,
        'crianca': crianca,
    }
    return render(request, 'criancas/editar_responsavel.html', context)


@responsavel_requerido
@require_POST
def revogar_responsavel(request, vinculo_id):
    """Revogar acesso de um responsável sem apagar o histórico."""
    vinculo = get_object_or_404(
        CriancaResponsavel.objects.select_related('crianca', 'responsavel'),
        id=vinculo_id
    )
    crianca = vinculo.crianca

    if not _usuario_pode_gerenciar_responsaveis(request.user, crianca):
        messages.error(request, 'Apenas o responsável principal pode revogar acessos.')
        return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)

    if vinculo.responsavel_principal:
        outros_principais = CriancaResponsavel.objects.filter(
            crianca=crianca,
            responsavel_principal=True,
            ativo=True
        ).exclude(id=vinculo.id).exists()
        if not outros_principais:
            messages.error(request, 'Defina outro responsável principal antes de revogar este acesso.')
            return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)

    vinculo.ativo = False
    vinculo.pode_fazer_checkin = False
    vinculo.pode_fazer_checkout = False
    vinculo.pode_editar_dados = False
    vinculo.responsavel_principal = False
    vinculo.save()

    registrar_auditoria(
        request.user,
        'REVOGAR',
        'CriancaResponsavel',
        vinculo.id,
        f'Acesso de {vinculo.responsavel.nome_completo} revogado para {crianca.nome_completo}'
    )
    messages.success(request, 'Acesso do responsável revogado.')
    return redirect('responsaveis:detalhe_crianca', crianca_id=crianca.id)
