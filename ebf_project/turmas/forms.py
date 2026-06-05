from django import forms
from .models import Turma, Professor


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ('nome', 'faixa_etaria', 'sala_local', 'ativa')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Crianças 4-5 anos'}),
            'faixa_etaria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 4-5 anos'}),
            'sala_local': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Sala 101'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ('nome_completo', 'telefone', 'funcao', 'turmas')
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Professor, Assistente'}),
            'turmas': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
