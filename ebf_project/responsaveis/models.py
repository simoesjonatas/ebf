import uuid
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class Responsavel(BaseModel):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='responsavel')
    nome_completo = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True)
    documento = models.CharField(max_length=20, blank=True, unique=True, null=True)
    token_qr = models.CharField(max_length=100, unique=True, db_index=True)
    autorizacao_imagem = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Responsável'
        verbose_name_plural = 'Responsáveis'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.usuario.email})"

    def save(self, *args, **kwargs):
        if not self.token_qr:
            self.token_qr = str(uuid.uuid4())
        super().save(*args, **kwargs)
