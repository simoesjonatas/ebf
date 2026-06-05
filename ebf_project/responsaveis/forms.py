from django import forms
from .models import Responsavel


class ResponsavelForm(forms.ModelForm):
    autorizacao_imagem = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Responsavel
        fields = ('nome_completo', 'telefone', 'documento', 'autorizacao_imagem')
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not (self.instance and self.instance.pk):
            self.fields['autorizacao_imagem'].initial = True

    def clean_documento(self):
        return self.cleaned_data.get('documento') or None
