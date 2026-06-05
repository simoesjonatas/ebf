from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import date
from core.decorators import coordenacao_requerida
from criancas.models import Crianca
from presencas.models import PresencaDiaria
from turmas.models import Turma


def get_dashboard_stats():
    """Obter estatísticas do dashboard"""
    hoje = date.today()
    
    stats = {
        'total_criancas': Crianca.objects.filter(ativa=True).count(),
        'presentes_hoje': PresencaDiaria.objects.filter(data=hoje, status='PRESENTE').count(),
        'retiradas_hoje': PresencaDiaria.objects.filter(data=hoje, status='RETIRADA').count(),
        'dentro_da_igreja': PresencaDiaria.objects.filter(data=hoje, status='PRESENTE').count(),
        'criancas_com_alergia': Crianca.objects.filter(ativa=True, alergias__gt='').count(),
        'presentes_com_alergia': PresencaDiaria.objects.filter(
            data=hoje,
            status='PRESENTE',
            crianca__alergias__gt=''
        ).count(),
        'turmas': Turma.objects.filter(ativa=True).annotate(
            total_criancas=Count('criancas'),
            presentes=Count('criancas__presencas', filter=Q(criancas__presencas__data=hoje, criancas__presencas__status='PRESENTE'))
        ),
        'checkouts_pendentes': PresencaDiaria.objects.filter(data=hoje, status='PRESENTE').count(),
    }
    
    return stats


@coordenacao_requerida
def dashboard(request):
    """Dashboard da coordenação"""
    stats = get_dashboard_stats()
    
    # Crianças sem responsável autorizado
    criancas_sem_responsavel = Crianca.objects.filter(
        ativa=True,
        crianca_responsavel__isnull=True
    ).distinct()
    stats['criancas_sem_responsavel'] = criancas_sem_responsavel.count()
    
    context = {
        'stats': stats,
        'criancas_sem_responsavel': criancas_sem_responsavel,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


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
    turmas = Turma.objects.filter(ativa=True).annotate(
        total=Count('criancas'),
        presentes_hoje=Count('criancas__presencas', filter=Q(criancas__presencas__data=hoje, criancas__presencas__status__in=['PRESENTE', 'RETIRADA']))
    )
    
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
    
    presencas = PresencaDiaria.objects.filter(
        data=filtro_data,
        status__in=['PRESENTE', 'RETIRADA']
    ).select_related('crianca', 'usuario_checkin', 'usuario_checkout', 'responsavel_checkout').order_by('-data')
    
    context = {
        'presencas': presencas,
        'data_filtro': filtro_data,
    }
    
    return render(request, 'dashboard/historico_checkin_checkout.html', context)
