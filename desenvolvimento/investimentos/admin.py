from django.contrib import admin
from .models import Ativo, Operacao, ValorAtivo

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao')
    search_fields = ('usuario', 'nome', 'classe', 'subclasse', 'banco', 'data_aquisicao')

@admin.register(Operacao)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ativo', 'tipo', 'valor')
    search_fields = ('usuario', 'ativo', 'tipo')

@admin.register(ValorAtivo)
class ValorAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'data', 'valor')
    search_fields = ('ativo', 'data')