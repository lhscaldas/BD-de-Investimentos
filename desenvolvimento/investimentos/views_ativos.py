from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, SUBCLASSES_POR_CLASSE
from .forms import AtivoForm, UploadCSVForm
from django.contrib import messages
from django.shortcuts import redirect
import csv
import io
import json

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

    def get_success_url(self):
        """Redireciona para a página de origem (next) se existir, senão retorna para listar_ativos"""
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        return next_url if next_url else "/listar-ativos/"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Obtém a classe selecionada no formulário (POST ou GET)
        classe_selecionada = self.request.POST.get("classe") or self.request.GET.get("classe")
        
        # Se houver uma classe selecionada, filtra as subclasses disponíveis
        if classe_selecionada in SUBCLASSES_POR_CLASSE:
            form.fields['subclasse'].choices = [(sub, sub) for sub in SUBCLASSES_POR_CLASSE[classe_selecionada]]
        else:
            form.fields['subclasse'].choices = [(sub, sub) for sub_list in SUBCLASSES_POR_CLASSE.values() for sub in sub_list]

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Converte o dicionário para JSON e passa para o template
        context['subclasses_por_classe_json'] = json.dumps(SUBCLASSES_POR_CLASSE)
        return context
    
class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    form_class = AtivoForm  # Usa o formulário estilizado
    template_name = 'form_ativo.html'
    success_url = '/listar-ativos'

    def get_queryset(self):
        """Garante que o usuário só pode editar seus próprios ativos"""
        return Ativo.objects.filter(usuario=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Obtém a classe do ativo que está sendo editado
        classe_selecionada = self.object.classe

        # Se houver uma classe selecionada, filtra as subclasses disponíveis
        if classe_selecionada in SUBCLASSES_POR_CLASSE:
            form.fields['subclasse'].choices = [(sub, sub) for sub in SUBCLASSES_POR_CLASSE[classe_selecionada]]
        else:
            form.fields['subclasse'].choices = [(sub, sub) for sub_list in SUBCLASSES_POR_CLASSE.values() for sub in sub_list]

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Converte o dicionário para JSON e passa para o template
        context['subclasses_por_classe_json'] = json.dumps(SUBCLASSES_POR_CLASSE)
        return context

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
            reader = list(csv.DictReader(io.StringIO(decoded_file), delimiter=";"))  # Convertendo para lista

            if not reader:
                messages.error(self.request, "O arquivo CSV está vazio ou mal formatado.")
                return redirect("importar_ativos")

            ativos_importados = 0
            for row in reader:
                try:
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
                    ativos_importados += 1
                except Exception as e:
                    messages.error(self.request, f"Erro ao processar linha: {row}. Erro: {e}")

            if ativos_importados > 0:
                messages.success(self.request, f"{ativos_importados} ativos importados com sucesso!")
            else:
                messages.warning(self.request, "Nenhum ativo foi importado.")

        except Exception as e:
            messages.error(self.request, f"Erro ao processar o CSV: {e}")

        # Consumir mensagens antes do redirecionamento
        list(messages.get_messages(self.request))

        return super().form_valid(form)

