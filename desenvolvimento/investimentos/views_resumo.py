from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao, ValorAtivo
from datetime import timedelta, datetime
from django.db.models import Sum
from django.utils.timezone import now
from collections import defaultdict
import json
import requests
import numpy as np
import yfinance as yf
from dateutil.relativedelta import relativedelta
import pandas as pd
import os

CACHE_FILE = "indices_cache.json"

def carregar_cache():
    """Carrega o cache do arquivo, se existir."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def salvar_cache(dados):
    """Salva os dados no arquivo de cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(dados, f)

def obter_indices_historicos(data_inicio, data_fim):
    try:
        # Carregar cache
        cache = carregar_cache()
        hoje = datetime.today().strftime("%Y-%m-%d")

        # Se já buscamos os dados hoje, retornamos do cache
        if cache.get("data_atualizacao") == hoje:
            print("Retornando dados do cache.")
            return cache.get("indices", {})

        # Converter datas para o formato YYYY-MM-DD
        data_inicio_iso = datetime.strptime(data_inicio, "%d/%m/%Y").strftime("%Y-%m-%d")
        data_fim_iso = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m-%d")

        # Baixar os dados do IBOVESPA via Yahoo Finance
        ibov = yf.Ticker("^BVSP")
        historico_ibov = ibov.history(start=data_inicio_iso, end=data_fim_iso, interval="1mo")

        ibov_mensal = {}
        if not historico_ibov.empty:
            ibov_por_mes = defaultdict(list)
            for data, row in historico_ibov.iterrows():
                mes_ano = data.strftime("%Y-%m")
                ibov_por_mes[mes_ano].append(row["Close"])

            meses_ordenados = sorted(ibov_por_mes.keys())
            for i in range(1, len(meses_ordenados)):
                mes_atual = meses_ordenados[i]
                mes_anterior = meses_ordenados[i - 1]

                valor_atual = ibov_por_mes[mes_atual][0]
                valor_anterior = ibov_por_mes[mes_anterior][0]

                if valor_anterior > 0:
                    ibov_mensal[mes_atual] = ((valor_atual / valor_anterior) - 1) * 100  # Percentual

        # Baixar os dados do CDI via API do Banco Central
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_inicio}&dataFinal={data_fim}"
        resposta = requests.get(url)
        cdi_mensal = {}

        if resposta.status_code == 200:
            dados_cdi = resposta.json()
            cdi_por_mes = defaultdict(list)
            for entrada in dados_cdi:
                data = datetime.strptime(entrada["data"], "%d/%m/%Y").date()
                mes_ano = data.strftime("%Y-%m")
                cdi_por_mes[mes_ano].append(float(entrada["valor"]) / 100)  # Convertendo para decimal

            cdi_mensal = {mes: (np.prod([1 + taxa for taxa in valores]) - 1) * 100 for mes, valores in cdi_por_mes.items()}

        # Salvar no cache
        indices = {
            "IBOVESPA": ibov_mensal,
            "CDI": cdi_mensal
        }
        cache = {
            "data_atualizacao": hoje,
            "indices": indices
        }
        salvar_cache(cache)

        return indices

    except Exception as e:
        print(f"Erro ao obter índices históricos: {e}")
        return {}


class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"

    def get_queryset(self):
        """Retorna os ativos do usuário e calcula sua rentabilidade."""
        ativos = Ativo.objects.filter(usuario=self.request.user)

        # Lista de campos que podem ser filtrados
        filtros_validos = ['nome', 'classe', 'subclasse', 'banco']
        
        # Aplica os filtros somente se houver valores preenchidos
        filtros = {f"{k}__icontains": v for k, v in self.request.GET.items() if v and k in filtros_validos}

        if filtros:
            ativos = ativos.filter(**filtros)

        for ativo in ativos:
            self.calcular_valor_atualizado(ativo)
            self.calcular_rentabilidade(ativo)

        return ativos

    def calcular_valor_atualizado(self, ativo):
        """Calcula o valor atualizado do ativo baseado nas operações de compra, venda e atualização."""
        ultima_atualizacao = (
            Operacao.objects.filter(ativo=ativo, tipo="atualizacao")
            .order_by("-data")
            .first()
        )

        ativo.ultima_atualizacao = ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao
        ativo.valor_atualizado = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

        compras = self.obter_soma_operacoes(ativo, "compra", ativo.ultima_atualizacao)
        vendas = self.obter_soma_operacoes(ativo, "venda", ativo.ultima_atualizacao)

        ativo.valor_atualizado += compras - vendas

    def obter_soma_operacoes(self, ativo, tipo, data_inicial):
        """Retorna a soma das operações do tipo especificado após uma determinada data."""
        if data_inicial is None:
            return 0  # Se não há data inicial, não deve fazer filtragem

        return (
            Operacao.objects.filter(ativo=ativo, tipo=tipo, data__gt=data_inicial)
            .aggregate(total=Sum("valor"))["total"] or 0
        )


    def obter_valor_referencia(self, ativo, anos):
        """Obtém o valor do ativo há `anos` anos atrás, considerando a última atualização disponível."""
        data_limite = ativo.ultima_atualizacao - timedelta(days=anos * 365)
        operacao_referencia = (
            Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_limite)
            .order_by("-data")
            .first()
        )
        return (
            operacao_referencia.valor if operacao_referencia else ativo.valor_inicial,
            operacao_referencia.data if operacao_referencia else ativo.data_aquisicao,
        )

    def calcular_rentabilidade(self, ativo):
        """Calcula a rentabilidade absoluta e percentual do ativo."""

        # Obtém os valores de referência corretamente ajustados com compras e vendas
        valor_1m = self.get_valor_ajustado(ativo, ativo.ultima_atualizacao - timedelta(days=30))
        valor_1a = self.get_valor_ajustado(ativo, ativo.ultima_atualizacao - timedelta(days=365))
        valor_inicial_ajustado = self.get_valor_ajustado(ativo, ativo.data_aquisicao)

        # Calcula a rentabilidade absoluta
        ativo.rentabilidade_1m_abs = ativo.valor_atualizado - valor_1m
        ativo.rentabilidade_1a_abs = ativo.valor_atualizado - valor_1a
        ativo.rentabilidade_total_abs = ativo.valor_atualizado - valor_inicial_ajustado

        # Calcula a rentabilidade percentual, evitando divisões por zero
        ativo.rentabilidade_1m_perc = ((ativo.rentabilidade_1m_abs / valor_1m) * 100) if valor_1m else 0
        ativo.rentabilidade_1a_perc = ((ativo.rentabilidade_1a_abs / valor_1a) * 100) if valor_1a else 0
        ativo.rentabilidade_total_perc = ((ativo.rentabilidade_total_abs / valor_inicial_ajustado) * 100) if valor_inicial_ajustado else 0


    def ajustar_valor_com_operacoes(self, ativo, valor_base, data_base, ultima_data):
        """Ajusta o valor do ativo considerando operações de compra e venda entre um período."""
        compras = self.obter_soma_operacoes_periodo(ativo, "compra", data_base, ultima_data)
        vendas = self.obter_soma_operacoes_periodo(ativo, "venda", data_base, ultima_data)
        return valor_base + compras - vendas

    def obter_soma_operacoes_periodo(self, ativo, tipo, data_inicial, data_final):
        """Retorna a soma das operações do tipo especificado dentro de um intervalo de tempo."""
        return (
            Operacao.objects.filter(ativo=ativo, tipo=tipo, data__gt=data_inicial, data__lte=data_final)
            .aggregate(total=Sum("valor"))["total"] or 0
        )

    def definir_contexto_vazio(self, context):
        """Define valores padrão para quando não há ativos."""
        context.update({
            "patrimonio_total": 0,
            "rentabilidade_abs_1m": 0,
            "rentabilidade_abs_1a": 0,
            "rentabilidade_abs_total": 0,
            "rentabilidade_perc_1m": 0,
            "rentabilidade_perc_1a": 0,
            "rentabilidade_perc_total": 0
        })
        return context
    
    def get_valor_ajustado(self, ativo, data_ref):
        """Obtém o valor do ativo ajustado por compras e vendas até uma determinada data."""
        if data_ref is None:
            return ativo.valor_inicial  # Se não houver data de referência, retorna o valor inicial.

        # Obtém a última atualização antes da data de referência
        ultima_atualizacao = (
            Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_ref)
            .order_by("-data")
            .first()
        )
        valor_base = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

        # Ajusta com compras e vendas no período correto
        compras_ate_data = (
            Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao, data__lte=data_ref)
            .aggregate(total=Sum("valor"))["total"] or 0
        )
        vendas_ate_data = (
            Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao, data__lte=data_ref)
            .aggregate(total=Sum("valor"))["total"] or 0
        )

        return valor_base + compras_ate_data - vendas_ate_data


    def calcular_rentabilidade_global(self, context, ativos):
        """Calcula a rentabilidade global da carteira baseada no método original."""
        patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

        datas_atualizacoes = [ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao]
        if datas_atualizacoes:
            data_atual = max(datas_atualizacoes)
        else:
            datas_aquisicao = [ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao]
            data_atual = min(datas_aquisicao) if datas_aquisicao else None

        if not data_atual:
            return self.definir_contexto_vazio(context)

        data_1m = data_atual - timedelta(days=30)
        data_1a = data_atual - timedelta(days=365)

        valor_inicial_ajustado_total = 0
        valor_1m_ajustado_total = 0
        valor_1a_ajustado_total = 0

        for ativo in ativos:
            compras_total = (
                Operacao.objects.filter(ativo=ativo, tipo="compra")
                .aggregate(total=Sum("valor"))["total"] or 0
            )
            vendas_total = (
                Operacao.objects.filter(ativo=ativo, tipo="venda")
                .aggregate(total=Sum("valor"))["total"] or 0
            )
            valor_inicial_ajustado = ativo.valor_inicial + compras_total - vendas_total
            valor_inicial_ajustado_total += valor_inicial_ajustado

            valor_1m_ajustado = self.get_valor_ajustado(ativo, data_1m)
            valor_1a_ajustado = self.get_valor_ajustado(ativo, data_1a)

            valor_1m_ajustado_total += valor_1m_ajustado
            valor_1a_ajustado_total += valor_1a_ajustado

        rentabilidade_abs_1m = patrimonio_total - valor_1m_ajustado_total
        rentabilidade_abs_1a = patrimonio_total - valor_1a_ajustado_total
        rentabilidade_abs_total = patrimonio_total - valor_inicial_ajustado_total

        rentabilidade_perc_1m = ((rentabilidade_abs_1m / valor_1m_ajustado_total) * 100) if valor_1m_ajustado_total else 0
        rentabilidade_perc_1a = ((rentabilidade_abs_1a / valor_1a_ajustado_total) * 100) if valor_1a_ajustado_total else 0
        rentabilidade_perc_total = ((rentabilidade_abs_total / valor_inicial_ajustado_total) * 100) if valor_inicial_ajustado_total else 0 

        context.update({
            "patrimonio_total": patrimonio_total,
            "rentabilidade_abs_1m": rentabilidade_abs_1m,
            "rentabilidade_abs_1a": rentabilidade_abs_1a,
            "rentabilidade_abs_total": rentabilidade_abs_total,  
            "rentabilidade_perc_1m": rentabilidade_perc_1m,
            "rentabilidade_perc_1a": rentabilidade_perc_1a,
            "rentabilidade_perc_total": rentabilidade_perc_total,
        })

        return context
    
    def calcular_rentabilidade_mensal(self, ativos):
        """Calcula a rentabilidade mês a mês da carteira inteira."""

        if not ativos.exists():
            return []  # Retorna lista vazia se não houver ativos

        # Determina o período de cálculo
        data_inicio = min(ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao)
        data_fim = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)

        # Garante que temos pelo menos um mês no intervalo
        if data_fim < data_inicio:
            return []

        rentabilidade_mensal = []
        valor_anterior = None

        # Gera as datas de referência mês a mês
        data_atual = data_inicio.replace(day=1)  # Sempre começa no primeiro dia do mês
        while data_atual <= data_fim:
            valor_atual = sum(self.get_valor_ajustado(ativo, data_atual) for ativo in ativos)

            # Se não há atualização no mês, mantém o valor do mês anterior
            if valor_atual is None and valor_anterior is not None:
                valor_atual = valor_anterior

            rentabilidade_abs = (valor_atual - valor_anterior) if valor_anterior else 0
            rentabilidade_perc = (rentabilidade_abs / valor_anterior * 100) if valor_anterior else 0

            rentabilidade_mensal.append({
                "mes": data_atual.strftime("%Y-%m"),
                "valor": valor_atual,
                "rentabilidade_abs": rentabilidade_abs,
                "rentabilidade_perc": rentabilidade_perc,
            })

            # Atualiza o valor do mês anterior para a próxima iteração
            valor_anterior = valor_atual
            data_atual += relativedelta(months=1)  # Avança para o próximo mês

        return rentabilidade_mensal
    
    def calcular_rentabilidade_comparativa(self, ativos):
        """Calcula a rentabilidade acumulada do patrimônio comparada ao CDI e IBOVESPA."""

        if not ativos.exists():
            return [], [], [], []

        # Determina o período do cálculo
        data_inicio = min(ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao)
        data_fim = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)

        if data_fim < data_inicio:
            return [], [], [], []

        # Obtém a rentabilidade inicial
        valor_inicial = sum(self.get_valor_ajustado(ativo, data_inicio) for ativo in ativos)

        # Obtém os dados históricos do CDI e IBOVESPA
        meses_ordenados = pd.date_range(data_inicio, data_fim, freq='MS').to_pydatetime().tolist()
        if not meses_ordenados:
            return [], [], [], []
        
        data_inicio_str = meses_ordenados[0].strftime("%d/%m/%Y")
        data_fim_str = meses_ordenados[-1].strftime("%d/%m/%Y")

        indices_historicos = obter_indices_historicos(data_inicio_str, data_fim_str)
        cdi_mensal_historico = indices_historicos.get("CDI", {})
        ibov_mensal_historico = indices_historicos.get("IBOVESPA", {})

        # Listas para armazenar os dados
        labels = []
        rentabilidade_perc = []
        cdi_acumulado = [1]  # CDI começa em 1 (100% do investimento inicial)
        ibov_acumulado = [1]  # IBOVESPA começa em 1 (100% do investimento inicial)

        valor_anterior = valor_inicial

        for i, mes_atual in enumerate(meses_ordenados):
            mes_str = mes_atual.strftime("%Y-%m")
            valor_atual = sum(self.get_valor_ajustado(ativo, mes_atual) for ativo in ativos)

            # Rentabilidade da carteira em relação ao início
            rentabilidade = ((valor_atual / valor_inicial) - 1) * 100 if valor_inicial else 0
            rentabilidade_perc.append(rentabilidade)

            # Obter CDI e IBOV mensal
            cdi_mensal = cdi_mensal_historico.get(mes_str, 0)
            ibov_mensal = ibov_mensal_historico.get(mes_str, 0)

            # Acumular CDI e IBOV
            cdi_acumulado.append(cdi_acumulado[-1] * (1 + cdi_mensal / 100))
            ibov_acumulado.append(ibov_acumulado[-1] * (1 + ibov_mensal / 100))

            labels.append(mes_str)
            valor_anterior = valor_atual

        # Converter CDI e IBOV para percentual
        cdi_acumulado_perc = [(valor - 1) * 100 for valor in cdi_acumulado[1:]]
        ibov_acumulado_perc = [(valor - 1) * 100 for valor in ibov_acumulado[1:]]

        return labels, rentabilidade_perc, cdi_acumulado_perc, ibov_acumulado_perc
    
    def calcular_evolucao_patrimonial(self, ativos):
        """Calcula a evolução do patrimônio mês a mês."""

        if not ativos.exists():
            return [], []

        data_inicio = min(ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao)
        data_fim = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)

        if data_fim < data_inicio:
            return [], []

        labels = []
        patrimonio = []

        meses_ordenados = pd.date_range(data_inicio, data_fim, freq='MS').to_pydatetime().tolist()

        for mes_atual in meses_ordenados:
            valor_atual = sum(self.get_valor_ajustado(ativo, mes_atual) for ativo in ativos)
            labels.append(mes_atual.strftime("%Y-%m"))
            patrimonio.append(valor_atual)

        return labels, patrimonio

    def calcular_composicao_por_subclasse(self, ativos):
        """Calcula a composição percentual da carteira por subclasse de ativo."""

        if not ativos.exists():
            return [], []

        # Obtém o valor atualizado total da carteira
        patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

        # Agrupa os valores por subclasse
        composicao_subclasse = {}
        for ativo in ativos:
            subclasse = ativo.subclasse
            composicao_subclasse[subclasse] = composicao_subclasse.get(subclasse, 0) + ativo.valor_atualizado

        # Calcula a participação percentual de cada subclasse
        labels = list(composicao_subclasse.keys())
        data = [(valor / patrimonio_total) * 100 for valor in composicao_subclasse.values()]

        return labels, data
    
    def calcular_composição_por_classe(self, ativos):
        """Calcula a composição percentual da carteira para Renda Fixa e Renda Variável."""

        if not ativos.exists():
            return {"Renda Fixa": 0, "Renda Variável": 0}

        # Obtém o valor atualizado total da carteira
        patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

        # Inicializa as classes com 0%
        composicao = {"Renda Fixa": 0, "Renda Variável": 0}

        # Soma os valores para cada classe
        for ativo in ativos:
            if ativo.classe in composicao:
                composicao[ativo.classe] += ativo.valor_atualizado

        # Converte para percentual
        composicao = {classe: (valor / patrimonio_total) * 100 for classe, valor in composicao.items()}

        return composicao

    def get_context_data(self, **kwargs):
        """Adiciona informações de rentabilidade global, comparativa e evolução patrimonial ao contexto."""
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        context["classes_disponiveis"] = usuario_ativos.values_list("classe", flat=True).distinct()
        context["subclasses_disponiveis"] = usuario_ativos.values_list("subclasse", flat=True).distinct()
        context["bancos_disponiveis"] = usuario_ativos.values_list("banco", flat=True).distinct()

        ativos = context["ativos"]

        if not ativos.exists():
            return self.definir_contexto_vazio(context)

        context = self.calcular_rentabilidade_global(context, ativos)
        context["rentabilidade_mensal"] = self.calcular_rentabilidade_mensal(ativos)

        # Adiciona rentabilidade comparativa (Carteira vs CDI vs IBOVESPA)
        labels, rentabilidade_perc, cdi_perc, ibov_perc = self.calcular_rentabilidade_comparativa(ativos)
        context["grafico_labels"] = json.dumps(labels)
        context["grafico_data_perc"] = json.dumps([float(val) for val in rentabilidade_perc])
        context["grafico_data_cdi"] = json.dumps([float(val) for val in cdi_perc])
        context["grafico_data_ibov"] = json.dumps([float(val) for val in ibov_perc])

        # Adiciona evolução patrimonial
        labels_patrimonio, patrimonio = self.calcular_evolucao_patrimonial(ativos)
        context["grafico_data_abs"] = json.dumps([float(val) for val in patrimonio])

         # Composição da carteira por subclasse
        labels_subclasse, data_subclasse = self.calcular_composicao_por_subclasse(ativos)
        context["grafico_labels_subclasses"] = json.dumps(labels_subclasse)
        context["grafico_data_subclasses"] = json.dumps([float(val) for val in data_subclasse])

        # Composição da carteira por classe de ativo
        composicao_classes = self.calcular_composição_por_classe(ativos)
        context["renda_fixa_perc"] = composicao_classes["Renda Fixa"]
        context["renda_variavel_perc"] = composicao_classes["Renda Variável"]

        return context



class ResumoAtivoView(DetailView):
    model = Ativo
    template_name = "resumo_ativo.html"
    context_object_name = "ativo"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ativo = self.object

        valores_ativos = ValorAtivo.objects.filter(ativo=ativo).order_by("data")

        operacoes = Operacao.objects.filter(ativo=ativo).order_by("data")

        if not valores_ativos.exists():
            context["rentabilidades"] = []
            context["grafico_labels"] = json.dumps([])
            context["grafico_data_perc"] = json.dumps([])
            context["grafico_data_abs"] = json.dumps([])
            return context

        historico = defaultdict(lambda: {"valor": None, "rentabilidade_abs": 0, "rentabilidade_perc": 0})

        # Mapeamento de atualizações e operações
        atualizacoes_mensais = {}
        compras_vendas_mensais = defaultdict(float)

        for operacao in operacoes:
            mes_operacao = operacao.data.replace(day=1)

            if operacao.tipo == "atualizacao":
                atualizacoes_mensais[mes_operacao] = float(operacao.valor)
            elif operacao.tipo == "compra":
                compras_vendas_mensais[mes_operacao] += float(operacao.valor)
            elif operacao.tipo == "venda":
                compras_vendas_mensais[mes_operacao] -= float(operacao.valor)

        mes_atual = ativo.data_aquisicao.replace(day=1)
        mes_final = now().date().replace(day=1)

        valores_por_mes = {va.data.replace(day=1): float(va.valor) for va in valores_ativos}

        while mes_atual <= mes_final:
            if mes_atual in valores_por_mes:
                historico[mes_atual]["valor"] = valores_por_mes[mes_atual]
            mes_atual += timedelta(days=32)
            mes_atual = mes_atual.replace(day=1)

        context["historico"] = historico

        meses_ordenados = sorted(historico.keys())

        labels = []
        data_perc = []
        data_abs = []

        # Cálculo da rentabilidade baseado na metodologia anterior
        for i in range(1, len(meses_ordenados)):
            mes_anterior = meses_ordenados[i - 1]
            mes_atual = meses_ordenados[i]

            valor_anterior = historico[mes_anterior]["valor"]
            valor_atual = historico[mes_atual]["valor"]

            # Ajustando o valor de referência com compras e vendas entre os meses
            ajuste = sum(
                compras_vendas_mensais[m] for m in meses_ordenados if mes_anterior <= m < mes_atual
            )

            if valor_anterior is not None and valor_atual is not None:
                rentabilidade_abs = valor_atual - (valor_anterior + ajuste)
                rentabilidade_perc = (rentabilidade_abs / (valor_anterior + ajuste)) * 100 if (valor_anterior + ajuste) != 0 else 0
            else:
                rentabilidade_abs = 0
                rentabilidade_perc = 0

            historico[mes_atual]["rentabilidade_abs"] = rentabilidade_abs
            historico[mes_atual]["rentabilidade_perc"] = rentabilidade_perc

            # Adicionando ao gráfico
            labels.append(mes_atual.strftime("%Y-%m"))
            data_perc.append(data_perc[-1] + rentabilidade_perc if data_perc else rentabilidade_perc)
            data_abs.append(valor_atual)


        context["rentabilidades"] = [
            {"data_referencia": mes, **dados} for mes, dados in sorted(historico.items())
        ]

        context["grafico_labels"] = json.dumps(labels)
        context["grafico_data_perc"] = json.dumps(data_perc)
        context["grafico_data_abs"] = json.dumps(data_abs)

        # Carregar cache do arquivo JSON
        indices_historicos = {}
        if os.path.exists("indices_cache.json"):
            with open("indices_cache.json", "r") as f:
                try:
                    indices_historicos = json.load(f).get("indices", {})
                except json.JSONDecodeError:
                    indices_historicos = {}

        # Determinar período desejado
        data_inicio = meses_ordenados[0].strftime("%d/%m/%Y")
        data_fim = meses_ordenados[-1].strftime("%d/%m/%Y")

        # Converter datas para o formato YYYY-MM para comparação
        data_inicio_fmt = datetime.strptime(data_inicio, "%d/%m/%Y").strftime("%Y-%m")
        data_fim_fmt = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m")

        # Filtrar diretamente na view
        cdi_mensal_historico = {
            mes: valor for mes, valor in indices_historicos.get("CDI", {}).items()
            if data_inicio_fmt <= mes <= data_fim_fmt
        }

        ibov_mensal_historico = {
            mes: valor for mes, valor in indices_historicos.get("IBOVESPA", {}).items()
            if data_inicio_fmt <= mes <= data_fim_fmt
        }


        data_cdi = [1]  # CDI começa em 1 (100% do investimento inicial)
        data_ibov = [1]  # IBOVESPA começa em 1 (100% do investimento inicial)

        for i in range(1, len(meses_ordenados)):
            mes_atual = meses_ordenados[i]
            mes_atual_str = mes_atual.strftime("%Y-%m")

            # Obter CDI e IBOV mensal
            cdi_mensal = cdi_mensal_historico.get(mes_atual_str, 0)
            ibov_mensal = ibov_mensal_historico.get(mes_atual_str, 0)

            # Acumular CDI e IBOV
            cdi_acumulado = data_cdi[-1] * (1 + cdi_mensal / 100)
            ibov_acumulado = data_ibov[-1] * (1 + ibov_mensal / 100)

            data_cdi.append(cdi_acumulado)
            data_ibov.append(ibov_acumulado)

        # Converter para percentual antes de exibir no gráfico
        data_cdi_percentual = [(valor - 1) * 100 for valor in data_cdi]
        data_ibov_percentual = [(valor - 1) * 100 for valor in data_ibov]

        # Enviar os dados corretos para o gráfico
        context["grafico_data_cdi"] = json.dumps(data_cdi_percentual)
        context["grafico_data_ibov"] = json.dumps(data_ibov_percentual)

        return context

