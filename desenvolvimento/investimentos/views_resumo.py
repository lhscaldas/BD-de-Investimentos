from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao, RentabilidadeHistorica
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum

class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"

    def get_queryset(self):
        queryset = Ativo.objects.filter(usuario=self.request.user)

        for ativo in queryset:
            ultima_atualizacao = (
                Operacao.objects.filter(ativo=ativo, tipo="atualizacao")
                .order_by("-data")
                .first()
            )

            valor_atualizado = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial
            ultima_data_atualizacao = ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao

            compras_pos = (
                Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_data_atualizacao)
                .aggregate(total=Sum("valor"))["total"] or 0
            )
            vendas_pos = (
                Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_data_atualizacao)
                .aggregate(total=Sum("valor"))["total"] or 0
            )

            valor_atualizado += compras_pos - vendas_pos  # Ajuste no valor atualizado

            def get_valor_referencia(ativo, anos):
                data_limite = ultima_data_atualizacao - timedelta(days=anos * 365)
                operacao_referencia = (
                    Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_limite)
                    .order_by("-data")
                    .first()
                )
                return (operacao_referencia.valor, operacao_referencia.data) if operacao_referencia else (ativo.valor_inicial, ativo.data_aquisicao)

            valor_1m, data_1m = get_valor_referencia(ativo, 1 / 12)
            valor_1a, data_1a = get_valor_referencia(ativo, 1)
            valor_inicial = ativo.valor_inicial

            def ajustar_valor_com_operacoes(ativo, valor_base, data_base, ultima_data):
                compras = (
                    Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=data_base, data__lte=ultima_data)
                    .aggregate(total=Sum("valor"))["total"] or 0
                )
                vendas = (
                    Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=data_base, data__lte=ultima_data)
                    .aggregate(total=Sum("valor"))["total"] or 0
                )
                return valor_base + compras - vendas

            valor_1m = ajustar_valor_com_operacoes(ativo, valor_1m, data_1m, ultima_data_atualizacao)
            valor_1a = ajustar_valor_com_operacoes(ativo, valor_1a, data_1a, ultima_data_atualizacao)
            valor_inicial_ajustado = ajustar_valor_com_operacoes(ativo, valor_inicial, ativo.data_aquisicao, ultima_data_atualizacao)

            rentabilidade_1m_abs = valor_atualizado - valor_1m
            rentabilidade_1a_abs = valor_atualizado - valor_1a
            rentabilidade_total_abs = valor_atualizado - valor_inicial_ajustado

            rentabilidade_1m_perc = ((rentabilidade_1m_abs / valor_1m) * 100) if valor_1m else 0
            rentabilidade_1a_perc = ((rentabilidade_1a_abs / valor_1a) * 100) if valor_1a else 0
            rentabilidade_total_perc = ((rentabilidade_total_abs / valor_inicial_ajustado) * 100) if valor_inicial_ajustado else 0

            ativo.ultima_atualizacao = ultima_data_atualizacao
            ativo.valor_atualizado = valor_atualizado  

            # **📌 Agora salvamos na classe RentabilidadeHistorica**
            RentabilidadeHistorica.objects.update_or_create(
                ativo=ativo,
                data_referencia=ultima_data_atualizacao,
                defaults={
                    "rentabilidade_abs": rentabilidade_1m_abs,
                    "rentabilidade_perc": rentabilidade_1m_perc,
                },
            )

            ativo.rentabilidade_1m_abs = rentabilidade_1m_abs
            ativo.rentabilidade_1m_perc = rentabilidade_1m_perc
            ativo.rentabilidade_1a_abs = rentabilidade_1a_abs
            ativo.rentabilidade_1a_perc = rentabilidade_1a_perc
            ativo.rentabilidade_total_abs = rentabilidade_total_abs
            ativo.rentabilidade_total_perc = rentabilidade_total_perc

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        context['classes_disponiveis'] = usuario_ativos.values_list('classe', flat=True).distinct()
        context['subclasses_disponiveis'] = usuario_ativos.values_list('subclasse', flat=True).distinct()
        context['bancos_disponiveis'] = usuario_ativos.values_list('banco', flat=True).distinct()

        ativos = context["ativos"]
        patrimonio_total = sum(ativo.valor_atualizado for ativo in ativos)

        data_atual = max(ativo.ultima_atualizacao for ativo in ativos if ativo.ultima_atualizacao)
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

            def get_valor_ajustado(ativo, data_ref):
                ultima_atualizacao = (
                    Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_ref)
                    .order_by("-data")
                    .first()
                )
                valor_base = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial

                compras_ate_data = (
                    Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_atualizacao.data, data__lte=data_ref)
                    .aggregate(total=Sum("valor"))["total"] or 0
                ) if ultima_atualizacao else 0

                vendas_ate_data = (
                    Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_atualizacao.data, data__lte=data_ref)
                    .aggregate(total=Sum("valor"))["total"] or 0
                ) if ultima_atualizacao else 0

                return valor_base + compras_ate_data - vendas_ate_data

            valor_1m_ajustado = get_valor_ajustado(ativo, data_1m)
            valor_1a_ajustado = get_valor_ajustado(ativo, data_1a)

            valor_1m_ajustado_total += valor_1m_ajustado
            valor_1a_ajustado_total += valor_1a_ajustado

        rentabilidade_abs_1m = patrimonio_total - valor_1m_ajustado_total
        rentabilidade_abs_1a = patrimonio_total - valor_1a_ajustado_total
        rentabilidade_abs_total = patrimonio_total - valor_inicial_ajustado_total

        rentabilidade_perc_1m = ((rentabilidade_abs_1m / valor_1m_ajustado_total) * 100) if valor_1m_ajustado_total else 0
        rentabilidade_perc_1a = ((rentabilidade_abs_1a / valor_1a_ajustado_total) * 100) if valor_1a_ajustado_total else 0
        rentabilidade_perc_total = ((rentabilidade_abs_total / valor_inicial_ajustado_total) * 100) if valor_inicial_ajustado_total else 0

        context["patrimonio_total"] = patrimonio_total
        context["rentabilidade_abs_1m"] = rentabilidade_abs_1m
        context["rentabilidade_abs_1a"] = rentabilidade_abs_1a
        context["rentabilidade_abs_total"] = rentabilidade_abs_total
        context["rentabilidade_perc_1m"] = rentabilidade_perc_1m
        context["rentabilidade_perc_1a"] = rentabilidade_perc_1a
        context["rentabilidade_perc_total"] = rentabilidade_perc_total

        return context
