from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from .forms import OperacaoForm, UploadCSVForm
from django.contrib import messages
from django.shortcuts import redirect
import csv
import io
from datetime import datetime

class OperacaoListView(LoginRequiredMixin, ListView):
    model = Operacao
    template_name = 'listar_operacoes.html'
    context_object_name = 'operacoes'

    def get_queryset(self):
        # Mostra apenas operações do usuário logado
        queryset = Operacao.objects.filter(ativo__usuario=self.request.user)

        ativo_id = self.request.GET.get('ativo')
        tipo = self.request.GET.get('tipo')
        classe = self.request.GET.get("classe")
        subclasse = self.request.GET.get("subclasse")
        banco = self.request.GET.get("banco")

        if ativo_id:
            queryset = queryset.filter(ativo_id=ativo_id)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
    
        if classe:
            queryset = queryset.filter(ativo__classe=classe)

        if subclasse:
            queryset = queryset.filter(ativo__subclasse=subclasse)

        if banco:
            queryset = queryset.filter(ativo__banco=banco)


        return queryset
    
    def get_context_data(self, **kwargs):
        """ Adiciona o TIPO_OPERACAO ao contexto do template """
        context = super().get_context_data(**kwargs)
        context['TIPO_OPERACAO'] = self.model.TIPO_OPERACAO
        context["classes"] = (
            Ativo.objects.filter(operacoes__usuario=self.request.user)
            .values_list("classe", flat=True)
            .distinct()
        )
        context["subclasses"] = (
            Ativo.objects.filter(operacoes__usuario=self.request.user)
            .values_list("subclasse", flat=True)
            .distinct()
        )
        context["bancos"] = (
            Ativo.objects.filter(operacoes__usuario=self.request.user)
            .values_list("banco", flat=True)
            .distinct()
        )
        return context
    
import logging
logger = logging.getLogger(__name__)

class OperacaoCreateView(LoginRequiredMixin, CreateView):
    model = Operacao
    form_class = OperacaoForm
    template_name = 'form_operacao.html'
    
    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        response = super().form_valid(form)
        return response

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Filtrar ativos apenas do usuário logado
        form.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.request.user)
        return form
    
    def get_success_url(self):
        """Redireciona para a página de origem (next) se existir, senão retorna para listar_operacoes"""
        next_url = self.request.POST.get("next") or self.request.GET.get("next")

        return next_url if next_url else "/listar-operacoes/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        ativo_id = self.request.GET.get("ativo")  # Obtém o ID do ativo da URL
        if ativo_id:
            kwargs['ativo_id'] = ativo_id  # Passa para o form
        return kwargs


class OperacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Operacao
    form_class = OperacaoForm
    template_name = 'form_operacao.html'
    success_url = '/listar-operacoes'

    def get_queryset(self):
        """Garante que o usuário só pode editar as operações dele"""
        return Operacao.objects.filter(usuario=self.request.user)

class OperacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Operacao
    template_name = 'deletar_operacao.html'
    success_url = '/listar-operacoes'

class ImportarOperacoesView(LoginRequiredMixin, FormView):
    template_name = "importar_operacoes.html"
    form_class = UploadCSVForm
    success_url = '/listar-operacoes'

    def form_valid(self, form):
        csv_file = self.request.FILES.get("csv_file")

        if not csv_file.name.endswith(".csv"):
            messages.error(self.request, "O arquivo deve estar no formato CSV.")
            return redirect("importar_operacoes")

        try:
            # Lê e processa o CSV
            decoded_file = csv_file.read().decode("utf-8")
            reader = list(csv.DictReader(io.StringIO(decoded_file), delimiter=";"))  # Convertendo para lista para depuração

            if not reader:
                messages.error(self.request, "O arquivo CSV está vazio ou mal formatado.")
                return redirect("importar_operacoes")

            linhas_importadas = 0
            for row in reader:
                try:
                    ativo_nome = row["Ativo"]
                    tipo = row["Tipo"]
                    data = datetime.strptime(row["Data"], "%Y-%m-%d").date()
                    valor = float(row["Valor"].replace("R$", "").replace(",", ".").strip())

                    # Verifica se o ativo existe
                    ativo = Ativo.objects.filter(nome=ativo_nome, usuario=self.request.user).first()
                    if not ativo:
                        messages.warning(self.request, f"Ativo '{ativo_nome}' não encontrado. Operação ignorada.")
                        continue  # Pula esta linha se o ativo não for encontrado

                    # Criar a operação no banco de dados
                    Operacao.objects.create(
                        usuario=self.request.user,
                        ativo=ativo,
                        tipo=tipo,
                        data=data,
                        valor=valor
                    )
                    linhas_importadas += 1  # Conta quantas operações foram importadas
                except Exception as e:
                    messages.error(self.request, f"Erro ao processar linha: {row}. Erro: {e}")

            if linhas_importadas > 0:
                messages.success(self.request, f"{linhas_importadas} operações importadas com sucesso!")
            else:
                messages.warning(self.request, "Nenhuma operação foi importada.")

        except Exception as e:
            messages.error(self.request, f"Erro ao processar o CSV: {e}")

        # Consumir mensagens antes do redirecionamento
        list(messages.get_messages(self.request))

        return super().form_valid(form)

