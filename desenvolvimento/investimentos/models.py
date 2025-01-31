from django.db import models
from django.contrib.auth.models import User

class Ativo(models.Model):
    CLASSES_ATIVO = [
        ('Renda Fixa', 'Renda Fixa'),
        ('Renda Variável', 'Renda Variável'),
    ]

    SUBCLASSES = [
        #'Renda Fixa'
        ('CDB', 'CDB'),
        ('Tesouro Direto', 'Tesouro Direto'),
        ('Fundo de Renda Fixa', 'Fundo de Renda Fixa'),
        #'Renda Variável'
        ('Ações', 'Ações'),
        ('FII', 'FII'),
        ('Criptomoeda', 'Criptomoeda'),
        ('Fundos no Exterior', 'Fundos no Exterior'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    nome = models.CharField(max_length=100, verbose_name="Nome do Ativo")
    classe = models.CharField(max_length=20, choices=CLASSES_ATIVO, verbose_name="Classe do Ativo")
    subclasse = models.CharField(max_length=50, choices=SUBCLASSES, verbose_name="Subclasse do Ativo")
    banco = models.CharField(max_length=50, verbose_name="Banco")
    valor_inicial = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Inicial")
    data_aquisicao = models.DateField(verbose_name="Data de Aquisição")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        db_table = "ativos"  # Define explicitamente o nome da tabela
        verbose_name = "ativos"  # Nome singular para o admin
        verbose_name_plural = "ativos"  # Nome plural para o admin

    def __str__(self):
        return f"{self.nome}"

class Operacao(models.Model):
    TIPO_OPERACAO = [
        ('compra', 'Compra'),
        ('venda', 'Venda'),
        ('atualizacao', 'Atualização'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário", null=True)
    tipo = models.CharField(max_length=15, choices=TIPO_OPERACAO)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data = models.DateField()
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='operacoes')

    class Meta:
        db_table = "operacoes"  # Define explicitamente o nome da tabela
        verbose_name = "operação"  # Nome singular para o admin
        verbose_name_plural = "operações"  # Nome plural para o admin

    def __str__(self):
        return f"{self.tipo.capitalize()} - R$ {self.valor} ({self.ativo.nome})"


