import uuid
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel

PROFILE_CHOICES = [
    ('responsavel', 'Responsável'),
    ('recepcao', 'Recepção'),
    ('checkin', 'Check-in'),
    ('professor', 'Professor'),
    ('checkout', 'Checkout'),
    ('coordenacao', 'Coordenação'),
    ('admin', 'Admin'),
]


class Perfil(BaseModel):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_perfil = models.CharField(max_length=20, choices=PROFILE_CHOICES, default='responsavel')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.get_tipo_perfil_display()}"

    def is_responsavel(self):
        return self.tipo_perfil == 'responsavel'

    def is_recepcao(self):
        return self.tipo_perfil == 'recepcao'

    def is_checkin(self):
        return self.tipo_perfil == 'checkin'

    def is_professor(self):
        return self.tipo_perfil == 'professor'

    def is_checkout(self):
        return self.tipo_perfil == 'checkout'

    def is_coordenacao(self):
        return self.tipo_perfil == 'coordenacao'

    def is_admin(self):
        return self.tipo_perfil == 'admin'

    def is_staff_user(self):
        return self.tipo_perfil in ['recepcao', 'checkin', 'professor', 'checkout', 'coordenacao', 'admin']
