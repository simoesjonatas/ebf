from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.decorators import coordenacao_requerida
from .forms import TurmaForm
from .models import Turma


@coordenacao_requerida
def listar_turmas(request):
    turmas = Turma.objects.all().order_by('nome')
    return render(request, 'turmas/listar_turmas.html', {'turmas': turmas})


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
