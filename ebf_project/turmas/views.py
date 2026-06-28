import uuid
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.decorators import coordenacao_requerida
from core.utils import registrar_auditoria
from .alocacao import sugerir_turma
from .forms import TurmaForm
from .models import Turma


@coordenacao_requerida
def listar_turmas(request):
    todas = Turma.objects.all().order_by('nome')
    status = request.GET.get('status', 'todas')
    busca = request.GET.get('q', '').strip()

    turmas = todas
    if status == 'ativas':
        turmas = turmas.filter(ativa=True)
    elif status == 'inativas':
        turmas = turmas.filter(ativa=False)
    else:
        status = 'todas'

    if busca:
        turmas = turmas.filter(
            models.Q(nome__icontains=busca) |
            models.Q(faixa_etaria__icontains=busca) |
            models.Q(sala_local__icontains=busca)
        )

    return render(request, 'turmas/listar_turmas.html', {
        'turmas': turmas,
        'status': status,
        'busca': busca,
        'total_todas': todas.count(),
        'total_ativas': todas.filter(ativa=True).count(),
        'total_inativas': todas.filter(ativa=False).count(),
    })


@coordenacao_requerida
def criar_turma(request):
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turma cadastrada com sucesso.')
            return redirect('turmas:listar')
    else:
        form = TurmaForm(initial={'ativa': True})

    return render(request, 'turmas/turma_form.html', {'form': form, 'titulo': 'Cadastrar turma'})


@coordenacao_requerida
def editar_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turma atualizada com sucesso.')
            return redirect('turmas:listar')
    else:
        form = TurmaForm(instance=turma)

    return render(request, 'turmas/turma_form.html', {'form': form, 'turma': turma, 'titulo': 'Editar turma'})


@coordenacao_requerida
@require_POST
def alternar_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    turma.ativa = not turma.ativa
    turma.save(update_fields=['ativa', 'atualizado_em'])
    messages.success(request, f'Turma {turma.nome} {"ativada" if turma.ativa else "desativada"} com sucesso.')
    return redirect('turmas:listar')


@coordenacao_requerida
def criancas_sem_turma(request):
    from criancas.models import Crianca

    turmas_ativas = list(Turma.objects.filter(ativa=True).order_by('nome'))
    criancas = Crianca.objects.filter(turma__isnull=True, ativa=True).order_by('nome_completo')

    busca = request.GET.get('q', '').strip()
    if busca:
        criancas = criancas.filter(nome_completo__icontains=busca)

    itens = []
    for crianca in criancas:
        sugestao = sugerir_turma(crianca.get_idade(), turmas_ativas)
        itens.append({'crianca': crianca, 'sugestao': sugestao})

    return render(request, 'turmas/criancas_sem_turma.html', {
        'itens': itens,
        'turmas_ativas': turmas_ativas,
        'total_com_sugestao': sum(1 for i in itens if i['sugestao']),
        'busca': busca,
        'total_sem_turma': Crianca.objects.filter(turma__isnull=True, ativa=True).count(),
    })


@coordenacao_requerida
@require_POST
def alocar_automatico(request):
    from criancas.models import Crianca

    turmas_ativas = list(Turma.objects.filter(ativa=True).order_by('nome'))
    criancas = Crianca.objects.filter(turma__isnull=True, ativa=True)

    busca = request.POST.get('q', '').strip()
    if busca:
        criancas = criancas.filter(nome_completo__icontains=busca)

    alocadas = 0
    for crianca in criancas:
        sugestao = sugerir_turma(crianca.get_idade(), turmas_ativas)
        if sugestao:
            crianca.turma = sugestao
            crianca.save(update_fields=['turma', 'atualizado_em'])
            registrar_auditoria(
                request.user, 'ATUALIZAR', 'Crianca', crianca.id,
                f'Alocação automática: {crianca.nome_completo} -> turma {sugestao.nome}'
            )
            alocadas += 1

    if alocadas:
        messages.success(request, f'{alocadas} criança{"s" if alocadas != 1 else ""} alocada{"s" if alocadas != 1 else ""} automaticamente.')
    else:
        messages.info(request, 'Nenhuma criança pôde ser alocada automaticamente. Aloque manualmente abaixo.')

    if busca:
        return redirect(f"{reverse('turmas:sem_turma')}?q={busca}")
    return redirect('turmas:sem_turma')


@coordenacao_requerida
@require_POST
def alocar_manual(request):
    from criancas.models import Crianca

    crianca_id = request.POST.get('crianca_id', '').strip()
    turma_id = request.POST.get('turma_id', '').strip()
    busca = request.POST.get('q', '').strip()

    def voltar():
        if busca:
            return redirect(f"{reverse('turmas:sem_turma')}?q={busca}")
        return redirect('turmas:sem_turma')

    try:
        uuid.UUID(crianca_id)
    except (ValueError, TypeError):
        messages.error(request, 'Criança inválida.')
        return voltar()

    crianca = get_object_or_404(Crianca, id=crianca_id, ativa=True)

    if not turma_id:
        messages.error(request, 'Selecione uma turma.')
        return voltar()

    turma = get_object_or_404(Turma, id=turma_id, ativa=True)
    crianca.turma = turma
    crianca.save(update_fields=['turma', 'atualizado_em'])
    registrar_auditoria(
        request.user, 'ATUALIZAR', 'Crianca', crianca.id,
        f'Alocação manual: {crianca.nome_completo} -> turma {turma.nome}'
    )
    messages.success(request, f'{crianca.nome_completo} alocada na turma {turma.nome}.')
    return voltar()
