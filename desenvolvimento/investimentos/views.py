from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from django.views.generic import TemplateView
from .forms import AtivoForm  # Importa o formulário personalizado

class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    form_class = AtivoForm  # Usa o formulário estilizado
    template_name = 'form_ativo.html'
    success_url = '/listar-ativos'

    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        return super().form_valid(form)

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'listar_ativos.html' 
    context_object_name = 'ativos'

    def get_queryset(self):
        # Filtra os ativos para mostrar apenas os do usuário logado
        return Ativo.objects.filter(usuario=self.request.user)
    
class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    # fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
    form_class = AtivoForm  # Usa o formulário estilizado
    template_name = 'form_ativo.html'
    success_url = '/listar-ativos'

    def get_queryset(self):
        """Garante que o usuário só pode editar seus próprios ativos"""
        return Ativo.objects.filter(usuario=self.request.user)

class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Ativo
    template_name = 'deletar_ativo.html'
    success_url = '/listar-ativos'  # Redireciona após a exclusão

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

class OperacaoListView(LoginRequiredMixin, ListView):
    model = Operacao
    template_name = 'listar_operacoes.html'
    context_object_name = 'operacoes'

    def get_queryset(self):
        return Operacao.objects.filter(ativo__usuario=self.request.user)  # Mostra apenas operações do usuário logado

class OperacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Operacao
    fields = ['tipo', 'valor', 'data']
    template_name = 'form_operacao.html'
    success_url = '/listar-operacoes'

class OperacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Operacao
    template_name = 'deletar_operacao.html'
    success_url = '/listar-operacoes'


class ResumoView(LoginRequiredMixin, TemplateView):
    template_name = 'resumo.html'
