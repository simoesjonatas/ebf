from django.urls import path
from . import views

app_name = 'criancas'

urlpatterns = [
    path('buscar/', views.buscar_criancas, name='buscar'),
    path('criar/', views.criar_crianca, name='criar'),
    path('<uuid:crianca_id>/staff/', views.detalhe_crianca_staff, name='detalhe_staff'),
    path('<uuid:crianca_id>/editar/', views.editar_crianca, name='editar'),
    path('<uuid:crianca_id>/adicionar-responsavel/', views.adicionar_responsavel, name='adicionar_responsavel'),
    path('responsavel/<uuid:vinculo_id>/editar/', views.editar_responsavel, name='editar_responsavel'),
    path('responsavel/<uuid:vinculo_id>/revogar/', views.revogar_responsavel, name='revogar_responsavel'),
]
