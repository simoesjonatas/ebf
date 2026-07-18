from django import forms
import re
from core.utils import comprimir_imagem
from .models import Crianca, CriancaResponsavel
from responsaveis.models import Responsavel
from turmas.models import Turma

PARENTESCO_CHOICES = [
    ('Pai', 'Pai'),
    ('Mãe', 'Mãe'),
    ('Avô', 'Avô'),
    ('Avó', 'Avó'),
    ('Tio', 'Tio'),
    ('Tia', 'Tia'),
    ('Irmão', 'Irmão'),
    ('Irmã', 'Irmã'),
    ('Padrasto', 'Padrasto'),
    ('Madrasta', 'Madrasta'),
    ('Tutor legal', 'Tutor legal'),
    ('Outro', 'Outro'),
]


class CriancaForm(forms.ModelForm):
    foto = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Envie uma foto tipo 3x4, de frente e bem iluminada.'
    )
    autorizacao_imagem = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    # Campo extra (não é do modelo Crianca): usado ao criar para registrar o
    # parentesco do responsável que está cadastrando.
    parentesco = forms.ChoiceField(
        choices=[('', 'Selecione...')] + PARENTESCO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='O que você é para a criança?'
    )

    class Meta:
        model = Crianca
        fields = ('nome_completo', 'data_nascimento', 'foto', 'alergias', 'restricoes_alimentares', 'cuidados_especiais', 'observacoes', 'autorizacao_imagem')
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Amendoim, Lactose'}),
            'restricoes_alimentares': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Vegetariano, Sem açúcar'}),
            'cuidados_especiais': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Pressão alta, Asma, Problemas auditivos'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Outras observações importantes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # PK é UUID com default, então instance.pk já vem preenchido mesmo em
        # objetos novos. O sinal confiável de "edição" é _state.adding=False.
        editando = self.instance and not self.instance._state.adding
        if editando:
            self.fields['foto'].required = False
            return
        self.fields['autorizacao_imagem'].initial = True
        # No cadastro, o parentesco é obrigatório
        self.fields['parentesco'].required = True

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if not foto:
            if self.instance and self.instance.pk and self.instance.foto:
                return foto
            raise forms.ValidationError('A foto 3x4 da criança é obrigatória.')

        content_type = getattr(foto, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise forms.ValidationError('Envie um arquivo de imagem válido.')

        # Limite de entrada generoso: aceita fotos de celular sem atrito. O
        # arquivo é comprimido logo abaixo, então o que será salvo em disco
        # fica em torno de ~100-150 KB independentemente do tamanho enviado.
        if foto.size > 8 * 1024 * 1024:
            raise forms.ValidationError('A foto deve ter no máximo 8 MB.')

        # Se nenhuma imagem nova foi enviada (edição mantendo a atual), não há
        # o que comprimir.
        if not hasattr(foto, 'read'):
            return foto

        return comprimir_imagem(foto)

    def _turma_por_idade(self, idade):
        turmas = Turma.objects.filter(ativa=True)
        for turma in turmas:
            texto = f'{turma.nome} {turma.faixa_etaria}'
            numeros = [int(n) for n in re.findall(r'\d+', texto)]
            if len(numeros) >= 2 and numeros[0] <= idade <= numeros[1]:
                return turma
            if len(numeros) == 1 and numeros[0] == idade:
                return turma
        return None

    def save(self, commit=True):
        crianca = super().save(commit=False)
        crianca.turma = self._turma_por_idade(crianca.get_idade())
        if commit:
            crianca.save()
            self.save_m2m()
        return crianca


class CriancaResponsavelForm(forms.ModelForm):
    identificador_responsavel = forms.CharField(
        label='Responsável',
        max_length=255,
        help_text='Informe o e-mail, telefone ou documento do responsável já cadastrado.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-mail, telefone ou documento'
        })
    )
    parentesco = forms.ChoiceField(
        choices=PARENTESCO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CriancaResponsavel
        fields = ('identificador_responsavel', 'parentesco', 'pode_fazer_checkin', 'pode_fazer_checkout', 'pode_editar_dados', 'responsavel_principal')
        widgets = {
            'pode_fazer_checkin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_fazer_checkout': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_editar_dados': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsavel_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, crianca=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.crianca = crianca

    def clean_identificador_responsavel(self):
        identificador = self.cleaned_data['identificador_responsavel'].strip()
        responsavel = Responsavel.objects.filter(usuario__email__iexact=identificador, ativo=True).first()

        if not responsavel:
            responsavel = Responsavel.objects.filter(documento__iexact=identificador, ativo=True).first()

        if not responsavel:
            telefone_normalizado = re.sub(r'\D', '', identificador)
            if telefone_normalizado:
                for candidato in Responsavel.objects.filter(ativo=True):
                    if re.sub(r'\D', '', candidato.telefone or '') == telefone_normalizado:
                        responsavel = candidato
                        break

        if not responsavel:
            raise forms.ValidationError('Responsável não encontrado. Cadastre o adulto primeiro ou confira o e-mail/telefone/documento.')

        if self.crianca and CriancaResponsavel.objects.filter(crianca=self.crianca, responsavel=responsavel, ativo=True).exists():
            raise forms.ValidationError('Este responsável já está ativo para esta criança.')

        self.cleaned_data['responsavel_obj'] = responsavel
        return identificador

    def save(self, commit=True):
        vinculo = super().save(commit=False)
        vinculo.responsavel = self.cleaned_data['responsavel_obj']
        if commit:
            vinculo.save()
        return vinculo


class CriancaResponsavelPermissoesForm(forms.ModelForm):
    parentesco = forms.ChoiceField(
        choices=PARENTESCO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CriancaResponsavel
        fields = ('parentesco', 'pode_fazer_checkin', 'pode_fazer_checkout', 'pode_editar_dados', 'responsavel_principal', 'ativo')
        widgets = {
            'pode_fazer_checkin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_fazer_checkout': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_editar_dados': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsavel_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
