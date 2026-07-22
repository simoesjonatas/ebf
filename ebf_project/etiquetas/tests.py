from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Perfil
from criancas.models import Crianca
from presencas.models import PresencaDiaria
from turmas.models import Turma

from .models import Etiqueta


class EtiquetasLoteTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='recepcao', password='senha123')
        Perfil.objects.create(usuario=self.usuario, tipo_perfil='recepcao', ativo=True)
        self.client.force_login(self.usuario)
        self.turma = Turma.objects.create(
            nome='Turma Etiquetas',
            faixa_etaria='6 a 8 anos',
            sala_local='Sala 1',
            ativa=True,
        )

    def criar_etiqueta(self, nome, impressa=True):
        crianca = Crianca.objects.create(
            nome_completo=nome,
            data_nascimento=date(2018, 1, 1),
            turma=self.turma,
            ativa=True,
        )
        presenca = PresencaDiaria.objects.create(
            crianca=crianca,
            status='PRESENTE',
            horario_checkin=timezone.now(),
            usuario_checkin=self.usuario,
        )
        return Etiqueta.objects.create(
            presenca=presenca,
            crianca=crianca,
            usuario_geracao=self.usuario,
            impressa=impressa,
            data_impressao=timezone.now() if impressa else None,
        )

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_listagem_de_impressas_exibe_acao_para_voltar_pendentes(self):
        etiqueta = self.criar_etiqueta('Criança Impressa')

        response = self.client.get(reverse('etiquetas:listar_etiquetas_dia'), {'status': 'impressas'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('etiquetas:marcar_nao_impressas_lote'))
        self.assertContains(response, f'value="{etiqueta.id}"')
        self.assertContains(response, 'Marcar selecionadas como pendentes')

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_marcar_nao_impressas_lote_volta_somente_selecionadas_para_pendentes(self):
        selecionada = self.criar_etiqueta('Criança Selecionada')
        nao_selecionada = self.criar_etiqueta('Criança Não Selecionada')

        response = self.client.post(
            reverse('etiquetas:marcar_nao_impressas_lote'),
            {'etiquetas': [str(selecionada.id)]},
        )

        self.assertRedirects(response, f"{reverse('etiquetas:listar_etiquetas_dia')}?status=pendentes")
        selecionada.refresh_from_db()
        nao_selecionada.refresh_from_db()
        self.assertFalse(selecionada.impressa)
        self.assertIsNone(selecionada.data_impressao)
        self.assertTrue(nao_selecionada.impressa)
        self.assertIsNotNone(nao_selecionada.data_impressao)
