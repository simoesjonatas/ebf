from django.contrib import admin
from .models import Crianca, CriancaResponsavel


class CriancaResponsavelInline(admin.TabularInline):
    model = CriancaResponsavel
    extra = 1
    fields = ('responsavel', 'parentesco', 'pode_fazer_checkin', 'pode_fazer_checkout', 'responsavel_principal', 'ativo')


@admin.register(Crianca)
class CriancaAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'data_nascimento', 'get_idade', 'codigo_interno', 'turma', 'ativa')
    list_filter = ('ativa', 'turma', 'criado_em', 'autorizacao_imagem')
    search_fields = ('nome_completo', 'codigo_interno', 'token_qr')
    readonly_fields = ('token_qr', 'codigo_interno', 'criado_em', 'atualizado_em', 'get_idade')
    inlines = [CriancaResponsavelInline]
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome_completo', 'data_nascimento', 'get_idade', 'turma')
        }),
        ('Saúde e Segurança', {
            'fields': ('alergias', 'restricoes_alimentares', 'cuidados_especiais', 'observacoes')
        }),
        ('Autorização', {
            'fields': ('autorizacao_imagem', 'ativa')
        }),
        ('Identificação', {
            'fields': ('codigo_interno', 'token_qr')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def get_idade(self, obj):
        return f"{obj.get_idade()} anos"
    get_idade.short_description = 'Idade'


@admin.register(CriancaResponsavel)
class CriancaResponsavelAdmin(admin.ModelAdmin):
    list_display = ('crianca', 'responsavel', 'parentesco', 'pode_fazer_checkin', 'pode_fazer_checkout', 'ativo')
    list_filter = ('ativo', 'pode_fazer_checkin', 'pode_fazer_checkout', 'responsavel_principal')
    search_fields = ('crianca__nome_completo', 'responsavel__nome_completo')
