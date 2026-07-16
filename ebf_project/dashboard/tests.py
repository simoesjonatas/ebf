from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Perfil


class CriancasAtivasPermissaoTests(TestCase):
    def acessar_com_usuario(self, usuario):
        self.client.force_login(usuario)
        return self.client.get(reverse('dashboard:criancas_ativas'))

    def test_perfis_staff_acessam_criancas_ativas(self):
        for tipo in ['recepcao', 'checkin', 'checkout', 'professor', 'coordenacao', 'admin']:
            with self.subTest(tipo=tipo):
                usuario = User.objects.create_user(username=f'user_{tipo}', password='senha123')
                Perfil.objects.create(usuario=usuario, tipo_perfil=tipo, ativo=True)

                response = self.acessar_com_usuario(usuario)

                self.assertEqual(response.status_code, 200)

    def test_superuser_sem_perfil_acessa_criancas_ativas(self):
        usuario = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='senha123',
        )

        response = self.acessar_com_usuario(usuario)

        self.assertEqual(response.status_code, 200)

    def test_usuario_staff_django_sem_perfil_acessa_criancas_ativas(self):
        usuario = User.objects.create_user(username='staff_django', password='senha123', is_staff=True)

        response = self.acessar_com_usuario(usuario)

        self.assertEqual(response.status_code, 200)

    def test_responsavel_nao_acessa_criancas_ativas(self):
        usuario = User.objects.create_user(username='responsavel', password='senha123')
        Perfil.objects.create(usuario=usuario, tipo_perfil='responsavel', ativo=True)

        response = self.acessar_com_usuario(usuario)

        self.assertEqual(response.status_code, 403)
