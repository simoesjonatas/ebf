from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from criancas.models import Crianca
from presencas.models import PresencaDiaria


class Etiqueta(BaseModel):
    presenca = models.OneToOneField(PresencaDiaria, on_delete=models.CASCADE, related_name='etiqueta')
    crianca = models.ForeignKey(Crianca, on_delete=models.CASCADE)
    data_geracao = models.DateTimeField(auto_now_add=True)
    usuario_geracao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    impressa = models.BooleanField(default=False)
    data_impressao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'
        ordering = ['-data_geracao']

    def __str__(self):
        return f"Etiqueta - {self.crianca.nome_completo} ({self.presenca.data.strftime('%d/%m/%Y')})"
