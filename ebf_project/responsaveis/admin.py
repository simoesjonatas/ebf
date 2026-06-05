from django.contrib import admin
from .models import Responsavel


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'usuario', 'telefone', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em', 'autorizacao_imagem')
    search_fields = ('nome_completo', 'usuario__email', 'telefone', 'documento')
    readonly_fields = ('token_qr', 'criado_em', 'atualizado_em')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('usuario', 'nome_completo', 'telefone', 'documento')
        }),
        ('Autorização', {
            'fields': ('autorizacao_imagem', 'ativo')
        }),
        ('Segurança', {
            'fields': ('token_qr',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
