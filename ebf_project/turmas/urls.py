from django.urls import path
from . import views

app_name = 'turmas'

urlpatterns = [
    path('', views.listar_turmas, name='listar'),
    path('criar/', views.criar_turma, name='criar'),
    path('<uuid:turma_id>/editar/', views.editar_turma, name='editar'),
    path('<uuid:turma_id>/alternar/', views.alternar_turma, name='alternar'),
]
