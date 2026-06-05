from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.decorators import responsavel_requerido
from core.utils import generate_qr_code, get_qr_payload, registrar_auditoria
from criancas.models import Crianca, CriancaResponsavel
from presencas.forms import QRCodeLoteCriancasForm
from presencas.models import PresencaDiaria, QRCodeOperacaoLote
from .forms import ResponsavelForm
from .models import Responsavel
from datetime import date


@login_required
def ativar_responsavel(request):
    if hasattr(request.user, 'responsavel'):
        messages.info(request, 'Sua área de responsável já está ativa.')
        return redirect('responsaveis:minhas_criancas')

    nome_inicial = request.user.get_full_name() or request.user.email or request.user.username
    if request.method == 'POST':
        form = ResponsavelForm(request.POST)
        if form.is_valid():
            responsavel = form.save(commit=False)
            responsavel.usuario = request.user
            responsavel.save()
            registrar_auditoria(
                request.user,
                'CRIAR',
                'Responsavel',
                responsavel.id,
                'Área de responsável ativada pelo usuário'
            )
            messages.success(request, 'Área de responsável ativada. Agora você pode cadastrar ou vincular crianças.')
            return redirect('responsaveis:minhas_criancas')
    else:
        form = ResponsavelForm(initial={'nome_completo': nome_inicial})

    return render(request, 'responsaveis/ativar_responsavel.html', {'form': form})


@responsavel_requerido
def dashboard_responsavel(request):
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        messages.error(request, 'Responsável não encontrado.')
        return redirect('core:home')
    
    criancas = Crianca.objects.filter(
        crianca_responsavel__responsavel=responsavel,
        crianca_responsavel__ativo=True
    ).distinct()
    
    hoje = date.today()
    criancas_info = []
    for crianca in criancas:
        try:
            presenca = PresencaDiaria.objects.get(crianca=crianca, data=hoje)
        except PresencaDiaria.DoesNotExist:
            presenca = None
        
        criancas_info.append({
            'crianca': crianca,
            'presenca': presenca,
            'status': presenca.get_status_display() if presenca else 'Não marcada'
        })
    
    qr_code_responsavel = generate_qr_code(get_qr_payload('responsavel', responsavel.token_qr))
    
    context = {
        'responsavel': responsavel,
        'criancas_info': criancas_info,
        'qr_code_responsavel': qr_code_responsavel,
    }
    
    return render(request, 'responsaveis/dashboard.html', context)


@responsavel_requerido
def minhas_criancas(request):
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    criancas = Crianca.objects.filter(
        crianca_responsavel__responsavel=responsavel,
        crianca_responsavel__ativo=True
    ).distinct()
    
    context = {
        'criancas': criancas,
    }
    return render(request, 'responsaveis/minhas_criancas.html', context)


@responsavel_requerido
def detalhe_crianca(request, crianca_id):
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    crianca = get_object_or_404(Crianca, id=crianca_id)
    
    if not CriancaResponsavel.objects.filter(crianca=crianca, responsavel=responsavel, ativo=True).exists():
        messages.error(request, 'Você não tem permissão para visualizar esta criança.')
        return redirect('responsaveis:minhas_criancas')
    
    qr_code = generate_qr_code(get_qr_payload('crianca', crianca.token_qr))
    
    context = {
        'crianca': crianca,
        'qr_code': qr_code,
        'responsaveis_vinculados': CriancaResponsavel.objects.filter(
            crianca=crianca,
            ativo=True
        ).select_related('responsavel').order_by('-responsavel_principal', 'responsavel__nome_completo'),
        'responsaveis_revogados': CriancaResponsavel.objects.filter(
            crianca=crianca,
            ativo=False
        ).select_related('responsavel').order_by('responsavel__nome_completo'),
        'pode_gerenciar_responsaveis': CriancaResponsavel.objects.filter(
            crianca=crianca,
            responsavel=responsavel,
            responsavel_principal=True,
            ativo=True
        ).exists(),
    }
    
    return render(request, 'responsaveis/detalhe_crianca.html', context)


@responsavel_requerido
def editar_perfil(request):
    try:
        responsavel = request.user.responsavel
    except Responsavel.DoesNotExist:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = ResponsavelForm(request.POST, instance=responsavel)
        if form.is_valid():
            form.save()
            registrar_auditoria(
                request.user,
                'ATUALIZAR',
                'Responsavel',
                responsavel.id,
                'Dados do responsável atualizados'
            )
            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('responsaveis:dashboard')
    else:
        form = ResponsavelForm(instance=responsavel)
    
    context = {
        'form': form,
        'responsavel': responsavel,
    }
    
    return render(request, 'responsaveis/editar_perfil.html', context)


@responsavel_requerido
def gerar_qr_checkin_lote(request):
    responsavel = request.user.responsavel
    criancas = (
        Crianca.objects
        .filter(
            crianca_responsavel__responsavel=responsavel,
            crianca_responsavel__ativo=True,
            crianca_responsavel__pode_fazer_checkin=True,
            ativa=True
        )
        .exclude(presencas__data=date.today(), presencas__status__in=['PRESENTE', 'RETIRADA'])
        .distinct()
        .order_by('nome_completo')
    )

    qr_code = None
    lote = None
    if request.method == 'POST':
        form = QRCodeLoteCriancasForm(criancas_queryset=criancas, data=request.POST)
        if form.is_valid():
            lote = QRCodeOperacaoLote.objects.create(
                tipo='CHECKIN',
                responsavel=responsavel,
                criado_por=request.user
            )
            lote.criancas.set(form.cleaned_data['criancas'])
            qr_code = generate_qr_code(get_qr_payload('checkin_lote', lote.token))
            registrar_auditoria(
                request.user,
                'CRIAR',
                'QRCodeOperacaoLote',
                lote.id,
                f'QR temporário de check-in em lote gerado para {lote.criancas.count()} criança(s)'
            )
    else:
        form = QRCodeLoteCriancasForm(criancas_queryset=criancas)

    return render(request, 'responsaveis/gerar_qr_lote.html', {
        'form': form,
        'lote': lote,
        'qr_code': qr_code,
        'tipo': 'check-in',
        'titulo': 'Gerar QR de check-in em lote',
        'descricao': 'Selecione as crianças que chegarão juntas e apresente este QR na recepção.',
    })


@responsavel_requerido
def gerar_qr_checkout_lote(request):
    responsavel = request.user.responsavel
    criancas = (
        Crianca.objects
        .filter(
            crianca_responsavel__responsavel=responsavel,
            crianca_responsavel__ativo=True,
            crianca_responsavel__pode_fazer_checkout=True,
            ativa=True,
            presencas__data=date.today(),
            presencas__status='PRESENTE'
        )
        .distinct()
        .order_by('nome_completo')
    )

    qr_code = None
    lote = None
    if request.method == 'POST':
        form = QRCodeLoteCriancasForm(criancas_queryset=criancas, data=request.POST)
        if form.is_valid():
            lote = QRCodeOperacaoLote.objects.create(
                tipo='CHECKOUT',
                responsavel=responsavel,
                criado_por=request.user
            )
            lote.criancas.set(form.cleaned_data['criancas'])
            qr_code = generate_qr_code(get_qr_payload('checkout_lote', lote.token))
            registrar_auditoria(
                request.user,
                'CRIAR',
                'QRCodeOperacaoLote',
                lote.id,
                f'QR temporário de check-out em lote gerado para {lote.criancas.count()} criança(s)'
            )
    else:
        form = QRCodeLoteCriancasForm(criancas_queryset=criancas)

    return render(request, 'responsaveis/gerar_qr_lote.html', {
        'form': form,
        'lote': lote,
        'qr_code': qr_code,
        'tipo': 'check-out',
        'titulo': 'Gerar QR de check-out em lote',
        'descricao': 'Selecione as crianças presentes que serão retiradas juntas e apresente este QR no checkout.',
    })
