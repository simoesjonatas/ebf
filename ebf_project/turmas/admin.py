from django.contrib import admin
from .models import Turma, Professor


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'faixa_etaria', 'sala_local', 'ativa')
    list_filter = ('ativa', 'criado_em')
    search_fields = ('nome', 'sala_local')
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'faixa_etaria', 'sala_local', 'ativa')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'usuario', 'funcao', 'ativo', 'criado_em')
    list_filter = ('ativo', 'funcao', 'criado_em')
    search_fields = ('nome_completo', 'usuario__email', 'telefone')
    filter_horizontal = ('turmas',)
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('usuario', 'nome_completo', 'telefone', 'funcao')
        }),
        ('Turmas', {
            'fields': ('turmas',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
