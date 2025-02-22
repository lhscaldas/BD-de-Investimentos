from django.db import models
from django.contrib.auth.models import User
from collections import defaultdict
import json

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
        db_table = "operacoes"
        verbose_name = "operação"
        verbose_name_plural = "operações"

    def atualizar_valores_e_rentabilidades(self):
        """Recalcula os valores do ativo e as rentabilidades simultaneamente e armazena tudo em um JSON.
        Estrutura do JSON: usuario -> ativo -> valores[mês], rentabilidades[mês]"""

        # Estrutura JSON para armazenar valores e rentabilidades organizados por usuário e ativo
        dados_financeiros = defaultdict(lambda: defaultdict(lambda: {"valor": defaultdict(float), "rentabilidade": defaultdict(float)}))

        usuario = self.usuario
        ativo = self.ativo

        operacoes = Operacao.objects.filter(ativo=ativo, usuario=usuario).order_by("data")

        # Dicionários para armazenar valores mensais
        atualizacoes_mensais = defaultdict(float)
        compras_vendas_mensais = defaultdict(float)
        rentabilidade_mensal = defaultdict(float)

        primeiro_mes = ativo.data_aquisicao.replace(day=1)

        # O primeiro mês recebe o valor inicial como atualização
        atualizacoes_mensais[primeiro_mes] = float(ativo.valor_inicial)

        # Coletar todas as atualizações, compras e vendas organizadas por mês
        for operacao in operacoes:
            mes_operacao = operacao.data.replace(day=1)

            if operacao.tipo == "atualizacao":
                atualizacoes_mensais[mes_operacao] = float(operacao.valor)  # Atualizações substituem o valor do mês
            elif operacao.tipo == "compra":
                compras_vendas_mensais[mes_operacao] += float(operacao.valor)
            elif operacao.tipo == "venda":
                compras_vendas_mensais[mes_operacao] -= float(operacao.valor)

        # Lista ordenada de meses para processamento
        meses_ordenados = sorted(set(atualizacoes_mensais.keys()) | set(compras_vendas_mensais.keys()))

        valores_por_mes = {}

        # Calcular valores mensais e rentabilidades simultaneamente
        for i in range(len(meses_ordenados)):
            mes_operacao = meses_ordenados[i]

            # Define o valor mensal considerando atualização + compras e vendas
            atualizacoes_mensais[mes_operacao] = atualizacoes_mensais.get(mes_operacao, 0)
            compras_vendas_mensais[mes_operacao] = compras_vendas_mensais.get(mes_operacao, 0)

            valores_por_mes[mes_operacao] = atualizacoes_mensais[mes_operacao] + compras_vendas_mensais[mes_operacao]

            # Calcular rentabilidade: valor do mês seguinte antes da atualização - valor do mês atual atualizado
            if i < len(meses_ordenados) - 1:
                mes_proximo = meses_ordenados[i + 1]
                rentabilidade_mensal[mes_operacao] = atualizacoes_mensais[mes_proximo] - valores_por_mes[mes_operacao]
            else:
                rentabilidade_mensal[mes_operacao] = 0.0  # Último mês recebe rentabilidade 0

            # Salvar valores e rentabilidades no JSON
            dados_financeiros[str(usuario.id)][str(ativo.id)]["valor"][mes_operacao.strftime("%Y-%m")] = valores_por_mes[mes_operacao]
            dados_financeiros[str(usuario.id)][str(ativo.id)]["rentabilidade"][mes_operacao.strftime("%Y-%m")] = rentabilidade_mensal[mes_operacao]

        # Salvar JSON no banco de dados ou em arquivo
        try:
            with open("dados_financeiros.json", "w", encoding="utf-8") as json_file:
                json.dump(dados_financeiros, json_file, indent=4, ensure_ascii=False)
            print("DEBUG: Dados financeiros salvos com sucesso")
        except Exception as e:
            print(f"DEBUG: Erro ao salvar JSON de dados financeiros: {e}")

        print("DEBUG: JSON gerado:", json.dumps(dados_financeiros, indent=4, ensure_ascii=False))






    def save(self, *args, **kwargs):
        """Salva a operação e atualiza os valores do ativo e rentabilidades."""
        super().save(*args, **kwargs)
        self.atualizar_valores_e_rentabilidades()

    def delete(self, *args, **kwargs):
        """Deleta a operação e recalcula os valores do ativo e rentabilidades."""
        super().delete(*args, **kwargs)
        self.atualizar_valores_e_rentabilidades()

    def __str__(self):
        return f"{self.tipo.capitalize()} - R$ {self.valor} ({self.ativo.nome})"
    
class ValorAtivo(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='valores_ativos')
    data = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "valores_ativo"
        verbose_name = "valor ativo"
        verbose_name_plural = "valores ativos"

    def __str__(self):
        return f"{self.ativo.nome} - {self.data}: R$ {self.valor}"
    

class RentabilidadeAtivo(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name='rentabilidades')
    data_referencia = models.DateField()
    rentabilidade_abs = models.DecimalField(max_digits=15, decimal_places=2)
    rentabilidade_perc = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "rentabilidade_ativo"
        verbose_name = "rentabilidade ativo"
        verbose_name_plural = "rentabilidades ativo"

    def __str__(self):
        return f"{self.ativo.nome} - {self.data_referencia}: {self.rentabilidade_perc}%"

        



