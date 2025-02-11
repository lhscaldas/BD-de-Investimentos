from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from datetime import timedelta
from django.db.models import Sum
from django.utils.timezone import now
from collections import defaultdict

class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"

    def get_queryset(self):
        """Retorna os ativos do usuário e calcula sua rentabilidade."""
        ativos = Ativo.objects.filter(usuario=self.request.user)

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
        valor_1m, data_1m = self.obter_valor_referencia(ativo, 1 / 12)
        valor_1a, data_1a = self.obter_valor_referencia(ativo, 1)
        valor_inicial = ativo.valor_inicial

        valor_1m = self.ajustar_valor_com_operacoes(ativo, valor_1m, data_1m, ativo.ultima_atualizacao)
        valor_1a = self.ajustar_valor_com_operacoes(ativo, valor_1a, data_1a, ativo.ultima_atualizacao)
        valor_inicial_ajustado = self.ajustar_valor_com_operacoes(ativo, valor_inicial, ativo.data_aquisicao, ativo.ultima_atualizacao)

        ativo.rentabilidade_1m_abs = ativo.valor_atualizado - valor_1m
        ativo.rentabilidade_1a_abs = ativo.valor_atualizado - valor_1a
        ativo.rentabilidade_total_abs = ativo.valor_atualizado - valor_inicial_ajustado

        ativo.rentabilidade_1m_perc = (ativo.rentabilidade_1m_abs / valor_1m * 100) if valor_1m else 0
        ativo.rentabilidade_1a_perc = (ativo.rentabilidade_1a_abs / valor_1a * 100) if valor_1a else 0
        ativo.rentabilidade_total_perc = (ativo.rentabilidade_total_abs / valor_inicial_ajustado * 100) if valor_inicial_ajustado else 0

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

    def get_context_data(self, **kwargs):
        """Adiciona informações de rentabilidade global da carteira ao contexto."""
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        context["classes_disponiveis"] = usuario_ativos.values_list("classe", flat=True).distinct()
        context["subclasses_disponiveis"] = usuario_ativos.values_list("subclasse", flat=True).distinct()
        context["bancos_disponiveis"] = usuario_ativos.values_list("banco", flat=True).distinct()

        ativos = context["ativos"]

        if not ativos.exists():
            return self.definir_contexto_vazio(context)

        return self.calcular_rentabilidade_global(context, ativos)

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
        """Obtém o valor do ativo em uma data específica, ajustado por compras e vendas."""
        if data_ref is None:
            return ativo.valor_inicial  # Se não houver data de referência, usa o valor inicial como fallback.

        ultima_atualizacao = (
            Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_ref)
            .order_by("-data")
            .first()
        )
        valor_base = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

        if ultima_atualizacao:
            compras_ate_data = (
                Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_atualizacao.data, data__lte=data_ref)
                .aggregate(total=Sum("valor"))["total"] or 0
            )
            vendas_ate_data = (
                Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_atualizacao.data, data__lte=data_ref)
                .aggregate(total=Sum("valor"))["total"] or 0
            )
        else:
            compras_ate_data = 0
            vendas_ate_data = 0

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
        rentabilidade_abs_total = patrimonio_total - valor_inicial_ajustado_total  # 🛠️ Correção aqui!

        rentabilidade_perc_1m = ((rentabilidade_abs_1m / valor_1m_ajustado_total) * 100) if valor_1m_ajustado_total else 0
        rentabilidade_perc_1a = ((rentabilidade_abs_1a / valor_1a_ajustado_total) * 100) if valor_1a_ajustado_total else 0
        rentabilidade_perc_total = ((rentabilidade_abs_total / valor_inicial_ajustado_total) * 100) if valor_inicial_ajustado_total else 0  # 🛠️ Correção aqui!

        context.update({
            "patrimonio_total": patrimonio_total,
            "rentabilidade_abs_1m": rentabilidade_abs_1m,
            "rentabilidade_abs_1a": rentabilidade_abs_1a,
            "rentabilidade_abs_total": rentabilidade_abs_total,  # 🛠️ Correção
            "rentabilidade_perc_1m": rentabilidade_perc_1m,
            "rentabilidade_perc_1a": rentabilidade_perc_1a,
            "rentabilidade_perc_total": rentabilidade_perc_total,  # 🛠️ Correção
        })

        return context








class ResumoAtivoView(DetailView):
    model = Ativo
    template_name = "resumo_ativo.html"
    context_object_name = "ativo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ativo = self.object
        
        # Obtém todas as operações do ativo
        operacoes = Operacao.objects.filter(ativo=ativo).order_by("data")

        if not operacoes.exists():
            context["rentabilidades"] = []
            return context

        # Dicionário para armazenar valores por mês
        historico = defaultdict(lambda: {"valor": None, "rentabilidade_abs": 0, "rentabilidade_perc": 0})

        # Valor inicial do ativo
        valor_atualizado = ativo.valor_inicial
        data_aquisicao = ativo.data_aquisicao
        mes_atual = data_aquisicao.replace(day=1)  # Começa do primeiro mês

        # Processa as operações para calcular os valores por mês
        for operacao in operacoes:
            mes_operacao = operacao.data.replace(day=1)
            
            while mes_atual < mes_operacao:
                # Preenche meses sem operação repetindo o último valor conhecido
                historico[mes_atual]["valor"] = valor_atualizado
                mes_atual += timedelta(days=32)  # Avança aproximadamente um mês
                mes_atual = mes_atual.replace(day=1)  # Garante que o dia seja sempre o primeiro

            # Atualiza o valor conforme a operação
            if operacao.tipo == "compra":
                valor_atualizado += operacao.valor
            elif operacao.tipo == "venda":
                valor_atualizado -= operacao.valor
            elif operacao.tipo == "atualizacao":
                valor_atualizado = operacao.valor

            # Armazena o valor atualizado no mês correspondente
            historico[mes_operacao]["valor"] = valor_atualizado

        # Garantir que o último mês seja registrado
        mes_final = now().date().replace(day=1)
        while mes_atual <= mes_final:
            historico[mes_atual]["valor"] = valor_atualizado
            mes_atual += timedelta(days=32)
            mes_atual = mes_atual.replace(day=1)

        # Calcula rentabilidade absoluta e percentual
        meses_ordenados = sorted(historico.keys())

        for i, mes in enumerate(meses_ordenados):
            if i == 0:
                continue  # O primeiro mês não tem base para comparação
            
            valor_anterior = historico[meses_ordenados[i - 1]]["valor"]
            valor_atual = historico[mes]["valor"]

            if valor_anterior is not None and valor_atual is not None:
                rentabilidade_abs = valor_atual - valor_anterior
                rentabilidade_perc = (rentabilidade_abs / valor_anterior) * 100 if valor_anterior != 0 else 0
            else:
                rentabilidade_abs = 0
                rentabilidade_perc = 0

            historico[mes]["rentabilidade_abs"] = rentabilidade_abs
            historico[mes]["rentabilidade_perc"] = rentabilidade_perc

        # Converte o histórico para uma lista ordenada para exibição no template
        context["rentabilidades"] = [
            {"data_referencia": mes, **dados} for mes, dados in sorted(historico.items())
        ]

        return context
