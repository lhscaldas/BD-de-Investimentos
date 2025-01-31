from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao

################################################
#                  Resumo                      #
################################################

class ResumoView(LoginRequiredMixin, TemplateView):
    template_name = 'resumo.html'