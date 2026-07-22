from django.urls import path
from . import views

app_name = 'etiquetas'

urlpatterns = [
    path('gerar/<uuid:presenca_id>/', views.gerar_etiqueta, name='gerar_etiqueta'),
    path('listar-dia/', views.listar_etiquetas_dia, name='listar_etiquetas_dia'),
    path('imprimir-lote/', views.imprimir_lote, name='imprimir_lote'),
    path('marcar-impressas-lote/', views.marcar_impressas_lote, name='marcar_impressas_lote'),
    path('marcar-nao-impressas-lote/', views.marcar_nao_impressas_lote, name='marcar_nao_impressas_lote'),
    path('<uuid:etiqueta_id>/impressa/', views.marcar_impressa, name='marcar_impressa'),
]
