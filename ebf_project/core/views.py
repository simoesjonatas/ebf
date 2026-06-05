from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from criancas.models import Crianca
from presencas.models import PresencaDiaria
from datetime import date


@login_required
def home(request):
    """Home page com redirecionamento baseado no perfil"""
    context = {}
    
    try:
        perfil = request.user.perfil
        context['tipo_perfil'] = perfil.tipo_perfil
        context['perfil'] = perfil

        try:
            responsavel = request.user.responsavel
            criancas = Crianca.objects.filter(crianca_responsavel__responsavel=responsavel, crianca_responsavel__ativo=True).distinct()
            context['responsavel'] = responsavel
            context['has_responsavel'] = True
            context['criancas'] = criancas
            context['total_criancas'] = criancas.count()

            hoje = date.today()
            presencas_hoje = PresencaDiaria.objects.filter(crianca__in=criancas, data=hoje)
            context['presentes'] = presencas_hoje.filter(status='PRESENTE').count()
            context['retiradas'] = presencas_hoje.filter(status='RETIRADA').count()
        except Exception:
            context['has_responsavel'] = False

        if perfil.is_recepcao():
            context['modo'] = 'recepcao'
            hoje = date.today()
            context['presencas_hoje'] = PresencaDiaria.objects.filter(data=hoje)
            context['presentes_para_retirada'] = PresencaDiaria.objects.filter(
                data=hoje,
                status='PRESENTE'
            )
        
        elif perfil.is_checkin():
            context['modo'] = 'checkin'
            hoje = date.today()
            context['presencas_hoje'] = PresencaDiaria.objects.filter(data=hoje)
        
        elif perfil.is_checkout():
            context['modo'] = 'checkout'
            hoje = date.today()
            context['presentes_para_retirada'] = PresencaDiaria.objects.filter(
                data=hoje,
                status='PRESENTE'
            )
        
        elif perfil.is_coordenacao() or perfil.is_admin():
            from dashboard.views import get_dashboard_stats
            context.update(get_dashboard_stats())
    
    except Exception:
        context['tipo_perfil'] = 'anonimo'
    
    return render(request, 'core/home.html', context)


def access_denied(request):
    """Página de acesso negado"""
    return render(request, 'core/access_denied.html', {
        'mensagem': 'Seu perfil não possui permissão para acessar esta página.'
    }, status=403)


def termos_uso(request):
    """Termos de uso e política de privacidade."""
    return render(request, 'core/termos_uso.html')
