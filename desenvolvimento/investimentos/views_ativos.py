from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo
from .forms import AtivoForm, UploadCSVForm
from django.contrib import messages
from django.shortcuts import redirect
import csv
import io

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'listar_ativos.html' 
    context_object_name = 'ativos'

    def get_queryset(self):
        # Mostra apenas operações do usuário logado
        queryset = Ativo.objects.filter(usuario=self.request.user)
        
        # Lista de campos que podem ser filtrados
        filtros_validos = ['nome', 'classe', 'subclasse', 'banco']
        
        # Aplica os filtros somente se houver valores preenchidos
        filtros = {f"{k}__icontains": v for k, v in self.request.GET.items() if v and k in filtros_validos}
        
        return queryset.filter(**filtros)
    
    def get_context_data(self, **kwargs):
        """ Adiciona as opções de filtro ao contexto """
        context = super().get_context_data(**kwargs)
        usuario_ativos = Ativo.objects.filter(usuario=self.request.user)

        # Obtém valores únicos de Classe, Subclasse e Banco
        context['classes_disponiveis'] = usuario_ativos.values_list('classe', flat=True).distinct()
        context['subclasses_disponiveis'] = usuario_ativos.values_list('subclasse', flat=True).distinct()
        context['bancos_disponiveis'] = usuario_ativos.values_list('banco', flat=True).distinct()

        return context

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

class ImportarAtivosView(LoginRequiredMixin, FormView):
    template_name = "importar_ativos.html"
    form_class = UploadCSVForm
    success_url = "/listar-ativos/"

    def form_valid(self, form):
        csv_file = self.request.FILES.get("csv_file")

        if not csv_file.name.endswith(".csv"):
            messages.error(self.request, "O arquivo deve estar no formato CSV.")
            return redirect("importar_ativos")

        try:
            # Lê e processa o CSV
            decoded_file = csv_file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded_file), delimiter=";")

            for row in reader:
                nome = row["Nome"]
                classe = row["Classe"]
                subclasse = row["Subclasse"]
                banco = row["Banco"]
                valor_inicial = float(row["Valor Inicial"].replace("R$", "").replace(",", ".").strip())
                data_aquisicao = row["Data de Aquisição"]

                # Criar o ativo no banco de dados
                Ativo.objects.create(
                    usuario=self.request.user,
                    nome=nome,
                    classe=classe,
                    subclasse=subclasse,
                    banco=banco,
                    valor_inicial=valor_inicial,
                    data_aquisicao=data_aquisicao
                )

            messages.success(self.request, "Ativos importados com sucesso!")
        except Exception as e:
            messages.error(self.request, f"Erro ao processar o CSV: {e}")

        return super().form_valid(form)