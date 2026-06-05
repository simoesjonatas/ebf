from django.contrib import admin
from .models import Auditoria


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('acao', 'modelo', 'usuario', 'criado_em')
    list_filter = ('acao', 'modelo', 'criado_em')
    search_fields = ('usuario__username', 'objeto_id', 'descricao')
    readonly_fields = ('criado_em',)
