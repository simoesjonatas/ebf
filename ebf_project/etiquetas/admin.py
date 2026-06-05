from django.contrib import admin
from .models import Etiqueta


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'presenca', 'impressa', 'data_geracao', 'usuario_geracao')
    list_filter = ('impressa', 'data_geracao', 'crianca__turma')
    search_fields = ('crianca__nome_completo', 'crianca__codigo_interno')
    readonly_fields = ('data_geracao', 'criado_em', 'atualizado_em')
