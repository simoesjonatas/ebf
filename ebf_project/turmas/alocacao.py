import re


def extrair_faixa(faixa_etaria):
    """Extrai (idade_min, idade_max) de um texto livre.
    Aceita faixas ('4-5 anos', '11 - 12 anos') e idade única ('3 anos',
    nesse caso vira (3, 3)). Retorna None se não houver nenhum número
    (ex.: 'Adultos')."""
    texto = faixa_etaria or ''
    match = re.search(r'(\d+)\s*-\s*(\d+)', texto)
    if match:
        minimo, maximo = int(match.group(1)), int(match.group(2))
        if minimo > maximo:
            minimo, maximo = maximo, minimo
        return minimo, maximo

    match = re.search(r'(\d+)', texto)
    if match:
        idade = int(match.group(1))
        return idade, idade

    return None


def sugerir_turma(idade, turmas):
    """Sugere automaticamente uma turma para a idade informada.
    Só sugere quando exatamente uma turma ativa tem faixa etária
    compatível — em caso de ambiguidade ou nenhuma turma compatível,
    retorna None para que a alocação seja feita manualmente."""
    compativeis = []
    for turma in turmas:
        faixa = extrair_faixa(turma.faixa_etaria)
        if faixa and faixa[0] <= idade <= faixa[1]:
            compativeis.append(turma)
    return compativeis[0] if len(compativeis) == 1 else None
