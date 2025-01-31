from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao

class OperacaoListView(LoginRequiredMixin, ListView):
    model = Operacao
    template_name = 'listar_operacoes.html'
    context_object_name = 'operacoes'

    def get_queryset(self):
        return Operacao.objects.filter(ativo__usuario=self.request.user)  # Mostra apenas operações do usuário logado

class OperacaoCreateView(LoginRequiredMixin, CreateView):
    model = Operacao
    fields = ['tipo', 'valor', 'data', 'ativo']
    template_name = 'form_operacao.html'
    success_url = '/listar-operacoes'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Filtrar ativos apenas do usuário logado
        form.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.request.user)
        return form

class OperacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Operacao
    fields = ['tipo', 'valor', 'data']
    template_name = 'form_operacao.html'
    success_url = '/listar-operacoes'

class OperacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Operacao
    template_name = 'deletar_operacao.html'
    success_url = '/listar-operacoes'