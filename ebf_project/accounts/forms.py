from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm
from core.utils import validar_telefone
from .models import Perfil

STAFF_PROFILE_CHOICES = [
    ('recepcao', 'Recepção'),
    ('checkin', 'Check-in'),
    ('checkout', 'Checkout'),
    ('professor', 'Professor'),
    ('coordenacao', 'Coordenação'),
    ('admin', 'Admin'),
]


class ResponsavelRegisterForm(UserCreationForm):
    nome_completo = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'})
    )
    aceite_termos = forms.BooleanField(
        required=True,
        label='Li e aceito os Termos de Uso e a Política de Privacidade/LGPD',
        error_messages={'required': 'Você precisa aceitar os Termos de Uso para criar a conta.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('email', 'nome_completo', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        # Normaliza para minúsculas: o e-mail é gravado sempre em lowercase,
        # garantindo que o login funcione independentemente do case digitado.
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nome_completo'].split()[0]
        user.last_name = ' '.join(self.cleaned_data['nome_completo'].split()[1:])
        if commit:
            user.save()
            from responsaveis.models import Responsavel
            Responsavel.objects.create(
                usuario=user,
                nome_completo=self.cleaned_data['nome_completo']
            )
            Perfil.objects.create(usuario=user, tipo_perfil='responsavel')
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}))

    def clean_email(self):
        # Aceita o e-mail em qualquer combinação de maiúsculas/minúsculas e o
        # normaliza para lowercase antes da busca no login.
        return (self.cleaned_data.get('email') or '').strip().lower()


class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'seuemail@exemplo.com',
            'autocomplete': 'email',
        })
    )

    def clean_email(self):
        # Normaliza para minúsculas; a busca por usuários (get_users) já é
        # case-insensitive no Django, então a redefinição encontra a conta.
        return (self.cleaned_data.get('email') or '').strip().lower()


class StyledSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='Nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nova senha',
            'autocomplete': 'new-password',
        }),
    )
    new_password2 = forms.CharField(
        label='Confirmar nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a nova senha',
            'autocomplete': 'new-password',
        }),
    )


class StaffRegisterForm(UserCreationForm):
    nome_completo = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail de acesso'})
    )
    tipo_perfil = forms.ChoiceField(
        choices=STAFF_PROFILE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Função operacional'
    )
    tambem_responsavel = forms.BooleanField(
        required=False,
        label='Este staff também é responsável por criança',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    telefone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control js-telefone', 'placeholder': '(11) 99999-9999', 'maxlength': '15', 'inputmode': 'tel'})
    )
    documento = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento opcional'})
    )
    aceite_termos = forms.BooleanField(
        required=True,
        label='Confirmo que este usuário foi informado sobre os Termos de Uso e a Política de Privacidade/LGPD',
        error_messages={'required': 'Confirme o aceite dos Termos de Uso para criar o acesso.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('email', 'nome_completo', 'tipo_perfil', 'tambem_responsavel', 'telefone', 'documento', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        # Normaliza para minúsculas: o e-mail é gravado sempre em lowercase,
        # garantindo que o login funcione independentemente do case digitado.
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def clean_telefone(self):
        return validar_telefone(self.cleaned_data.get('telefone'))

    def save(self, commit=True):
        user = super().save(commit=False)
        nome = self.cleaned_data['nome_completo']
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = nome.split()[0]
        user.last_name = ' '.join(nome.split()[1:])
        if commit:
            user.save()
            Perfil.objects.create(usuario=user, tipo_perfil=self.cleaned_data['tipo_perfil'])
            if self.cleaned_data.get('tambem_responsavel'):
                from responsaveis.models import Responsavel
                Responsavel.objects.create(
                    usuario=user,
                    nome_completo=nome,
                    telefone=self.cleaned_data.get('telefone', ''),
                    documento=self.cleaned_data.get('documento') or None
                )
        return user


class StaffRoleForm(forms.ModelForm):
    tipo_perfil = forms.ChoiceField(
        choices=STAFF_PROFILE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Função'
    )

    class Meta:
        model = Perfil
        fields = ('tipo_perfil',)


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ('tipo_perfil', 'ativo')
        widgets = {
            'tipo_perfil': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
