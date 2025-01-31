from django.contrib import admin
from .models import Ativo, Operacao

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao')
    search_fields = ('usuario', 'nome', 'classe', 'subclasse', 'banco', 'data_aquisicao')

@admin.register(Operacao)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ativo', 'tipo', 'valor')
    search_fields = ('usuario', 'ativo', 'tipo')