import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from datetime import date
from core.decorators import recepcao_requerida
from core.utils import generate_qr_code, get_qr_payload
from presencas.models import PresencaDiaria
from .models import Etiqueta


def _preparar_etiqueta_para_impressao(etiqueta):
    """Garante token de check-out válido e devolve os dados para renderizar
    uma etiqueta (criança, QR e validade)."""
    presenca = etiqueta.presenca
    if presenca.status == 'PRESENTE' and (not presenca.checkout_token or not presenca.checkout_token_valido()):
        presenca.gerar_checkout_token()
        presenca.save(update_fields=['checkout_token', 'checkout_token_expira_em', 'atualizado_em'])
    qr_code = generate_qr_code(get_qr_payload('checkout', presenca.checkout_token)) if presenca.checkout_token else None
    return {
        'crianca': etiqueta.crianca,
        'qr_code': qr_code,
        'checkout_token_expira_em': presenca.checkout_token_expira_em,
    }


@login_required
def gerar_etiqueta(request, presenca_id):
    """Gerar e exibir etiqueta de criança"""
    presenca = get_object_or_404(PresencaDiaria, id=presenca_id)
    crianca = presenca.crianca
    
    # Verificar permissões
    try:
        if request.user.perfil.is_responsavel():
            from responsaveis.models import Responsavel
            responsavel = request.user.responsavel
            if not presenca.crianca.crianca_responsavel.filter(responsavel=responsavel).exists():
                messages.error(request, 'Você não tem permissão para visualizar esta etiqueta.')
                return redirect('core:home')
    except:
        pass
    
    # Obter ou criar etiqueta
    etiqueta, criado = Etiqueta.objects.get_or_create(
        presenca=presenca,
        crianca=crianca,
        defaults={'usuario_geracao': request.user}
    )
    
    if presenca.status == 'PRESENTE' and (not presenca.checkout_token or not presenca.checkout_token_valido()):
        presenca.gerar_checkout_token()
        presenca.save(update_fields=['checkout_token', 'checkout_token_expira_em', 'atualizado_em'])

    qr_code = generate_qr_code(get_qr_payload('checkout', presenca.checkout_token)) if presenca.checkout_token else None
    
    context = {
        'etiqueta': etiqueta,
        'crianca': crianca,
        'qr_code': qr_code,
        'presenca': presenca,
        'checkout_token_expira_em': presenca.checkout_token_expira_em,
    }
    
    return render(request, 'etiquetas/gerar_etiqueta.html', context)


@recepcao_requerida
def listar_etiquetas_dia(request):
    """Listar etiquetas do dia"""
    hoje = date.today()
    status = request.GET.get('status', 'todas')
    pagina = request.GET.get('page', 1)

    etiquetas_base = Etiqueta.objects.filter(presenca__data=hoje)
    etiquetas = Etiqueta.objects.filter(
        presenca__data=hoje
    ).select_related('crianca', 'presenca').order_by('-data_geracao')

    if status == 'impressas':
        etiquetas = etiquetas.filter(impressa=True)
    elif status == 'pendentes':
        etiquetas = etiquetas.filter(impressa=False)
    else:
        status = 'todas'

    paginator = Paginator(etiquetas, 25)
    page_obj = paginator.get_page(pagina)
    
    context = {
        'etiquetas': page_obj.object_list,
        'data': hoje,
        'status': status,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_etiquetas': etiquetas_base.count(),
        'total_impressas': etiquetas_base.filter(impressa=True).count(),
        'total_pendentes': etiquetas_base.filter(impressa=False).count(),
    }
    
    return render(request, 'etiquetas/listar_etiquetas_dia.html', context)


@recepcao_requerida
def marcar_impressa(request, etiqueta_id):
    """Marcar etiqueta como impressa"""
    etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
    
    if not etiqueta.impressa:
        etiqueta.impressa = True
        etiqueta.data_impressao = timezone.now()
        etiqueta.save()
        messages.success(request, 'Etiqueta marcada como impressa.')

    proxima_url = request.GET.get('next')
    if proxima_url and url_has_allowed_host_and_scheme(
        proxima_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(proxima_url)

    return redirect('etiquetas:listar_etiquetas_dia')


@recepcao_requerida
def imprimir_lote(request):
    """Impressão em massa das etiquetas do dia (uma etiqueta 90x29mm por
    página). Por padrão imprime as pendentes; ?status=todas inclui as impressas."""
    hoje = date.today()
    status = request.GET.get('status', 'pendentes')

    etiquetas = Etiqueta.objects.filter(
        presenca__data=hoje
    ).select_related('crianca', 'crianca__turma', 'presenca').order_by('crianca__nome_completo')

    if status != 'todas':
        status = 'pendentes'
        etiquetas = etiquetas.filter(impressa=False)

    etiquetas = list(etiquetas)
    itens = [_preparar_etiqueta_para_impressao(e) for e in etiquetas]
    ids = [str(e.id) for e in etiquetas]

    return render(request, 'etiquetas/imprimir_lote.html', {
        'itens': itens,
        'ids': ids,
        'total': len(itens),
        'status': status,
        'data': hoje,
    })


@recepcao_requerida
@require_POST
def marcar_impressas_lote(request):
    """Confirma em massa que as etiquetas foram impressas."""
    ids = request.POST.getlist('etiquetas')
    validos = []
    for i in ids:
        try:
            uuid.UUID(i)
            validos.append(i)
        except (ValueError, TypeError):
            continue

    qs = Etiqueta.objects.filter(id__in=validos, impressa=False)
    atualizadas = qs.update(impressa=True, data_impressao=timezone.now())

    if atualizadas:
        messages.success(request, f'{atualizadas} etiqueta{"s" if atualizadas != 1 else ""} marcada{"s" if atualizadas != 1 else ""} como impressa{"s" if atualizadas != 1 else ""}.')
    else:
        messages.info(request, 'Nenhuma etiqueta pendente foi marcada.')

    return redirect('etiquetas:listar_etiquetas_dia')
