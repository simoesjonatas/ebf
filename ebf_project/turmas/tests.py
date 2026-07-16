from datetime import date
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Perfil
from criancas.models import Crianca
from .models import Turma


class TurmaCriancasExportTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='coord', password='senha123')
        Perfil.objects.create(usuario=self.usuario, tipo_perfil='coordenacao', ativo=True)
        self.client.login(username='coord', password='senha123')

        self.turma = Turma.objects.create(
            nome='Turma Azul',
            faixa_etaria='6 a 8 anos',
            sala_local='Sala 1',
            ativa=True,
        )
        self.outra_turma = Turma.objects.create(
            nome='Turma Verde',
            faixa_etaria='9 a 10 anos',
            sala_local='Sala 2',
            ativa=True,
        )
        self.crianca = Crianca.objects.create(
            nome_completo='Ana da Silva',
            data_nascimento=date(2018, 5, 10),
            turma=self.turma,
            ativa=True,
        )
        self.outra_crianca = Crianca.objects.create(
            nome_completo='Bia de Souza',
            data_nascimento=date(2017, 8, 20),
            turma=self.outra_turma,
            ativa=True,
        )

    def _textos_da_planilha(self, response):
        with ZipFile(BytesIO(response.content)) as arquivo:
            xml = arquivo.read('xl/sharedStrings.xml')
        root = ElementTree.fromstring(xml)
        namespace = {'xlsx': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        return [item.text for item in root.findall('.//xlsx:t', namespace)]

    def test_tela_criancas_da_turma_lista_apenas_criancas_da_turma(self):
        response = self.client.get(reverse('turmas:criancas', args=[self.turma.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana da Silva')
        self.assertNotContains(response, 'Bia de Souza')
        self.assertContains(response, reverse('turmas:exportar_criancas_excel', args=[self.turma.id]))

    def test_exportar_criancas_excel_da_turma(self):
        response = self.client.get(reverse('turmas:exportar_criancas_excel', args=[self.turma.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment; filename="criancas-turma-azul.xlsx"', response['Content-Disposition'])

        textos = self._textos_da_planilha(response)
        self.assertIn('Nome completo', textos)
        self.assertIn('Ana da Silva', textos)
        self.assertNotIn('Bia de Souza', textos)
