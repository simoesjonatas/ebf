from django import forms
from .models import PresencaDiaria


class CheckinForm(forms.Form):
    criancas = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label='Selecione as crianças',
        required=True
    )

    def __init__(self, criancas_queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if criancas_queryset:
            self.fields['criancas'].queryset = criancas_queryset


class CheckoutForm(forms.Form):
    criancas = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label='Selecione as crianças a retirar',
        required=True
    )
    observacao = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Observação (opcional)'
    )

    def __init__(self, criancas_queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if criancas_queryset:
            self.fields['criancas'].queryset = criancas_queryset


class QRCodeLoteCriancasForm(forms.Form):
    criancas = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label='Selecione as crianças',
        required=True
    )

    def __init__(self, criancas_queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if criancas_queryset is not None:
            self.fields['criancas'].queryset = criancas_queryset
