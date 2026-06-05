from django.contrib import admin
from .models import PresencaDiaria, QRCodeOperacaoLote


@admin.register(PresencaDiaria)
class PresencaDiariaAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'data', 'status', 'horario_checkin', 'checkout_token_expira_em', 'horario_checkout', 'responsavel_checkout')
    list_filter = ('status', 'data', 'crianca__turma')
    search_fields = ('crianca__nome_completo', 'crianca__codigo_interno')
    readonly_fields = ('checkout_token', 'checkout_token_expira_em', 'criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Criança', {
            'fields': ('crianca', 'data', 'status')
        }),
        ('Check-in', {
            'fields': ('horario_checkin', 'usuario_checkin', 'responsavel_checkin', 'checkout_token', 'checkout_token_expira_em')
        }),
        ('Check-out', {
            'fields': ('horario_checkout', 'usuario_checkout', 'responsavel_checkout')
        }),
        ('Observações', {
            'fields': ('observacao',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['crianca', 'data']
        return self.readonly_fields


@admin.register(QRCodeOperacaoLote)
class QRCodeOperacaoLoteAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'responsavel', 'expira_em', 'usado_em', 'ativo', 'criado_em')
    list_filter = ('tipo', 'ativo', 'expira_em', 'usado_em')
    search_fields = ('responsavel__nome_completo', 'responsavel__usuario__email', 'token')
    readonly_fields = ('token', 'criado_em', 'atualizado_em')
    filter_horizontal = ('criancas',)
