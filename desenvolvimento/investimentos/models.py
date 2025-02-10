from django.db import models
from django.contrib.auth.models import User

CLASSES_ATIVO = [
    ('Renda Fixa', 'Renda Fixa'),
    ('Renda Variável', 'Renda Variável'),
]

SUBCLASSES_POR_CLASSE = {
    'Renda Fixa': ['CDB', 'Tesouro Direto', 'Fundo de Renda Fixa'],
    'Renda Variável': ['Ações', 'Fundos de Ações', 'Fundos Multimercado', 'FII', 'Criptomoeda', 'Fundos no Exterior'],
}

# Gerar SUBCLASSES automaticamente a partir de SUBCLASSES_POR_CLASSE
SUBCLASSES = [(subclasse, subclasse) for _, sub_classes in SUBCLASSES_POR_CLASSE.items() for subclasse in sub_classes]

class Ativo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    nome = models.CharField(max_length=100, verbose_name="Nome do Ativo")
    classe = models.CharField(max_length=20, choices=CLASSES_ATIVO, verbose_name="Classe do Ativo")
    subclasse = models.CharField(max_length=50, choices=SUBCLASSES, verbose_name="Subclasse do Ativo")
    banco = models.CharField(max_length=50, verbose_name="Banco")
    valor_inicial = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Inicial")
    data_aquisicao = models.DateField(verbose_name="Data de Aquisição")
    observacoes = models.TextField(blank=True, null=True, default="", verbose_name="Observações")

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
    

class RentabilidadeHistorica(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name="historico_rentabilidade")
    data_referencia = models.DateField()  # Representa o mês da rentabilidade (exemplo: 2024-01-01 para janeiro/2024)
    
    rentabilidade_abs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rentabilidade_perc = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('ativo', 'data_referencia')  # Garante que um ativo tenha apenas um registro por mês
        ordering = ['data_referencia']

    def __str__(self):
        return f"{self.ativo.nome} - {self.data_referencia.strftime('%Y-%m')}: {self.rentabilidade_perc}%"


