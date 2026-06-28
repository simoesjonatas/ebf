from django.urls import path
from . import views

app_name = 'turmas'

urlpatterns = [
    path('', views.listar_turmas, name='listar'),
    path('criar/', views.criar_turma, name='criar'),
    path('<uuid:turma_id>/editar/', views.editar_turma, name='editar'),
    path('<uuid:turma_id>/alternar/', views.alternar_turma, name='alternar'),
    path('sem-turma/', views.criancas_sem_turma, name='sem_turma'),
    path('sem-turma/alocar-automatico/', views.alocar_automatico, name='alocar_automatico'),
    path('sem-turma/alocar-manual/', views.alocar_manual, name='alocar_manual'),
]
