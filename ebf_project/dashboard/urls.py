from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('criancas/', views.criancas_ativas, name='criancas_ativas'),
    path('presentes/', views.criancas_presentes, name='criancas_presentes'),
    path('presentes/checkout/', views.checkout_manual, name='checkout_manual'),
    path('checkins/', views.criancas_checkins, name='criancas_checkins'),
    path('retiradas/', views.criancas_retiradas, name='criancas_retiradas'),
    path('alergias/', views.criancas_alergias, name='criancas_alergias'),
    path('presenca-por-dia/', views.presenca_por_dia, name='presenca_por_dia'),
    path('criancas-por-turma/', views.criancas_por_turma, name='criancas_por_turma'),
    path('criancas-com-restricoes/', views.criancas_com_restricoes, name='criancas_com_restricoes'),
    path('historico-checkin-checkout/', views.historico_checkin_checkout, name='historico_checkin_checkout'),
]
