import uuid
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from core.decorators import coordenacao_requerida
from core.utils import registrar_auditoria
from .alocacao import sugerir_turma
from .forms import TurmaForm
from .models import Turma


EXCEL_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def _excel_coluna(indice):
    nome = ''
    while indice:
        indice, resto = divmod(indice - 1, 26)
        nome = chr(65 + resto) + nome
    return nome


def _texto_xml(valor):
    return escape(str(valor), {'"': '&quot;', "'": '&apos;'})


def _gerar_xlsx_simples(linhas):
    total_linhas = len(linhas)
    total_colunas = max((len(linha) for linha in linhas), default=1)
    ultima_celula = f'{_excel_coluna(total_colunas)}{total_linhas or 1}'
    strings_compartilhadas = []
    indices_strings = {}
    total_strings = 0

    def indice_string(valor):
        nonlocal total_strings
        texto = str(valor)
        total_strings += 1
        if texto not in indices_strings:
            indices_strings[texto] = len(strings_compartilhadas)
            strings_compartilhadas.append(texto)
        return indices_strings[texto]

    linhas_xml = []
    for linha_idx, linha in enumerate(linhas, start=1):
        celulas = []
        for coluna_idx, valor in enumerate(linha, start=1):
            referencia = f'{_excel_coluna(coluna_idx)}{linha_idx}'
            estilo = ' s="1"' if linha_idx == 1 else ''
            if valor in (None, ''):
                celulas.append(f'<c r="{referencia}"{estilo}/>')
            elif isinstance(valor, int):
                celulas.append(f'<c r="{referencia}"{estilo}><v>{valor}</v></c>')
            else:
                celulas.append(f'<c r="{referencia}" t="s"{estilo}><v>{indice_string(valor)}</v></c>')
        linhas_xml.append(f'<row r="{linha_idx}">{"".join(celulas)}</row>')

    worksheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="A1:{ultima_celula}"/>
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>
      <selection pane="bottomLeft"/>
    </sheetView>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>
    <col min="1" max="1" width="34" customWidth="1"/>
    <col min="2" max="2" width="16" customWidth="1"/>
    <col min="3" max="3" width="10" customWidth="1"/>
    <col min="4" max="4" width="18" customWidth="1"/>
    <col min="5" max="5" width="34" customWidth="1"/>
    <col min="6" max="6" width="18" customWidth="1"/>
  </cols>
  <sheetData>
    {''.join(linhas_xml)}
  </sheetData>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>'''

    shared_strings = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{total_strings}" uniqueCount="{len(strings_compartilhadas)}">
  {''.join(f'<si><t>{_texto_xml(texto)}</t></si>' for texto in strings_compartilhadas)}
</sst>'''

    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as arquivo:
        arquivo.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>''')
        arquivo.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>''')
        arquivo.writestr('docProps/core.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>EBF PIBVP</dc:creator>
  <cp:lastModifiedBy>EBF PIBVP</cp:lastModifiedBy>
</cp:coreProperties>''')
        arquivo.writestr('docProps/app.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>EBF PIBVP</Application>
</Properties>''')
        arquivo.writestr('xl/workbook.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <workbookPr/>
  <bookViews>
    <workbookView xWindow="0" yWindow="0" windowWidth="16384" windowHeight="8192"/>
  </bookViews>
  <sheets>
    <sheet name="Criancas" sheetId="1" r:id="rId1"/>
  </sheets>
  <calcPr calcId="124519" fullCalcOnLoad="1"/>
</workbook>''')
        arquivo.writestr('xl/_rels/workbook.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>''')
        arquivo.writestr('xl/styles.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2"><font><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font><font><b/><sz val="11"/><color theme="1"/><name val="Calibri"/><family val="2"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
  <dxfs count="0"/>
  <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>''')
        arquivo.writestr('xl/sharedStrings.xml', shared_strings)
        arquivo.writestr('xl/worksheets/sheet1.xml', worksheet)

    return buffer.getvalue()


def _obter_criancas_da_turma(turma):
    from criancas.models import Crianca, CriancaResponsavel

    vinculos_ativos = CriancaResponsavel.objects.filter(ativo=True).select_related('responsavel').order_by(
        '-responsavel_principal',
        'responsavel__nome_completo',
    )
    criancas = list(
        Crianca.objects.filter(turma=turma, ativa=True)
        .prefetch_related(models.Prefetch('crianca_responsavel', queryset=vinculos_ativos, to_attr='vinculos_ativos'))
        .order_by('nome_completo')
    )

    for crianca in criancas:
        crianca.responsavel_principal_turma = crianca.vinculos_ativos[0].responsavel if crianca.vinculos_ativos else None
    return criancas


@coordenacao_requerida
def listar_turmas(request):
    todas = Turma.objects.annotate(
        total_criancas_ativas=models.Count(
            'criancas',
            filter=models.Q(criancas__ativa=True),
            distinct=True,
        )
    ).order_by('nome')
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
def criancas_da_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    criancas = _obter_criancas_da_turma(turma)

    return render(request, 'turmas/criancas_da_turma.html', {
        'turma': turma,
        'criancas': criancas,
        'total': len(criancas),
    })


@coordenacao_requerida
def exportar_criancas_excel(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    criancas = _obter_criancas_da_turma(turma)

    linhas = [[
        'Nome completo',
        'Código',
        'Idade',
        'Data de nascimento',
        'Responsável principal',
        'Telefone',
    ]]

    for crianca in criancas:
        responsavel = crianca.responsavel_principal_turma
        linhas.append([
            crianca.nome_completo,
            crianca.codigo_interno,
            crianca.get_idade(),
            crianca.data_nascimento.strftime('%d/%m/%Y'),
            responsavel.nome_completo if responsavel else '',
            responsavel.telefone if responsavel else '',
        ])

    nome_arquivo = f'criancas-{slugify(turma.nome) or "turma"}.xlsx'
    response = HttpResponse(_gerar_xlsx_simples(linhas), content_type=EXCEL_CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    return response


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
