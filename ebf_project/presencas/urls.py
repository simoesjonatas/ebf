from django.urls import path
from . import views

app_name = 'presencas'

urlpatterns = [
    path('checkin/qr/', views.leitura_qr_checkin, name='leitura_qr_checkin'),
    path('checkin/processar/', views.processar_qr_checkin, name='processar_qr_checkin'),
    path('checkin/crianca/<uuid:crianca_id>/', views.checkin_crianca, name='checkin_crianca'),
    path('checkin/responsavel/<uuid:responsavel_id>/', views.checkin_responsavel, name='checkin_responsavel'),
    path('checkin/lote/<uuid:lote_id>/', views.checkin_lote, name='checkin_lote'),
    
    path('checkout/qr/', views.leitura_qr_checkout, name='leitura_qr_checkout'),
    path('checkout/processar/', views.processar_qr_checkout, name='processar_qr_checkout'),
    path('checkout/responsavel/<uuid:responsavel_id>/', views.checkout_responsavel, name='checkout_responsavel'),
    path('checkout/presenca/<uuid:presenca_id>/', views.checkout_presenca, name='checkout_presenca'),
    path('checkout/lote/<uuid:lote_id>/', views.checkout_lote, name='checkout_lote'),
]
