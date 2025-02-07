from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from datetime import timedelta
from django.db.models import Sum

class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"

    def get_queryset(self):
        queryset = Ativo.objects.filter(usuario=self.request.user)

        # Aplica os filtros somente se houver valores preenchidos
        filtros_validos = ['nome', 'classe', 'subclasse', 'banco']
        filtros = {f"{k}__icontains": v for k, v in self.request.GET.items() if v and k in filtros_validos}
        queryset = queryset.filter(**filtros)

        for ativo in queryset:
            # Obtém a operação de atualização mais recente (valor atualizado atual)
            ultima_atualizacao = (
                Operacao.objects.filter(ativo=ativo, tipo="atualizacao")
                .order_by("-data")
                .first()
            )

            valor_atualizado = ultima_atualizacao.valor if ultima_atualizacao else ativo.valor_inicial
            ultima_data_atualizacao = ultima_atualizacao.data if ultima_atualizacao else ativo.data_aquisicao

            # Considerar compras e vendas posteriores à última atualização
            compras_pos = (
                Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_data_atualizacao)
                .aggregate(total=Sum("valor"))["total"] or 0
            )
            vendas_pos = (
                Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_data_atualizacao)
                .aggregate(total=Sum("valor"))["total"] or 0
            )

            valor_atualizado += compras_pos - vendas_pos  # Ajuste no valor atualizado

            # Função para obter o valor da última atualização antes da data-alvo
            def get_valor_referencia(ativo, anos):
                """Busca a operação de atualização mais próxima da referência"""
                data_limite = ultima_data_atualizacao - timedelta(days=anos * 365)
                operacao_referencia = (
                    Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data__lte=data_limite)
                    .order_by("-data")
                    .first()
                )
                return (operacao_referencia.valor, operacao_referencia.data) if operacao_referencia else (ativo.valor_inicial, ativo.data_aquisicao)

            # Obtém os valores de referência e suas datas
            valor_1m, data_1m = get_valor_referencia(ativo, 1 / 12)  # 1 mês ≈ 1/12 ano
            valor_1a, data_1a = get_valor_referencia(ativo, 1)
            valor_3a, data_3a = get_valor_referencia(ativo, 3)

            # Ajustar valores com operações de compra/venda entre a data de referência e a última atualização
            def ajustar_valor_com_operacoes(ativo, valor_base, data_base, ultima_data):
                """Soma compras e subtrai vendas ocorridas entre data_base e ultima_data"""
                compras = (
                    Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=data_base, data__lte=ultima_data)
                    .aggregate(total=Sum("valor"))["total"] or 0
                )
                vendas = (
                    Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=data_base, data__lte=ultima_data)
                    .aggregate(total=Sum("valor"))["total"] or 0
                )
                return valor_base + compras - vendas

            # Ajustar os valores de referência com compras e vendas
            valor_1m = ajustar_valor_com_operacoes(ativo, valor_1m, data_1m, ultima_data_atualizacao)
            valor_1a = ajustar_valor_com_operacoes(ativo, valor_1a, data_1a, ultima_data_atualizacao)
            valor_3a = ajustar_valor_com_operacoes(ativo, valor_3a, data_3a, ultima_data_atualizacao)

            # Calcula rentabilidades (% e valor absoluto)
            ativo.rentabilidade_1m_abs = valor_atualizado - valor_1m
            ativo.rentabilidade_1a_abs = valor_atualizado - valor_1a
            ativo.rentabilidade_3a_abs = valor_atualizado - valor_3a

            ativo.rentabilidade_1m_perc = ((ativo.rentabilidade_1m_abs / valor_1m) * 100) if valor_1m else 0
            ativo.rentabilidade_1a_perc = ((ativo.rentabilidade_1a_abs / valor_1a) * 100) if valor_1a else 0
            ativo.rentabilidade_3a_perc = ((ativo.rentabilidade_3a_abs / valor_3a) * 100) if valor_3a else 0

            # Adiciona os valores calculados ao objeto ativo
            ativo.ultima_atualizacao = ultima_data_atualizacao
            ativo.valor_atualizado = valor_atualizado  # Agora ajustado com compras e vendas após a última atualização

        return queryset



    def get_context_data(self, **kwargs):
        """ Adiciona as opções de filtro ao contexto """
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        # Obtém valores únicos de Classe, Subclasse e Banco
        context['classes_disponiveis'] = usuario_ativos.values_list('classe', flat=True).distinct()
        context['subclasses_disponiveis'] = usuario_ativos.values_list('subclasse', flat=True).distinct()
        context['bancos_disponiveis'] = usuario_ativos.values_list('banco', flat=True).distinct()

        return context
