from django.contrib import admin
from .models import Ativo, Operacao

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao')
    search_fields = ('nome', 'banco', 'classe', 'subclasse')

@admin.register(Operacao)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'valor', 'ativo')
    search_fields = ('tipo', 'ativo')