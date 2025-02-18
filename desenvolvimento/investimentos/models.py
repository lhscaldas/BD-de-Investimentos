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

    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            ValorAtivo.objects.get_or_create(ativo=self, data=self.data_aquisicao, defaults={'valor': self.valor_inicial})

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

    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            
            if self.tipo == 'atualizacao':
                valor = self.valor
            else:
                ultimo_valor = (ValorAtivo.objects.filter(ativo=self.ativo, data__lt=self.data)
                                .order_by('-data').first())
                ultimo_valor = ultimo_valor.valor if ultimo_valor else self.ativo.valor_inicial
                
                if self.tipo == 'compra':
                    valor = ultimo_valor + self.valor
                elif self.tipo == 'venda':
                    valor = ultimo_valor - self.valor

            ValorAtivo.objects.create(ativo=self.ativo, data=self.data, valor=valor)

    def __str__(self):
        return f"{self.tipo.capitalize()} - R$ {self.valor} ({self.ativo.nome})"
    

class ValorAtivo(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='valores')
    data = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "valores_ativo"
        verbose_name = "valor ativo"
        verbose_name_plural = "valores ativos"

    def __str__(self):
        return f"{self.ativo.nome} - {self.data}: R$ {self.valor}"
        



