from django.contrib import admin
from .models import Ativo, Operacao, ValorAtivo, RentabilidadeAtivo

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao')
    search_fields = ('usuario__username', 'nome', 'classe', 'subclasse', 'banco')

@admin.register(Operacao)
class OperacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ativo', 'tipo', 'valor')
    search_fields = ('usuario__username', 'ativo__nome', 'tipo')

@admin.register(ValorAtivo)
class ValorAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'data', 'valor')
    search_fields = ['ativo__nome']

@admin.register(RentabilidadeAtivo)
class RentabilidadeAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'data_referencia', 'rentabilidade_abs', 'rentabilidade_perc')
    search_fields = ('ativo__nome', 'data_referencia')