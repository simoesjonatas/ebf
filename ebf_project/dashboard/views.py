import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from datetime import date
from core.decorators import coordenacao_requerida
from core.utils import registrar_auditoria
from criancas.models import Crianca
from presencas.models import PresencaDiaria
from turmas.models import Turma


def get_dashboard_stats():
    """Obter estatísticas do dashboard"""
    hoje = date.today()

    total_criancas = Crianca.objects.filter(ativa=True).count()
    presentes_hoje = PresencaDiaria.objects.filter(data=hoje, status='PRESENTE').count()
    retiradas_hoje = PresencaDiaria.objects.filter(data=hoje, status='RETIRADA').count()
    checkins_hoje = presentes_hoje + retiradas_hoje

    # Turmas com total e presentes (distinct evita inflar por joins múltiplos)
    turmas = list(
        Turma.objects.filter(ativa=True).annotate(
            total_criancas=Count('criancas', distinct=True),
            presentes=Count(
                'criancas__presencas',
                filter=Q(criancas__presencas__data=hoje, criancas__presencas__status='PRESENTE'),
                distinct=True,
            ),
        ).order_by('nome')
    )
    # Percentual real de presença por turma (calculado aqui, não no template)
    for turma in turmas:
        turma.percentual = round(turma.presentes / turma.total_criancas * 100) if turma.total_criancas else 0

    stats = {
        'total_criancas': total_criancas,
        'presentes_hoje': presentes_hoje,
        'retiradas_hoje': retiradas_hoje,
        'checkins_hoje': checkins_hoje,
        'dentro_da_igreja': presentes_hoje,
        'taxa_presenca': round(checkins_hoje / total_criancas * 100) if total_criancas else 0,
        'criancas_com_alergia': Crianca.objects.filter(ativa=True, alergias__gt='').count(),
        'sem_autorizacao_imagem': Crianca.objects.filter(ativa=True, autorizacao_imagem=False).count(),
        'presentes_com_alergia': PresencaDiaria.objects.filter(
            data=hoje,
            status='PRESENTE',
            crianca__alergias__gt=''
        ).count(),
        'turmas': turmas,
        'checkouts_pendentes': presentes_hoje,
    }

    return stats


@coordenacao_requerida
def dashboard(request):
    """Dashboard da coordenação"""
    return render(request, 'dashboard/dashboard.html', {'stats': get_dashboard_stats()})


def _listar_por_presenca(request, statuses, ctx, so_alergias=False):
    """Helper: lista presenças de hoje por status, com filtro de nome/turma e
    paginação. 'ctx' traz os rótulos específicos de cada tela.
    so_alergias=True restringe às crianças que têm alergias cadastradas."""
    hoje = date.today()
    termo = request.GET.get('q', '').strip()
    turma_id = request.GET.get('turma', '').strip()

    presencas = (
        PresencaDiaria.objects
        .filter(data=hoje, status__in=statuses)
        .select_related('crianca', 'crianca__turma')
        .order_by('crianca__nome_completo')
    )

    if so_alergias:
        presencas = presencas.filter(crianca__alergias__gt='')

    if termo:
        presencas = presencas.filter(crianca__nome_completo__icontains=termo)

    if turma_id:
        try:
            uuid.UUID(turma_id)
            presencas = presencas.filter(crianca__turma_id=turma_id)
        except (ValueError, TypeError):
            turma_id = ''

    paginator = Paginator(presencas, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'presencas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'turmas': Turma.objects.filter(ativa=True).order_by('nome'),
        'termo': termo,
        'turma_id': turma_id,
        'total': paginator.count,
    }
    context.update(ctx)
    return render(request, 'dashboard/criancas_por_presenca.html', context)


@coordenacao_requerida
def criancas_presentes(request):
    """Crianças que ainda estão na igreja agora (check-in feito, sem retirada)."""
    return _listar_por_presenca(request, ['PRESENTE'], {
        'titulo': 'Crianças na igreja agora',
        'eyebrow': 'Tempo real',
        'icone': 'bi-house-heart-fill',
        'icone_cor': 'is-green',
        'url_atual': 'dashboard:criancas_presentes',
        'mostrar_checkout': False,
        'permitir_checkout': True,
        'vazio': 'Nenhuma criança na igreja no momento.',
    })


@coordenacao_requerida
def criancas_checkins(request):
    """Todas as crianças que fizeram check-in hoje (presentes + já retiradas)."""
    return _listar_por_presenca(request, ['PRESENTE', 'RETIRADA'], {
        'titulo': 'Check-ins de hoje',
        'eyebrow': 'Hoje',
        'icone': 'bi-box-arrow-in-right',
        'icone_cor': '',
        'url_atual': 'dashboard:criancas_checkins',
        'mostrar_checkout': True,
        'vazio': 'Nenhum check-in registrado hoje.',
    })


@coordenacao_requerida
def criancas_retiradas(request):
    """Crianças que já foram retiradas hoje."""
    return _listar_por_presenca(request, ['RETIRADA'], {
        'titulo': 'Crianças já retiradas',
        'eyebrow': 'Hoje',
        'icone': 'bi-box-arrow-right',
        'icone_cor': 'is-orange',
        'url_atual': 'dashboard:criancas_retiradas',
        'mostrar_checkout': True,
        'vazio': 'Nenhuma criança retirada ainda hoje.',
    })


@coordenacao_requerida
def criancas_ativas(request):
    """Lista todas as crianças ativas cadastradas, com filtro por nome/código
    e por turma, com paginação."""
    termo = request.GET.get('q', '').strip()
    turma_id = request.GET.get('turma', '').strip()
    sem_imagem = request.GET.get('sem_imagem') == '1'

    criancas = (
        Crianca.objects.filter(ativa=True)
        .select_related('turma')
        .order_by('nome_completo')
    )

    if termo:
        criancas = criancas.filter(
            Q(nome_completo__icontains=termo) | Q(codigo_interno__icontains=termo)
        )

    if turma_id:
        try:
            uuid.UUID(turma_id)
            criancas = criancas.filter(turma_id=turma_id)
        except (ValueError, TypeError):
            turma_id = ''

    if sem_imagem:
        criancas = criancas.filter(autorizacao_imagem=False)

    paginator = Paginator(criancas, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/criancas_ativas.html', {
        'criancas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'turmas': Turma.objects.filter(ativa=True).order_by('nome'),
        'termo': termo,
        'turma_id': turma_id,
        'sem_imagem': sem_imagem,
        'total': paginator.count,
    })


@coordenacao_requerida
def criancas_alergias(request):
    """Crianças presentes que possuem alergias cadastradas."""
    return _listar_por_presenca(request, ['PRESENTE'], {
        'titulo': 'Presentes com alergias',
        'eyebrow': 'Atenção',
        'icone': 'bi-exclamation-triangle-fill',
        'icone_cor': 'is-yellow',
        'url_atual': 'dashboard:criancas_alergias',
        'mostrar_checkout': False,
        'mostrar_alergias': True,
        'vazio': 'Nenhuma criança presente com alergias.',
    }, so_alergias=True)


@coordenacao_requerida
@require_POST
def checkout_manual(request):
    """Check-out manual (sem QR) de uma ou várias crianças presentes.
    Feito pela coordenação direto na tela de presentes."""
    ids = request.POST.getlist('presencas')
    validos = []
    for i in ids:
        try:
            uuid.UUID(i)
            validos.append(i)
        except (ValueError, TypeError):
            continue

    hoje = date.today()
    presencas = (
        PresencaDiaria.objects
        .filter(id__in=validos, data=hoje, status='PRESENTE')
        .select_related('crianca')
    )

    feitos = 0
    for presenca in presencas:
        nota = 'Check-out manual (coordenação)'
        presenca.observacao = f'{presenca.observacao} | {nota}'.strip(' |') if presenca.observacao else nota
        try:
            presenca.fazer_checkout(request.user, None)  # sem responsável (manual)
            registrar_auditoria(
                request.user, 'CHECKOUT', 'PresencaDiaria', presenca.id,
                f'Check-out manual de {presenca.crianca.nome_completo}'
            )
            feitos += 1
        except ValueError:
            continue

    if feitos:
        plural = 's' if feitos != 1 else ''
        messages.success(request, f'{feitos} criança{plural} retirada{plural} manualmente com sucesso.')
    else:
        messages.info(request, 'Nenhuma criança foi retirada. Selecione ao menos uma criança presente.')

    querystring = request.GET.urlencode()
    destino = reverse('dashboard:criancas_presentes')
    return redirect(f'{destino}?{querystring}' if querystring else destino)


@coordenacao_requerida
def presenca_por_dia(request):
    """Relatório de presença por dia"""
    # Filtro por data
    data_str = request.GET.get('data')
    if data_str:
        try:
            from datetime import datetime
            filtro_data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except:
            filtro_data = date.today()
    else:
        filtro_data = date.today()
    
    presencas = PresencaDiaria.objects.filter(data=filtro_data).select_related('crianca', 'crianca__turma').order_by('crianca__nome_completo')
    
    context = {
        'presencas': presencas,
        'data_filtro': filtro_data,
    }
    
    return render(request, 'dashboard/presenca_por_dia.html', context)


@coordenacao_requerida
def criancas_por_turma(request):
    """Relatório de crianças por turma"""
    hoje = date.today()
    turmas = list(Turma.objects.filter(ativa=True).annotate(
        total=Count('criancas', distinct=True),
        presentes_hoje=Count(
            'criancas__presencas',
            filter=Q(criancas__presencas__data=hoje, criancas__presencas__status__in=['PRESENTE', 'RETIRADA']),
            distinct=True,
        )
    ).order_by('nome'))
    for turma in turmas:
        turma.percentual = round(turma.presentes_hoje / turma.total * 100) if turma.total else 0

    context = {
        'turmas': turmas,
    }

    return render(request, 'dashboard/criancas_por_turma.html', context)


@coordenacao_requerida
def criancas_com_restricoes(request):
    """Relatório de crianças com alergias/cuidados especiais"""
    hoje = date.today()
    criancas = Crianca.objects.filter(
        ativa=True
    ).filter(
        Q(alergias__gt='') | Q(cuidados_especiais__gt='') | Q(restricoes_alimentares__gt='')
    ).select_related('turma').order_by('nome_completo')
    
    context = {
        'criancas': criancas,
    }
    
    return render(request, 'dashboard/criancas_com_restricoes.html', context)


@coordenacao_requerida
def historico_checkin_checkout(request):
    """Histórico de check-in e checkout"""
    data_str = request.GET.get('data')
    if data_str:
        try:
            from datetime import datetime
            filtro_data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except:
            filtro_data = date.today()
    else:
        filtro_data = date.today()
    
    termo = request.GET.get('q', '').strip()

    presencas = PresencaDiaria.objects.filter(
        data=filtro_data,
        status__in=['PRESENTE', 'RETIRADA']
    ).select_related('crianca', 'usuario_checkin', 'usuario_checkout', 'responsavel_checkout').order_by('-data')

    if termo:
        presencas = presencas.filter(crianca__nome_completo__icontains=termo)

    context = {
        'presencas': presencas,
        'data_filtro': filtro_data,
        'termo': termo,
    }

    return render(request, 'dashboard/historico_checkin_checkout.html', context)
