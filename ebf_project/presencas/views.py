from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
from core.decorators import recepcao_requerida, checkout_requerido
from core.utils import normalize_qr_payload, registrar_auditoria
from criancas.models import Crianca, CriancaResponsavel
from responsaveis.models import Responsavel
from .models import PresencaDiaria, QRCodeOperacaoLote
from .forms import CheckinForm, CheckoutForm
from etiquetas.models import Etiqueta


@recepcao_requerida
def leitura_qr_checkin(request):
    """Página para leitura de QR Code de check-in"""
    return render(request, 'presencas/leitura_qr_checkin.html')


@recepcao_requerida
@require_http_methods(["POST"])
def processar_qr_checkin(request):
    """Processa leitura de QR Code para check-in"""
    tipo_qr, token = normalize_qr_payload(request.POST.get('token', ''))
    
    if not token:
        return JsonResponse({'sucesso': False, 'mensagem': 'Token inválido'})

    if tipo_qr == 'checkout':
        return JsonResponse({'sucesso': False, 'mensagem': 'Este QR Code é temporário de check-out, não de check-in.'})
    if tipo_qr == 'checkout_lote':
        return JsonResponse({'sucesso': False, 'mensagem': 'Este QR Code é de check-out em lote, não de check-in.'})
    if tipo_qr == 'checkin_lote':
        lote = QRCodeOperacaoLote.objects.select_related('responsavel').filter(token=token, tipo='CHECKIN').first()
        if not lote:
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code de check-in em lote não encontrado.'})
        if not lote.valido():
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code de check-in em lote expirado ou já utilizado.'})
        return JsonResponse({
            'sucesso': True,
            'tipo': 'checkin_lote',
            'lote_id': str(lote.id),
            'nome': lote.responsavel.nome_completo,
        })
    
    crianca = Crianca.objects.filter(token_qr=token).first() if tipo_qr in [None, 'crianca'] else None
    responsavel = Responsavel.objects.filter(token_qr=token).first() if tipo_qr in [None, 'responsavel'] else None
    
    if crianca:
        return JsonResponse({
            'sucesso': True,
            'tipo': 'crianca',
            'crianca_id': str(crianca.id),
            'nome': crianca.nome_completo,
            'codigo': crianca.codigo_interno
        })
    
    elif responsavel:
        # Listar crianças que esse responsável pode fazer check-in
        criancas = Crianca.objects.filter(
            crianca_responsavel__responsavel=responsavel,
            crianca_responsavel__pode_fazer_checkin=True,
            crianca_responsavel__ativo=True
        ).distinct()
        
        return JsonResponse({
            'sucesso': True,
            'tipo': 'responsavel',
            'responsavel_id': str(responsavel.id),
            'nome': responsavel.nome_completo,
            'criancas': [
                {'id': str(c.id), 'nome': c.nome_completo, 'codigo': c.codigo_interno}
                for c in criancas
            ]
        })
    
    return JsonResponse({'sucesso': False, 'mensagem': 'QR Code não encontrado'})


@recepcao_requerida
def checkin_crianca(request, crianca_id):
    """Check-in de criança individual"""
    crianca = get_object_or_404(Crianca, id=crianca_id)
    hoje = date.today()
    
    # Obter ou criar registro de presença
    presenca, criado = PresencaDiaria.objects.get_or_create(crianca=crianca, data=hoje)
    
    if not criado and presenca.ja_fez_checkin():
        messages.warning(request, f'{crianca.nome_completo} já fez check-in hoje.')
        return redirect('presencas:leitura_qr_checkin')
    
    # Realizar check-in
    presenca.fazer_checkin(request.user)
    
    registrar_auditoria(
        request.user,
        'CHECKIN',
        'PresencaDiaria',
        presenca.id,
        f'Check-in de {crianca.nome_completo}'
    )
    
    messages.success(request, f'Check-in de {crianca.nome_completo} realizado com sucesso!')
    
    # Gerar etiqueta automaticamente
    Etiqueta.objects.get_or_create(
        presenca=presenca,
        crianca=crianca,
        defaults={'usuario_geracao': request.user}
    )
    
    return redirect('etiquetas:gerar_etiqueta', presenca_id=str(presenca.id))


@recepcao_requerida
def checkin_responsavel(request, responsavel_id):
    """Check-in em lote pelo responsável"""
    responsavel = get_object_or_404(Responsavel, id=responsavel_id)
    
    # Listar crianças que podem fazer check-in
    criancas = Crianca.objects.filter(
        crianca_responsavel__responsavel=responsavel,
        crianca_responsavel__pode_fazer_checkin=True,
        crianca_responsavel__ativo=True
    ).distinct()
    
    if request.method == 'POST':
        form = CheckinForm(criancas_queryset=criancas, data=request.POST)
        if form.is_valid():
            criancas_selecionadas = form.cleaned_data['criancas']
            hoje = date.today()
            
            for crianca in criancas_selecionadas:
                presenca, criado = PresencaDiaria.objects.get_or_create(crianca=crianca, data=hoje)
                
                if criado or not presenca.ja_fez_checkin():
                    presenca.fazer_checkin(request.user, responsavel=responsavel)
                    
                    registrar_auditoria(
                        request.user,
                        'CHECKIN',
                        'PresencaDiaria',
                        presenca.id,
                        f'Check-in de {crianca.nome_completo} (responsável {responsavel.nome_completo})'
                    )
                    
                    # Gerar etiqueta
                    Etiqueta.objects.get_or_create(
                        presenca=presenca,
                        crianca=crianca,
                        defaults={'usuario_geracao': request.user}
                    )
            
            messages.success(request, f'{len(criancas_selecionadas)} criança(s) registrada(s)!')
            return redirect('etiquetas:listar_etiquetas_dia')
    else:
        form = CheckinForm(criancas_queryset=criancas)
    
    context = {
        'form': form,
        'responsavel': responsavel,
    }
    return render(request, 'presencas/checkin_responsavel.html', context)


@recepcao_requerida
def checkin_lote(request, lote_id):
    """Check-in de várias crianças usando um único QR temporário."""
    lote = get_object_or_404(
        QRCodeOperacaoLote.objects.select_related('responsavel').prefetch_related('criancas'),
        id=lote_id,
        tipo='CHECKIN'
    )

    if not lote.valido():
        messages.error(request, 'QR Code de check-in em lote expirado ou já utilizado.')
        return redirect('presencas:leitura_qr_checkin')

    criancas = lote.criancas.filter(
        crianca_responsavel__responsavel=lote.responsavel,
        crianca_responsavel__pode_fazer_checkin=True,
        crianca_responsavel__ativo=True,
        ativa=True
    ).distinct()

    if request.method == 'POST':
        hoje = date.today()
        total = 0
        for crianca in criancas:
            presenca, criado = PresencaDiaria.objects.get_or_create(crianca=crianca, data=hoje)
            if criado or not presenca.ja_fez_checkin():
                presenca.fazer_checkin(request.user, responsavel=lote.responsavel)
                Etiqueta.objects.get_or_create(
                    presenca=presenca,
                    crianca=crianca,
                    defaults={'usuario_geracao': request.user}
                )
                registrar_auditoria(
                    request.user,
                    'CHECKIN',
                    'PresencaDiaria',
                    presenca.id,
                    f'Check-in em lote de {crianca.nome_completo} (responsável {lote.responsavel.nome_completo})'
                )
                total += 1

        lote.marcar_usado()
        messages.success(request, f'{total} criança(s) registrada(s) pelo QR em lote.')
        return redirect('etiquetas:listar_etiquetas_dia')

    return render(request, 'presencas/checkin_lote.html', {
        'lote': lote,
        'responsavel': lote.responsavel,
        'criancas': criancas,
    })


@checkout_requerido
def leitura_qr_checkout(request):
    """Página para leitura de QR Code de check-out"""
    return render(request, 'presencas/leitura_qr_checkout.html')


@checkout_requerido
@require_http_methods(["POST"])
def processar_qr_checkout(request):
    """Processa leitura de QR Code para check-out"""
    tipo_qr, token = normalize_qr_payload(request.POST.get('token', ''))
    hoje = date.today()
    
    if not token:
        return JsonResponse({'sucesso': False, 'mensagem': 'Token inválido'})

    if tipo_qr == 'checkout':
        presenca = (
            PresencaDiaria.objects
            .select_related('crianca')
            .filter(checkout_token=token, data=hoje)
            .first()
        )

        if not presenca:
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code temporário não encontrado para hoje.'})

        if not presenca.checkout_token_valido():
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code de check-out expirado ou criança não está presente.'})

        return JsonResponse({
            'sucesso': True,
            'tipo': 'presenca',
            'presenca_id': str(presenca.id),
            'crianca_id': str(presenca.crianca_id),
            'nome': presenca.crianca.nome_completo,
            'codigo': presenca.crianca.codigo_interno,
        })

    if tipo_qr == 'crianca':
        return JsonResponse({'sucesso': False, 'mensagem': 'Use o QR Code temporário da etiqueta ou o QR Code do responsável para check-out.'})
    if tipo_qr == 'checkin_lote':
        return JsonResponse({'sucesso': False, 'mensagem': 'Este QR Code é de check-in em lote, não de check-out.'})
    if tipo_qr == 'checkout_lote':
        lote = QRCodeOperacaoLote.objects.select_related('responsavel').filter(token=token, tipo='CHECKOUT').first()
        if not lote:
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code de check-out em lote não encontrado.'})
        if not lote.valido():
            return JsonResponse({'sucesso': False, 'mensagem': 'QR Code de check-out em lote expirado ou já utilizado.'})
        return JsonResponse({
            'sucesso': True,
            'tipo': 'checkout_lote',
            'lote_id': str(lote.id),
            'nome': lote.responsavel.nome_completo,
        })
    
    responsavel = Responsavel.objects.filter(token_qr=token).first()
    
    if not responsavel:
        return JsonResponse({'sucesso': False, 'mensagem': 'QR Code não encontrado'})
    
    # Listar crianças aptas para checkout
    criancas = Crianca.objects.filter(
        crianca_responsavel__responsavel=responsavel,
        crianca_responsavel__pode_fazer_checkout=True,
        crianca_responsavel__ativo=True,
        presencas__data=hoje,
        presencas__status='PRESENTE'
    ).distinct()
    
    if not criancas.exists():
        return JsonResponse({
            'sucesso': False,
            'mensagem': 'Nenhuma criança disponível para retirada'
        })
    
    return JsonResponse({
        'sucesso': True,
        'tipo': 'responsavel',
        'responsavel_id': str(responsavel.id),
        'nome': responsavel.nome_completo,
        'criancas': [
            {'id': str(c.id), 'nome': c.nome_completo, 'codigo': c.codigo_interno}
            for c in criancas
        ]
    })


@checkout_requerido
def checkout_presenca(request, presenca_id):
    """Checkout por QR temporário gerado no check-in."""
    presenca = get_object_or_404(
        PresencaDiaria.objects.select_related('crianca', 'crianca__turma'),
        id=presenca_id
    )
    crianca = presenca.crianca

    if not presenca.checkout_token_valido():
        messages.error(request, 'QR Code de check-out expirado ou criança não está presente.')
        return redirect('presencas:leitura_qr_checkout')

    vinculos = (
        CriancaResponsavel.objects
        .filter(
            crianca=crianca,
            ativo=True,
            pode_fazer_checkout=True,
            responsavel__ativo=True
        )
        .select_related('responsavel')
        .order_by('-responsavel_principal', 'responsavel__nome_completo')
    )

    if request.method == 'POST':
        responsavel_id = request.POST.get('responsavel_id')
        vinculo = vinculos.filter(responsavel_id=responsavel_id).first()

        if not vinculo:
            messages.error(request, 'Responsável não autorizado para retirar esta criança.')
            return redirect('presencas:checkout_presenca', presenca_id=presenca.id)

        presenca.fazer_checkout(request.user, vinculo.responsavel)

        registrar_auditoria(
            request.user,
            'CHECKOUT',
            'PresencaDiaria',
            presenca.id,
            f'Check-out de {crianca.nome_completo} por QR temporário (responsável {vinculo.responsavel.nome_completo})'
        )
        messages.success(request, f'{crianca.nome_completo} retirada com sucesso.')
        return redirect('presencas:leitura_qr_checkout')

    return render(request, 'presencas/checkout_presenca.html', {
        'presenca': presenca,
        'crianca': crianca,
        'vinculos': vinculos,
    })


@checkout_requerido
def checkout_lote(request, lote_id):
    """Checkout de várias crianças usando um único QR temporário."""
    lote = get_object_or_404(
        QRCodeOperacaoLote.objects.select_related('responsavel').prefetch_related('criancas'),
        id=lote_id,
        tipo='CHECKOUT'
    )

    if not lote.valido():
        messages.error(request, 'QR Code de check-out em lote expirado ou já utilizado.')
        return redirect('presencas:leitura_qr_checkout')

    hoje = date.today()
    criancas = lote.criancas.filter(
        crianca_responsavel__responsavel=lote.responsavel,
        crianca_responsavel__pode_fazer_checkout=True,
        crianca_responsavel__ativo=True,
        ativa=True,
        presencas__data=hoje,
        presencas__status='PRESENTE'
    ).distinct()

    if request.method == 'POST':
        total = 0
        for crianca in criancas:
            try:
                presenca = PresencaDiaria.objects.get(crianca=crianca, data=hoje, status='PRESENTE')
                presenca.fazer_checkout(request.user, lote.responsavel)
                registrar_auditoria(
                    request.user,
                    'CHECKOUT',
                    'PresencaDiaria',
                    presenca.id,
                    f'Check-out em lote de {crianca.nome_completo} (responsável {lote.responsavel.nome_completo})'
                )
                total += 1
            except PresencaDiaria.DoesNotExist:
                pass

        lote.marcar_usado()
        messages.success(request, f'{total} criança(s) retirada(s) pelo QR em lote.')
        return redirect('presencas:leitura_qr_checkout')

    return render(request, 'presencas/checkout_lote.html', {
        'lote': lote,
        'responsavel': lote.responsavel,
        'criancas': criancas,
    })


@checkout_requerido
def checkout_responsavel(request, responsavel_id):
    """Checkout pelo responsável"""
    responsavel = get_object_or_404(Responsavel, id=responsavel_id)
    hoje = date.today()
    
    # Listar crianças aptas para checkout
    criancas = Crianca.objects.filter(
        crianca_responsavel__responsavel=responsavel,
        crianca_responsavel__pode_fazer_checkout=True,
        crianca_responsavel__ativo=True,
        presencas__data=hoje,
        presencas__status='PRESENTE'
    ).distinct()
    
    if request.method == 'POST':
        form = CheckoutForm(criancas_queryset=criancas, data=request.POST)
        if form.is_valid():
            criancas_selecionadas = form.cleaned_data['criancas']
            observacao = form.cleaned_data.get('observacao', '')
            
            for crianca in criancas_selecionadas:
                try:
                    presenca = PresencaDiaria.objects.get(crianca=crianca, data=hoje)
                    presenca.fazer_checkout(request.user, responsavel)
                    if observacao:
                        presenca.observacao = observacao
                        presenca.save()
                    
                    registrar_auditoria(
                        request.user,
                        'CHECKOUT',
                        'PresencaDiaria',
                        presenca.id,
                        f'Check-out de {crianca.nome_completo} (responsável {responsavel.nome_completo})'
                    )
                except PresencaDiaria.DoesNotExist:
                    pass
            
            messages.success(request, f'{len(criancas_selecionadas)} criança(s) retirada(s)!')
            return redirect('presencas:leitura_qr_checkout')
    else:
        form = CheckoutForm(criancas_queryset=criancas)
    
    context = {
        'form': form,
        'responsavel': responsavel,
    }
    return render(request, 'presencas/checkout_responsavel.html', context)
