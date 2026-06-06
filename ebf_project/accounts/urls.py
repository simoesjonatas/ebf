from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import StyledPasswordResetForm, StyledSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_responsavel, name='register'),
    path('staff/', views.listar_staff, name='staff_list'),
    path('staff/register/', views.register_staff, name='staff_register'),
    path('staff/<uuid:perfil_id>/funcao/', views.alterar_funcao_staff, name='staff_role_update'),
    path('responsaveis/', views.listar_responsaveis, name='responsaveis_list'),
    path('responsaveis/<uuid:perfil_id>/funcao/', views.alterar_perfil_responsavel, name='responsavel_role_update'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path(
        'senha/esqueci/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            form_class=StyledPasswordResetForm,
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/auth/senha/esqueci/done/'
        ),
        name='password_reset'
    ),
    path(
        'senha/esqueci/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            form_class=StyledSetPasswordForm,
            success_url='/auth/senha/redefinir/concluido/'
        ),
        name='password_reset_confirm'
    ),
    path(
        'senha/redefinir/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.perfil_edit_view, name='perfil_edit'),
]
