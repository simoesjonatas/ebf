from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import secrets
from core.models import BaseModel
from criancas.models import Crianca
from responsaveis.models import Responsavel

STATUS_PRESENCA = [
    ('NAO_CHEGOU', 'Não chegou'),
    ('PRESENTE', 'Presente'),
    ('RETIRADA', 'Retirada'),
    ('AUSENTE', 'Ausente'),
]

TIPO_QR_LOTE = [
    ('CHECKIN', 'Check-in'),
    ('CHECKOUT', 'Check-out'),
]


class PresencaDiaria(BaseModel):
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE, related_name='presencas')
    data = models.DateField(auto_now_add=True, db_index=True)
    
    status = models.CharField(max_length=20, choices=STATUS_PRESENCA, default='NAO_CHEGOU')
    
    # Check-in
    horario_checkin = models.DateTimeField(null=True, blank=True)
    usuario_checkin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='presencas_checkin')
    responsavel_checkin = models.ForeignKey(Responsavel, on_delete=models.SET_NULL, null=True, blank=True, related_name='presencas_checkin')
    checkout_token = models.CharField(max_length=80, unique=True, null=True, blank=True, db_index=True)
    checkout_token_expira_em = models.DateTimeField(null=True, blank=True)
    
    # Check-out
    horario_checkout = models.DateTimeField(null=True, blank=True)
    usuario_checkout = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='presencas_checkout')
    responsavel_checkout = models.ForeignKey(Responsavel, on_delete=models.SET_NULL, null=True, blank=True, related_name='presencas_checkout')
    
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Presença Diária'
        verbose_name_plural = 'Presenças Diárias'
        ordering = ['-data', 'crianca__nome_completo']
        unique_together = ('crianca', 'data')

    def __str__(self):
        return f"{self.crianca.nome_completo} - {self.data.strftime('%d/%m/%Y')} ({self.get_status_display()})"

    def fazer_checkin(self, usuario, responsavel=None):
        self.status = 'PRESENTE'
        self.horario_checkin = timezone.now()
        self.usuario_checkin = usuario
        self.responsavel_checkin = responsavel
        self.gerar_checkout_token()
        self.save()

    def fazer_checkout(self, usuario, responsavel):
        if self.status != 'PRESENTE':
            raise ValueError("Criança não está marcada como presente")
        self.status = 'RETIRADA'
        self.horario_checkout = timezone.now()
        self.usuario_checkout = usuario
        self.responsavel_checkout = responsavel
        self.save()

    def ja_fez_checkin(self):
        return self.status in ['PRESENTE', 'RETIRADA']

    def ja_fez_checkout(self):
        return self.status == 'RETIRADA'

    def gerar_checkout_token(self, validade_horas=12):
        while True:
            token = secrets.token_urlsafe(32)
            if not PresencaDiaria.objects.filter(checkout_token=token).exclude(id=self.id).exists():
                self.checkout_token = token
                self.checkout_token_expira_em = timezone.now() + timedelta(hours=validade_horas)
                return token

    def checkout_token_valido(self):
        return (
            self.checkout_token
            and self.checkout_token_expira_em
            and self.checkout_token_expira_em >= timezone.now()
            and self.status == 'PRESENTE'
        )


class QRCodeOperacaoLote(BaseModel):
    tipo = models.CharField(max_length=20, choices=TIPO_QR_LOTE)
    responsavel = models.ForeignKey(Responsavel, on_delete=models.CASCADE, related_name='qrcodes_lote')
    criancas = models.ManyToManyField(Crianca, related_name='qrcodes_lote')
    token = models.CharField(max_length=80, unique=True, db_index=True)
    expira_em = models.DateTimeField(db_index=True)
    usado_em = models.DateTimeField(null=True, blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='qrcodes_lote_criados')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'QR Code de Operação em Lote'
        verbose_name_plural = 'QR Codes de Operação em Lote'
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.token:
            while True:
                token = secrets.token_urlsafe(32)
                if not QRCodeOperacaoLote.objects.filter(token=token).exists():
                    self.token = token
                    break
        if not self.expira_em:
            self.expira_em = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def valido(self):
        return self.ativo and not self.usado_em and self.expira_em >= timezone.now()

    def marcar_usado(self):
        self.usado_em = timezone.now()
        self.ativo = False
        self.save(update_fields=['usado_em', 'ativo', 'atualizado_em'])
