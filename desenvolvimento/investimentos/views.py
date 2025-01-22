from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo


class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
    template_name = 'investimentos/criar_ativo.html'  # Caminho para o template
    success_url = '/'  # Redireciona após a criação do ativo

    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        return super().form_valid(form)

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'investimentos/listar_ativos.html'  # Caminho para o template
    context_object_name = 'ativos'

    def get_queryset(self):
        # Filtra os ativos para mostrar apenas os do usuário logado
        return Ativo.objects.filter(usuario=self.request.user)
    
class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
    template_name = 'investimentos/editar_ativo.html'
    success_url = '/'  # Redireciona após a edição

class AtivoDeleteView(LoginRequiredMixin, DeleteView):
    model = Ativo
    template_name = 'investimentos/deletar_ativo.html'
    success_url = '/'  # Redireciona após a exclusão

