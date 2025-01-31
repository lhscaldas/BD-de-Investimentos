from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo
from .forms import AtivoForm


################################################
#                  Ativos                      #
################################################   

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'listar_ativos.html' 
    context_object_name = 'ativos'

    def get_queryset(self):
        # Filtra os ativos para mostrar apenas os do usuário logado
        return Ativo.objects.filter(usuario=self.request.user)

class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    form_class = AtivoForm  # Usa o formulário estilizado
    template_name = 'form_ativo.html'
    success_url = '/listar-ativos'

    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        return super().form_valid(form)
    
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