from django.urls import path
from . import views

app_name = 'etiquetas'

urlpatterns = [
    path('gerar/<uuid:presenca_id>/', views.gerar_etiqueta, name='gerar_etiqueta'),
    path('listar-dia/', views.listar_etiquetas_dia, name='listar_etiquetas_dia'),
    path('<uuid:etiqueta_id>/impressa/', views.marcar_impressa, name='marcar_impressa'),
]
