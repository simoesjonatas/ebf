from django.urls import path
from . import views

app_name = 'responsaveis'

urlpatterns = [
    path('ativar/', views.ativar_responsavel, name='ativar'),
    path('dashboard/', views.dashboard_responsavel, name='dashboard'),
    path('minhas-criancas/', views.minhas_criancas, name='minhas_criancas'),
    path('qrcode/checkin/', views.gerar_qr_checkin_lote, name='gerar_qr_checkin_lote'),
    path('qrcode/checkout/', views.gerar_qr_checkout_lote, name='gerar_qr_checkout_lote'),
    path('crianca/<uuid:crianca_id>/', views.detalhe_crianca, name='detalhe_crianca'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
]
