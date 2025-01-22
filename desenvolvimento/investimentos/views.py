from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao

class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
    template_name = 'investimentos/form_ativo.html'
    success_url = '/investimentos/listar-ativos'

    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        return super().form_valid(form)

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'investimentos/listar_ativos.html' 
    context_object_name = 'ativos'

    def get_queryset(self):
        # Filtra os ativos para mostrar apenas os do usuário logado
        return Ativo.objects.filter(usuario=self.request.user)
    
class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
    template_name = 'investimentos/form_ativo.html'
    success_url = '/investimentos/listar-ativos'

class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Ativo
    template_name = 'investimentos/deletar_ativo.html'
    success_url = '/investimentos/listar-ativos'  # Redireciona após a exclusão

class OperacaoCreateView(LoginRequiredMixin, CreateView):
    model = Operacao
    fields = ['tipo', 'valor', 'data', 'ativo']
    template_name = 'investimentos/form_operacao.html'
    success_url = '/investimentos/listar-operacoes'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Filtrar ativos apenas do usuário logado
        form.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.request.user)
        return form

class OperacaoListView(LoginRequiredMixin, ListView):
    model = Operacao
    template_name = 'investimentos/listar_operacoes.html'
    context_object_name = 'operacoes'

    def get_queryset(self):
        return Operacao.objects.filter(ativo__usuario=self.request.user)  # Mostra apenas operações do usuário logado

class OperacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Operacao
    fields = ['tipo', 'valor', 'data']
    template_name = 'investimentos/form_operacao.html'
    success_url = '/investimentos/listar-operacoes'

class OperacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Operacao
    template_name = 'investimentos/deletar_operacao.html'
    success_url = '/investimentos/listar-operacoes'

