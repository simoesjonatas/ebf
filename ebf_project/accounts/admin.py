from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Perfil


class PerfilInline(admin.StackedInline):
    model = Perfil
    fields = ('tipo_perfil', 'ativo')


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_perfil', 'ativo')
    list_filter = ('tipo_perfil', 'ativo')
    search_fields = ('usuario__username', 'usuario__email')
