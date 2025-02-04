from django.db.models import Max, Sum
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao

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

        # Obtém a data da última operação de atualização para cada ativo
        ultimas_atualizacoes = (
            Operacao.objects.filter(ativo__usuario=self.request.user, tipo="atualizacao")
            .values("ativo")
            .annotate(ultima_data=Max("data"))
        )

        # Mapeia a última atualização para cada ativo
        atualizacoes_dict = {
            item["ativo"]: item["ultima_data"]
            for item in ultimas_atualizacoes
        }

        for ativo in queryset:
            ultima_data_atualizacao = atualizacoes_dict.get(ativo.id)

            # Obtém a última operação de atualização
            if ultima_data_atualizacao:
                ultima_atualizacao = (
                    Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data=ultima_data_atualizacao)
                    .order_by("-data")
                    .first()
                )
                valor_atualizado = ultima_atualizacao.valor
            else:
                ultima_atualizacao = None
                valor_atualizado = ativo.valor_inicial  # Se não houver atualização, começa com o valor inicial

            # Obtém a soma de compras e vendas após a última atualização (se houver atualização)
            if ultima_data_atualizacao:
                compras = (
                    Operacao.objects.filter(ativo=ativo, tipo="compra", data__gt=ultima_data_atualizacao)
                    .aggregate(total_compras=Sum("valor"))["total_compras"] or 0
                )
                vendas = (
                    Operacao.objects.filter(ativo=ativo, tipo="venda", data__gt=ultima_data_atualizacao)
                    .aggregate(total_vendas=Sum("valor"))["total_vendas"] or 0
                )
            else:
                compras = 0
                vendas = 0

            # Ajusta o valor atualizado com compras e vendas
            valor_atualizado += compras - vendas

            # Verifica se há uma compra ou venda mais recente que a última atualização
            ultima_operacao = (
                Operacao.objects.filter(ativo=ativo, tipo__in=["compra", "venda"])
                .order_by("-data")
                .first()
            )

            if ultima_operacao and (not ultima_data_atualizacao or ultima_operacao.data > ultima_data_atualizacao):
                ultima_data_atualizacao = ultima_operacao.data  # Atualiza a data da última atualização

            # Se o ativo não tem nenhuma operação, mantém a data de aquisição como última atualização
            if not ultima_data_atualizacao:
                ultima_data_atualizacao = ativo.data_aquisicao

            # Adiciona os valores calculados ao objeto ativo
            ativo.ultima_atualizacao = ultima_data_atualizacao
            ativo.valor_atualizado = valor_atualizado  # Novo atributo para o template

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
