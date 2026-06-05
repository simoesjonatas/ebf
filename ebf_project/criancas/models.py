import uuid
from pathlib import Path
from datetime import date
from django.db import models
from django.utils import timezone
from django.utils.text import get_valid_filename
from core.models import BaseModel
from turmas.models import Turma


def caminho_foto_crianca(instance, filename):
    extensao = Path(filename).suffix.lower()
    nome = get_valid_filename(Path(filename).stem[:80]) or 'foto'
    nome_arquivo = f'{nome}{extensao}'
    return f'criancas/fotos/{instance.id}/{nome_arquivo}'


class Crianca(BaseModel):
    nome_completo = models.CharField(max_length=255)
    data_nascimento = models.DateField()
    foto = models.ImageField(upload_to=caminho_foto_crianca, null=True)
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, null=True, blank=True, related_name='criancas')
    
    # Informações de saúde e segurança
    alergias = models.TextField(blank=True)
    restricoes_alimentares = models.TextField(blank=True)
    cuidados_especiais = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    
    # Autorização
    autorizacao_imagem = models.BooleanField(default=True)
    
    # Tokens e códigos
    token_qr = models.CharField(max_length=100, unique=True, db_index=True)
    codigo_interno = models.CharField(max_length=20, unique=True, db_index=True)
    
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Criança'
        verbose_name_plural = 'Crianças'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.get_idade()} anos)"

    def save(self, *args, **kwargs):
        if not self.token_qr:
            self.token_qr = str(uuid.uuid4())
        if not self.codigo_interno:
            ultimo_codigo = (
                Crianca.objects
                .filter(codigo_interno__startswith='EBF-')
                .order_by('-codigo_interno')
                .values_list('codigo_interno', flat=True)
                .first()
            )
            numero = 1
            if ultimo_codigo:
                try:
                    numero = int(ultimo_codigo.split('-')[1]) + 1
                except (IndexError, ValueError):
                    numero = Crianca.objects.count() + 1
            while Crianca.objects.filter(codigo_interno=f"EBF-{numero:06d}").exists():
                numero += 1
            self.codigo_interno = f"EBF-{numero:06d}"
        super().save(*args, **kwargs)

    def get_idade(self):
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        return idade

    def get_responsaveis_checkin(self):
        return self.responsaveis.filter(
            crianca_responsavel__pode_fazer_checkin=True,
            crianca_responsavel__ativo=True
        )

    def get_responsaveis_checkout(self):
        return self.responsaveis.filter(
            crianca_responsavel__pode_fazer_checkout=True,
            crianca_responsavel__ativo=True
        )

    def tem_observacoes_importantes(self):
        return bool(self.alergias or self.cuidados_especiais)


class CriancaResponsavel(BaseModel):
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE, related_name='crianca_responsavel')
    responsavel = models.ForeignKey('responsaveis.Responsavel', on_delete=models.CASCADE, related_name='crianca_responsavel')
    
    parentesco = models.CharField(max_length=50, default='Responsável')
    pode_fazer_checkin = models.BooleanField(default=True)
    pode_fazer_checkout = models.BooleanField(default=True)
    pode_editar_dados = models.BooleanField(default=False)
    responsavel_principal = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Criança-Responsável'
        verbose_name_plural = 'Criança-Responsáveis'
        unique_together = ('crianca', 'responsavel')

    def __str__(self):
        return f"{self.crianca.nome_completo} - {self.responsavel.nome_completo}"


# Many-to-many through model
Crianca.responsaveis = models.ManyToManyField('responsaveis.Responsavel', through=CriancaResponsavel)
