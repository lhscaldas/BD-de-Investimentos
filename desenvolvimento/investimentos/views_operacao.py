from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ativo, Operacao
from .forms import OperacaoForm, UploadCSVForm
from django.contrib import messages
from django.shortcuts import redirect
import csv
import io

class OperacaoListView(LoginRequiredMixin, ListView):
    model = Operacao
    template_name = 'listar_operacoes.html'
    context_object_name = 'operacoes'

    def get_queryset(self):
        # Mostra apenas operações do usuário logado
        queryset = Operacao.objects.filter(ativo__usuario=self.request.user)

        ativo_id = self.request.GET.get('ativo')
        tipo = self.request.GET.get('tipo')

        if ativo_id:
            queryset = queryset.filter(ativo_id=ativo_id)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset
    
    def get_context_data(self, **kwargs):
        """ Adiciona o TIPO_OPERACAO ao contexto do template """
        context = super().get_context_data(**kwargs)
        context['TIPO_OPERACAO'] = self.model.TIPO_OPERACAO  # Passa os choices para o template
        return context

class OperacaoCreateView(LoginRequiredMixin, CreateView):
    model = Operacao
    form_class = OperacaoForm
    template_name = 'form_operacao.html'
    success_url = '/listar-operacoes'

    def form_valid(self, form):
        form.instance.usuario = self.request.user  # Define o usuário logado
        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Filtrar ativos apenas do usuário logado
        form.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.request.user)
        return form

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
            reader = csv.DictReader(io.StringIO(decoded_file), delimiter=";")

            for row in reader:
                ativo_nome = row["Ativo"]
                tipo = row["Tipo"]
                data = row["Data"]
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

            messages.success(self.request, "Operações importadas com sucesso!")
        except Exception as e:
            messages.error(self.request, f"Erro ao processar o CSV: {e}")

        return super().form_valid(form)
