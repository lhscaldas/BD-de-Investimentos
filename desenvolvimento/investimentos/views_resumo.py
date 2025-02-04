from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from django.db.models import Max

class ResumoView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = "resumo.html"
    context_object_name = "ativos"

    def get_queryset(self):
        queryset = Ativo.objects.filter(usuario=self.request.user)

        # Obtém a data da operação de atualização mais recente para cada ativo
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

        # Adiciona a última atualização ao contexto de cada ativo
        for ativo in queryset:
            ultima_data = atualizacoes_dict.get(ativo.id)
            if ultima_data:
                ativo.ultima_atualizacao = (
                    Operacao.objects.filter(ativo=ativo, tipo="atualizacao", data=ultima_data)
                    .order_by("-data")
                    .first()
                )
            else:
                ativo.ultima_atualizacao = None  # Se não houver atualizações

        return queryset
