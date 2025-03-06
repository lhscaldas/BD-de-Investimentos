from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from datetime import timedelta, datetime
from django.db.models import Sum
import json
from dateutil.relativedelta import relativedelta
import pandas as pd
import os
from .views_resumo_aux import obter_indices_historicos, calcular_indices_acumulados
from math import prod

class ResumoAtivoView(DetailView):
    model = Ativo
    template_name = "resumo_ativo.html"
    context_object_name = "ativo"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ativo = self.object
        usuario = self.request.user

        # Caminho do arquivo JSON
        json_path = "dados_financeiros.json"

        # Verifica se o arquivo existe
        if not os.path.exists(json_path):
            context["rentabilidades"] = []
            context["grafico_labels"] = json.dumps([])
            context["grafico_data_perc"] = json.dumps([])
            context["grafico_data_abs"] = json.dumps([])
            return context

        # Carrega os dados do JSON
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                dados_financeiros = json.load(f)
            except json.JSONDecodeError:
                context["rentabilidades"] = []
                context["grafico_labels"] = json.dumps([])
                context["grafico_data_perc"] = json.dumps([])
                context["grafico_data_abs"] = json.dumps([])
                return context

        # Verifica se há dados para o usuário e ativo
        usuario_id = str(usuario.id)
        ativo_id = str(ativo.id)

        if usuario_id not in dados_financeiros or ativo_id not in dados_financeiros[usuario_id]:
            context["rentabilidades"] = []
            context["grafico_labels"] = json.dumps([])
            context["grafico_data_perc"] = json.dumps([])
            context["grafico_data_abs"] = json.dumps([])
            return context

        # Obtém valores e rentabilidades do JSON
        dados_ativo = dados_financeiros[usuario_id][ativo_id]
        valores_por_mes = {datetime.strptime(mes, "%Y-%m"): float(valor) for mes, valor in dados_ativo["valor"].items()}
        rentabilidades_por_mes = {datetime.strptime(mes, "%Y-%m"): float(rent) for mes, rent in dados_ativo["rentabilidade"].items()}

        # Ordenação por data
        meses_ordenados = sorted(valores_por_mes.keys())

        # Criar estrutura do histórico
        historico = {
            mes: {
                "valor": valores_por_mes.get(mes, 0.0),
                "rentabilidade_abs": rentabilidades_por_mes.get(mes, 0.0),
                "rentabilidade_perc": (rentabilidades_por_mes.get(mes, 0.0) / valores_por_mes.get(mes, 1)) * 100 if valores_por_mes.get(mes, 1) != 0 else 0.0
            }
            for mes in meses_ordenados
        }

        context["historico"] = historico
        labels = [mes.strftime("%Y-%m") for mes in meses_ordenados]
        data_abs = [historico[mes]["valor"] for mes in meses_ordenados]

        # Calculando rentabilidade acumulada
        data_perc = []
        rentabilidade_acumulada = 1
        for mes in meses_ordenados:
            rentabilidade_acumulada *= (1 + historico[mes]["rentabilidade_perc"] / 100)
            data_perc.append((rentabilidade_acumulada - 1) * 100)

        context["rentabilidades"] = [
            {"data_referencia": mes, **dados} for mes, dados in sorted(historico.items())
        ]

        # Serializa os dados para o gráfico
        context["grafico_labels"] = json.dumps(labels)
        context["grafico_data_perc"] = json.dumps(data_perc[:-1])
        context["grafico_data_abs"] = json.dumps(data_abs)

        # Calcula CDI e IBOV
        data_cdi_percentual, data_ibov_percentual = calcular_indices_acumulados(meses_ordenados)
        context["grafico_data_cdi"] = json.dumps(data_cdi_percentual[:-1])
        context["grafico_data_ibov"] = json.dumps(data_ibov_percentual[:-1])

        return context

class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"
    
    def carregar_dados_financeiros(self):
        """Carrega os dados financeiros do JSON."""
        try:
            with open("dados_financeiros.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_queryset(self):
        """Retorna os ativos do usuário e define seus valores a partir do JSON."""
        ativos = Ativo.objects.filter(usuario=self.request.user)
        filtros_validos = ['nome', 'classe', 'subclasse', 'banco']
        filtros = {f"{k}__icontains": v for k, v in self.request.GET.items() if v and k in filtros_validos}
        if filtros:
            ativos = ativos.filter(**filtros)
        
        # Carrega os dados do JSON
        dados_financeiros = self.carregar_dados_financeiros()
        usuario_id = str(self.request.user.id)
        
        for ativo in ativos:
            ativo_id = str(ativo.id)
            
            # Obtém a última atualização do banco de dados
            ultima_atualizacao = (
                Operacao.objects.filter(ativo=ativo, tipo="atualizacao")
                .order_by("-data")
                .first()
            )
            ativo.ultima_atualizacao = ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao
            
            if usuario_id in dados_financeiros and ativo_id in dados_financeiros[usuario_id]:
                dados_ativo = dados_financeiros[usuario_id][ativo_id]
                valores = {datetime.strptime(mes, "%Y-%m"): float(valor) for mes, valor in dados_ativo["valor"].items()}
                rentabilidades = {datetime.strptime(mes, "%Y-%m"): float(rent) for mes, rent in dados_ativo["rentabilidade"].items()}
                
                # Ordenação por data
                meses_ordenados = sorted(valores.keys())
                
                if meses_ordenados:
                    ativo.valor_atualizado = valores[meses_ordenados[-1]]
                    
                    if len(meses_ordenados) > 1:
                        ativo.rentabilidade_1m_abs = rentabilidades[meses_ordenados[-2]]
                        ativo.rentabilidade_1m_perc = (rentabilidades[meses_ordenados[-2]] / valores[meses_ordenados[-2]]) * 100
                    else:
                        ativo.rentabilidade_1m_abs = 0
                        ativo.rentabilidade_1m_perc = 0
                    
                    if len(meses_ordenados) > 12:
                        ativo.rentabilidade_1a_abs = sum(rentabilidades[mes] for mes in meses_ordenados[-13:])
                        ativo.rentabilidade_1a_perc = (prod([(1 + (rentabilidades[mes] / valores[mes])) for mes in meses_ordenados[-13:]]) - 1) * 100

                    else:
                        ativo.rentabilidade_1a_abs = 0
                        ativo.rentabilidade_1a_perc = 0
                    
                    ativo.rentabilidade_total_abs = sum(rentabilidades.values())
                    ativo.rentabilidade_total_perc = (prod([(1 + (rentabilidades[mes] / valores[mes])) for mes in meses_ordenados]) - 1) * 100 
                else:
                    ativo.valor_atualizado = ativo.valor_inicial
                    ativo.rentabilidade_1m_abs = 0
                    ativo.rentabilidade_1m_perc = 0
                    ativo.rentabilidade_1a_abs = 0
                    ativo.rentabilidade_1a_perc = 0
                    ativo.rentabilidade_total_abs = 0
                    ativo.rentabilidade_total_perc = 0
            else:
                ativo.valor_atualizado = ativo.valor_inicial
                ativo.rentabilidade_1m_abs = 0
                ativo.rentabilidade_1m_perc = 0
                ativo.rentabilidade_1a_abs = 0
                ativo.rentabilidade_1a_perc = 0
                ativo.rentabilidade_total_abs = 0
                ativo.rentabilidade_total_perc = 0
        
        return ativos


    def get_context_data(self, **kwargs):
        """Adiciona informações de rentabilidade global, comparativa e evolução patrimonial ao contexto."""
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        # Cria o contexto para os filtros
        context["classes_disponiveis"] = usuario_ativos.values_list("classe", flat=True).distinct()
        context["subclasses_disponiveis"] = usuario_ativos.values_list("subclasse", flat=True).distinct()
        context["bancos_disponiveis"] = usuario_ativos.values_list("banco", flat=True).distinct()

        # Verifica se há ativos
        ativos = context["ativos"]
        if not ativos.exists():
            return self.definir_contexto_vazio(context)

        # Carrega os dados do JSON
        dados_financeiros = self.carregar_dados_financeiros()

        # Adiciona evolução patrimonial
        evolucao_patrimonial = self.calcular_evolucao_patrimonial(ativos, dados_financeiros)
        context.update(evolucao_patrimonial)

        # Composição da carteira por subclasse
        labels_subclasse, data_subclasse = self.calcular_composicao_por_subclasse(ativos)
        context["grafico_labels_subclasses"] = json.dumps(labels_subclasse)
        context["grafico_data_subclasses"] = json.dumps([float(val) for val in data_subclasse])

        # Composição da carteira por classe de ativo
        composicao_classes = self.calcular_composição_por_classe(ativos)
        context["renda_fixa_perc"] = composicao_classes["Renda Fixa"]
        context["renda_variavel_perc"] = composicao_classes["Renda Variável"]

        # Adiciona rentabilidade comparativa (Carteira vs CDI vs IBOVESPA)
        # labels, rentabilidade_perc, cdi_perc, ibov_perc = self.calcular_rentabilidade_comparativa(ativos)
        # context["grafico_labels"] = json.dumps(labels)
        # context["grafico_data_perc"] = json.dumps([float(val) for val in rentabilidade_perc])
        # context["grafico_data_cdi"] = json.dumps([float(val) for val in cdi_perc])
        # context["grafico_data_ibov"] = json.dumps([float(val) for val in ibov_perc])

        return context
    
    def definir_contexto_vazio(self, context):
        context.update({
                "patrimonio_total": 0,
                "rentabilidade_abs_1m": 0,
                "rentabilidade_abs_1a": 0,
                "rentabilidade_abs_total": 0,
                "rentabilidade_perc_1m": 0,
                "rentabilidade_perc_1a": 0,
                "rentabilidade_perc_total": 0,
                "rentabilidade_mensal": []
            })
        return context

    
    def calcular_evolucao_patrimonial(self, ativos, dados_financeiros):
        """Processa os dados financeiros para calcular patrimônio, rentabilidade mensal e evolução patrimonial."""
        usuario_id = str(self.request.user.id)
        patrimonio_total = 0
        rentabilidade_mensal = []
        valores_mensais = {}
        rentabilidades_mensais_carteira = {}
        labels = []

        for ativo in ativos:
            ativo_id = str(ativo.id)
            if usuario_id in dados_financeiros and ativo_id in dados_financeiros[usuario_id]:
                dados_ativo = dados_financeiros[usuario_id][ativo_id]
                valores = {datetime.strptime(mes, "%Y-%m"): float(valor) for mes, valor in dados_ativo["valor"].items()}
                rentabilidades = {datetime.strptime(mes, "%Y-%m"): float(rent) for mes, rent in dados_ativo["rentabilidade"].items()}
                
                meses_ordenados = sorted(valores.keys())
                if meses_ordenados:
                    patrimonio_total += valores[meses_ordenados[-1]]
                
                for mes in rentabilidades:
                    if mes not in rentabilidades_mensais_carteira:
                        rentabilidades_mensais_carteira[mes] = 0
                    rentabilidades_mensais_carteira[mes] += rentabilidades[mes]
                
                for mes in valores:
                    if mes not in valores_mensais:
                        valores_mensais[mes] = 0
                    valores_mensais[mes] += valores[mes]
        
        meses_ordenados = sorted(valores_mensais.keys())

        for mes in meses_ordenados:
            valor_atual = valores_mensais[mes]
            rentabilidade_abs = rentabilidades_mensais_carteira.get(mes, 0)
            rentabilidade_perc = (rentabilidade_abs / valor_atual * 100) if rentabilidade_abs else 0
            
            rentabilidade_mensal.append({
                "mes": mes.strftime("%Y-%m"),
                "valor": valor_atual,
                "rentabilidade_abs": rentabilidade_abs,
                "rentabilidade_perc": rentabilidade_perc,
            })
            labels.append(mes.strftime("%Y-%m"))
            
        
        rentabilidade_abs_1m = rentabilidade_mensal[-2]["rentabilidade_abs"] if len(rentabilidade_mensal) > 1 else 0
        rentabilidade_abs_1a = sum(item["rentabilidade_abs"] for item in rentabilidade_mensal[-13:]) if len(rentabilidade_mensal) > 12 else 0
        rentabilidade_abs_total = sum(item["rentabilidade_abs"] for item in rentabilidade_mensal)

        rentabilidade_perc_1m = (rentabilidade_abs_1m / valores_mensais.get(meses_ordenados[-2], 1) * 100) if len(meses_ordenados) > 1 else 0
        rentabilidade_perc_1a = (rentabilidade_abs_1a / valores_mensais.get(meses_ordenados[-13], 1) * 100) if len(meses_ordenados) > 12 else 0
        rentabilidade_perc_total = (rentabilidade_abs_total / valores_mensais.get(meses_ordenados[0], 1) * 100) if meses_ordenados else 0

        return {
            "patrimonio_total": patrimonio_total,
            "rentabilidade_abs_1m": rentabilidade_abs_1m,
            "rentabilidade_abs_1a": rentabilidade_abs_1a,
            "rentabilidade_abs_total": rentabilidade_abs_total,
            "rentabilidade_perc_1m": rentabilidade_perc_1m,
            "rentabilidade_perc_1a": rentabilidade_perc_1a,
            "rentabilidade_perc_total": rentabilidade_perc_total,
            "rentabilidade_mensal": rentabilidade_mensal,
            "grafico_labels": json.dumps(labels),
            "grafico_data_abs": json.dumps([float(val) for val in valores_mensais.values()])
        }
    

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

    
    # def calcular_rentabilidade_comparativa(self, ativos):
    #     """Calcula a rentabilidade acumulada do patrimônio comparada ao CDI e IBOVESPA."""

    #     if not ativos.exists():
    #         return [], [], [], []

    #     # Determina o período do cálculo
    #     data_inicio = min(ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao)
    #     data_fim = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)

    #     if data_fim < data_inicio:
    #         return [], [], [], []

    #     # Obtém a rentabilidade inicial
    #     valor_inicial = sum(self.get_valor_ajustado(ativo, data_inicio) for ativo in ativos)

    #     # Obtém os dados históricos do CDI e IBOVESPA
    #     meses_ordenados = pd.date_range(data_inicio, data_fim, freq='MS').to_pydatetime().tolist()
    #     if not meses_ordenados:
    #         return [], [], [], []
        
    #     data_inicio_str = meses_ordenados[0].strftime("%d/%m/%Y")
    #     data_fim_str = meses_ordenados[-1].strftime("%d/%m/%Y")

    #     indices_historicos = obter_indices_historicos(data_inicio_str, data_fim_str)
    #     cdi_mensal_historico = indices_historicos.get("CDI", {})
    #     ibov_mensal_historico = indices_historicos.get("IBOVESPA", {})

    #     # Listas para armazenar os dados
    #     labels = []
    #     rentabilidade_perc = []
    #     cdi_acumulado = [1]  # CDI começa em 1 (100% do investimento inicial)
    #     ibov_acumulado = [1]  # IBOVESPA começa em 1 (100% do investimento inicial)

    #     valor_anterior = valor_inicial

    #     for i, mes_atual in enumerate(meses_ordenados):
    #         mes_str = mes_atual.strftime("%Y-%m")
    #         valor_atual = sum(self.get_valor_ajustado(ativo, mes_atual) for ativo in ativos)

    #         # Rentabilidade da carteira em relação ao início
    #         rentabilidade = ((valor_atual / valor_inicial) - 1) * 100 if valor_inicial else 0
    #         rentabilidade_perc.append(rentabilidade)

    #         # Obter CDI e IBOV mensal
    #         cdi_mensal = cdi_mensal_historico.get(mes_str, 0)
    #         ibov_mensal = ibov_mensal_historico.get(mes_str, 0)

    #         # Acumular CDI e IBOV
    #         cdi_acumulado.append(cdi_acumulado[-1] * (1 + cdi_mensal / 100))
    #         ibov_acumulado.append(ibov_acumulado[-1] * (1 + ibov_mensal / 100))

    #         labels.append(mes_str)
    #         valor_anterior = valor_atual

    #     # Converter CDI e IBOV para percentual
    #     cdi_acumulado_perc = [(valor - 1) * 100 for valor in cdi_acumulado[1:]]
    #     ibov_acumulado_perc = [(valor - 1) * 100 for valor in ibov_acumulado[1:]]

    #     return labels, rentabilidade_perc, cdi_acumulado_perc, ibov_acumulado_perc



    

