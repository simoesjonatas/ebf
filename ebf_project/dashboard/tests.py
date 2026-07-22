from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Perfil
from criancas.models import Crianca
from presencas.models import PresencaDiaria
from turmas.models import Turma


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

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_criancas_ativas_com_paginacao_nao_gera_erro_500(self):
        usuario = User.objects.create_user(username='coord_paginacao', password='senha123')
        Perfil.objects.create(usuario=usuario, tipo_perfil='coordenacao', ativo=True)
        turma = Turma.objects.create(
            nome='Turma Paginada',
            faixa_etaria='6 a 8 anos',
            sala_local='Sala 1',
            ativa=True,
        )
        for indice in range(25):
            Crianca.objects.create(
                nome_completo=f'Criança {indice:02d}',
                data_nascimento=date(2018, 1, 1),
                turma=turma,
                ativa=True,
            )

        primeira_pagina = self.acessar_com_usuario(usuario)
        ultima_pagina = self.client.get(reverse('dashboard:criancas_ativas'), {'page': 2})

        self.assertEqual(primeira_pagina.status_code, 200)
        self.assertEqual(ultima_pagina.status_code, 200)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_criancas_presentes_com_paginacao_nao_gera_erro_500(self):
        usuario = User.objects.create_user(username='coord_presentes', password='senha123')
        Perfil.objects.create(usuario=usuario, tipo_perfil='coordenacao', ativo=True)
        turma = Turma.objects.create(
            nome='Turma Presentes',
            faixa_etaria='6 a 8 anos',
            sala_local='Sala 2',
            ativa=True,
        )
        for indice in range(25):
            crianca = Crianca.objects.create(
                nome_completo=f'Criança Presente {indice:02d}',
                data_nascimento=date(2018, 1, 1),
                turma=turma,
                ativa=True,
            )
            PresencaDiaria.objects.create(
                crianca=crianca,
                status='PRESENTE',
                horario_checkin=timezone.now(),
                usuario_checkin=usuario,
            )

        self.client.force_login(usuario)
        primeira_pagina = self.client.get(reverse('dashboard:criancas_presentes'))
        ultima_pagina = self.client.get(reverse('dashboard:criancas_presentes'), {'page': 2})

        self.assertEqual(primeira_pagina.status_code, 200)
        self.assertEqual(ultima_pagina.status_code, 200)
