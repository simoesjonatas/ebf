from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class Turma(BaseModel):
    nome = models.CharField(max_length=100, unique=True)
    faixa_etaria = models.CharField(max_length=100)
    sala_local = models.CharField(max_length=100)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.faixa_etaria})"

    def get_professores(self):
        return self.professor_set.filter(ativo=True)


class Professor(BaseModel):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor')
    nome_completo = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True)
    funcao = models.CharField(max_length=100)
    turmas = models.ManyToManyField(Turma, blank=True, related_name='professores')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} - {self.funcao}"
