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

    # def get_queryset(self):
    #     """Retorna os ativos do usuário e calcula sua rentabilidade."""
    #     ativos = Ativo.objects.filter(usuario=self.request.user)

    #     # Lista de campos que podem ser filtrados
    #     filtros_validos = ['nome', 'classe', 'subclasse', 'banco']
        
    #     # Aplica os filtros somente se houver valores preenchidos
    #     filtros = {f"{k}__icontains": v for k, v in self.request.GET.items() if v and k in filtros_validos}

    #     if filtros:
    #         ativos = ativos.filter(**filtros)

    #     for ativo in ativos:
    #         self.calcular_valor_atualizado(ativo)
    #         self.calcular_rentabilidade(ativo)

    #     return ativos

    # def calcular_valor_atualizado(self, ativo):
        # """Calcula o valor atualizado do ativo baseado nas operações de compra, venda e atualização."""
        # ultima_atualizacao = (
        #     Operacao.objects.filter(ativo=ativo, tipo="atualizacao")
        #     .order_by("-data")
        #     .first()
        # )

        # ativo.ultima_atualizacao = ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao
    #     ativo.valor_atualizado = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

    #     compras = self.obter_soma_operacoes(ativo, "compra", ativo.ultima_atualizacao)
    #     vendas = self.obter_soma_operacoes(ativo, "venda", ativo.ultima_atualizacao)

    #     ativo.valor_atualizado += compras - vendas

    # def obter_soma_operacoes(self, ativo, tipo, data_inicial):
    #     """Retorna a soma das operações do tipo especificado após uma determinada data."""
    #     if data_inicial is None:
    #         return 0  # Se não há data inicial, não deve fazer filtragem

    #     return (
    #         Operacao.objects.filter(ativo=ativo, tipo=tipo, data__gt=data_inicial)
    #         .aggregate(total=Sum("valor"))["total"] or 0
    #     )


    # def obter_valor_referencia(self, ativo, anos):
    #     """Obtém o valor do ativo há `anos` anos atrás, considerando a última atualização disponível."""
    #     data_limite = ativo.ultima_atualizacao - timedelta(days=anos * 365)
    #     operacao_referencia = (
    #         Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_limite)
    #         .order_by("-data")
    #         .first()
    #     )
    #     return (
    #         operacao_referencia.valor if operacao_referencia else ativo.valor_inicial,
    #         operacao_referencia.data if operacao_referencia else ativo.data_aquisicao,
    #     )

    # def calcular_rentabilidade(self, ativo):
    #     """Calcula a rentabilidade absoluta e percentual do ativo."""

    #     # Obtém os valores de referência corretamente ajustados com compras e vendas
    #     valor_1m = self.get_valor_ajustado(ativo, ativo.ultima_atualizacao - timedelta(days=30))
    #     valor_1a = self.get_valor_ajustado(ativo, ativo.ultima_atualizacao - timedelta(days=365))
    #     valor_inicial_ajustado = self.get_valor_ajustado(ativo, ativo.data_aquisicao)

    #     # Calcula a rentabilidade absoluta
    #     ativo.rentabilidade_1m_abs = ativo.valor_atualizado - valor_1m
    #     ativo.rentabilidade_1a_abs = ativo.valor_atualizado - valor_1a
    #     ativo.rentabilidade_total_abs = ativo.valor_atualizado - valor_inicial_ajustado

    #     # Calcula a rentabilidade percentual, evitando divisões por zero
    #     ativo.rentabilidade_1m_perc = ((ativo.rentabilidade_1m_abs / valor_1m) * 100) if valor_1m else 0
    #     ativo.rentabilidade_1a_perc = ((ativo.rentabilidade_1a_abs / valor_1a) * 100) if valor_1a else 0
    #     ativo.rentabilidade_total_perc = ((ativo.rentabilidade_total_abs / valor_inicial_ajustado) * 100) if valor_inicial_ajustado else 0


    # def ajustar_valor_com_operacoes(self, ativo, valor_base, data_base, ultima_data):
    #     """Ajusta o valor do ativo considerando operações de compra e venda entre um período."""
    #     compras = self.obter_soma_operacoes_periodo(ativo, "compra", data_base, ultima_data)
    #     vendas = self.obter_soma_operacoes_periodo(ativo, "venda", data_base, ultima_data)
    #     return valor_base + compras - vendas

    # def obter_soma_operacoes_periodo(self, ativo, tipo, data_inicial, data_final):
    #     """Retorna a soma das operações do tipo especificado dentro de um intervalo de tempo."""
    #     return (
    #         Operacao.objects.filter(ativo=ativo, tipo=tipo, data__gt=data_inicial, data__lte=data_final)
    #         .aggregate(total=Sum("valor"))["total"] or 0
    #     )

    # def definir_contexto_vazio(self, context):
    #     """Define valores padrão para quando não há ativos."""
    #     context.update({
    #         "patrimonio_total": 0,
    #         "rentabilidade_abs_1m": 0,
    #         "rentabilidade_abs_1a": 0,
    #         "rentabilidade_abs_total": 0,
    #         "rentabilidade_perc_1m": 0,
    #         "rentabilidade_perc_1a": 0,
    #         "rentabilidade_perc_total": 0
    #     })
    #     return context
    
    # def get_valor_ajustado(self, ativo, data_ref):
    #     """Obtém o valor do ativo ajustado por compras e vendas até uma determinada data."""
    #     if data_ref is None:
    #         return ativo.valor_inicial  # Se não houver data de referência, retorna o valor inicial.

    #     # Obtém a última atualização antes da data de referência
    #     ultima_atualizacao = (
    #         Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_ref)
    #         .order_by("-data")
    #         .first()
    #     )
    #     valor_base = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

    #     # Ajusta com compras e vendas no período correto
    #     compras_ate_data = (
    #         Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao, data__lte=data_ref)
    #         .aggregate(total=Sum("valor"))["total"] or 0
    #     )
    #     vendas_ate_data = (
    #         Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao, data__lte=data_ref)
    #         .aggregate(total=Sum("valor"))["total"] or 0
    #     )

    #     return valor_base + compras_ate_data - vendas_ate_data

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

        context["classes_disponiveis"] = usuario_ativos.values_list("classe", flat=True).distinct()
        context["subclasses_disponiveis"] = usuario_ativos.values_list("subclasse", flat=True).distinct()
        context["bancos_disponiveis"] = usuario_ativos.values_list("banco", flat=True).distinct()

        ativos = context["ativos"]

        if not ativos.exists():
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

        # Carrega os dados do JSON
        dados_financeiros = self.carregar_dados_financeiros()
        usuario_id = str(self.request.user.id)

        rentabilidade_mensal = []
        valores_mensais = {}
        rentabilidades_mensais = {}

        for ativo in ativos:
            ativo_id = str(ativo.id)
            if usuario_id in dados_financeiros and ativo_id in dados_financeiros[usuario_id]:
                dados_ativo = dados_financeiros[usuario_id][ativo_id]
                valores = {datetime.strptime(mes, "%Y-%m"): float(valor) for mes, valor in dados_ativo["valor"].items()}
                rentabilidades = {datetime.strptime(mes, "%Y-%m"): float(rent) for mes, rent in dados_ativo["rentabilidade"].items()}
                
                for mes in valores:
                    if mes not in valores_mensais:
                        valores_mensais[mes] = 0
                        rentabilidades_mensais[mes] = 0
                    valores_mensais[mes] += valores[mes]
                    rentabilidades_mensais[mes] += rentabilidades[mes]
        
        meses_ordenados = sorted(valores_mensais.keys())
        valor_anterior = None

        for mes in meses_ordenados:
            valor_atual = valores_mensais[mes]
            rentabilidade_abs = (valor_atual - valor_anterior) if valor_anterior else 0
            rentabilidade_perc = (rentabilidades_mensais[mes] / valor_anterior * 100) if valor_anterior else 0
            
            rentabilidade_mensal.append({
                "mes": mes.strftime("%Y-%m"),
                "valor": valor_atual,
                "rentabilidade_abs": rentabilidade_abs,
                "rentabilidade_perc": rentabilidade_perc,
            })
            
            valor_anterior = valor_atual

        context["rentabilidade_mensal"] = rentabilidade_mensal

        # # Adiciona rentabilidade comparativa (Carteira vs CDI vs IBOVESPA)
        # labels, rentabilidade_perc, cdi_perc, ibov_perc = self.calcular_rentabilidade_comparativa(ativos)
        # context["grafico_labels"] = json.dumps(labels)
        # context["grafico_data_perc"] = json.dumps([float(val) for val in rentabilidade_perc])
        # context["grafico_data_cdi"] = json.dumps([float(val) for val in cdi_perc])
        # context["grafico_data_ibov"] = json.dumps([float(val) for val in ibov_perc])

        # # Adiciona evolução patrimonial
        # labels_patrimonio, patrimonio = self.calcular_evolucao_patrimonial(ativos)
        # context["grafico_data_abs"] = json.dumps([float(val) for val in patrimonio])

        #  # Composição da carteira por subclasse
        # labels_subclasse, data_subclasse = self.calcular_composicao_por_subclasse(ativos)
        # context["grafico_labels_subclasses"] = json.dumps(labels_subclasse)
        # context["grafico_data_subclasses"] = json.dumps([float(val) for val in data_subclasse])

        # # Composição da carteira por classe de ativo
        # composicao_classes = self.calcular_composição_por_classe(ativos)
        # context["renda_fixa_perc"] = composicao_classes["Renda Fixa"]
        # context["renda_variavel_perc"] = composicao_classes["Renda Variável"]

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



    # def calcular_rentabilidade_global(self, context, ativos):
    #     """Calcula a rentabilidade global da carteira baseada no método original."""
    #     patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

    #     datas_atualizacoes = [ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao]
    #     if datas_atualizacoes:
    #         data_atual = max(datas_atualizacoes)
    #     else:
    #         datas_aquisicao = [ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao]
    #         data_atual = min(datas_aquisicao) if datas_aquisicao else None

    #     if not data_atual:
    #         return self.definir_contexto_vazio(context)

    #     data_1m = data_atual - timedelta(days=30)
    #     data_1a = data_atual - timedelta(days=365)

    #     valor_inicial_ajustado_total = 0
    #     valor_1m_ajustado_total = 0
    #     valor_1a_ajustado_total = 0

    #     for ativo in ativos:
    #         compras_total = (
    #             Operacao.objects.filter(ativo=ativo, tipo="compra")
    #             .aggregate(total=Sum("valor"))["total"] or 0
    #         )
    #         vendas_total = (
    #             Operacao.objects.filter(ativo=ativo, tipo="venda")
    #             .aggregate(total=Sum("valor"))["total"] or 0
    #         )
    #         valor_inicial_ajustado = ativo.valor_inicial + compras_total - vendas_total
    #         valor_inicial_ajustado_total += valor_inicial_ajustado

    #         valor_1m_ajustado = self.get_valor_ajustado(ativo, data_1m)
    #         valor_1a_ajustado = self.get_valor_ajustado(ativo, data_1a)

    #         valor_1m_ajustado_total += valor_1m_ajustado
    #         valor_1a_ajustado_total += valor_1a_ajustado

    #     rentabilidade_abs_1m = patrimonio_total - valor_1m_ajustado_total
    #     rentabilidade_abs_1a = patrimonio_total - valor_1a_ajustado_total
    #     rentabilidade_abs_total = patrimonio_total - valor_inicial_ajustado_total

    #     rentabilidade_perc_1m = ((rentabilidade_abs_1m / valor_1m_ajustado_total) * 100) if valor_1m_ajustado_total else 0
    #     rentabilidade_perc_1a = ((rentabilidade_abs_1a / valor_1a_ajustado_total) * 100) if valor_1a_ajustado_total else 0
    #     rentabilidade_perc_total = ((rentabilidade_abs_total / valor_inicial_ajustado_total) * 100) if valor_inicial_ajustado_total else 0 

    #     context.update({
    #         "patrimonio_total": patrimonio_total,
    #         "rentabilidade_abs_1m": rentabilidade_abs_1m,
    #         "rentabilidade_abs_1a": rentabilidade_abs_1a,
    #         "rentabilidade_abs_total": rentabilidade_abs_total,  
    #         "rentabilidade_perc_1m": rentabilidade_perc_1m,
    #         "rentabilidade_perc_1a": rentabilidade_perc_1a,
    #         "rentabilidade_perc_total": rentabilidade_perc_total,
    #     })

    #     return context
    

    
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
    
    # def calcular_evolucao_patrimonial(self, ativos):
    #     """Calcula a evolução do patrimônio mês a mês."""

    #     if not ativos.exists():
    #         return [], []

    #     data_inicio = min(ativo.data_aquisicao for ativo in ativos if ativo.data_aquisicao)
    #     data_fim = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)

    #     if data_fim < data_inicio:
    #         return [], []

    #     labels = []
    #     patrimonio = []

    #     meses_ordenados = pd.date_range(data_inicio, data_fim, freq='MS').to_pydatetime().tolist()

    #     for mes_atual in meses_ordenados:
    #         valor_atual = sum(self.get_valor_ajustado(ativo, mes_atual) for ativo in ativos)
    #         labels.append(mes_atual.strftime("%Y-%m"))
    #         patrimonio.append(valor_atual)

    #     return labels, patrimonio

    # def calcular_composicao_por_subclasse(self, ativos):
    #     """Calcula a composição percentual da carteira por subclasse de ativo."""

    #     if not ativos.exists():
    #         return [], []

    #     # Obtém o valor atualizado total da carteira
    #     patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

    #     # Agrupa os valores por subclasse
    #     composicao_subclasse = {}
    #     for ativo in ativos:
    #         subclasse = ativo.subclasse
    #         composicao_subclasse[subclasse] = composicao_subclasse.get(subclasse, 0) + ativo.valor_atualizado

    #     # Calcula a participação percentual de cada subclasse
    #     labels = list(composicao_subclasse.keys())
    #     data = [(valor / patrimonio_total) * 100 for valor in composicao_subclasse.values()]

    #     return labels, data
    
    # def calcular_composição_por_classe(self, ativos):
    #     """Calcula a composição percentual da carteira para Renda Fixa e Renda Variável."""

    #     if not ativos.exists():
    #         return {"Renda Fixa": 0, "Renda Variável": 0}

    #     # Obtém o valor atualizado total da carteira
    #     patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

    #     # Inicializa as classes com 0%
    #     composicao = {"Renda Fixa": 0, "Renda Variável": 0}

    #     # Soma os valores para cada classe
    #     for ativo in ativos:
    #         if ativo.classe in composicao:
    #             composicao[ativo.classe] += ativo.valor_atualizado

    #     # Converte para percentual
    #     composicao = {classe: (valor / patrimonio_total) * 100 for classe, valor in composicao.items()}

    #     return composicao

    

