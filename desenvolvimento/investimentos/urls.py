from django.urls import path
from .views import AtivoCreateView, AtivoListView, AtivoUpdateView, AtivoDeleteView, ImportarAtivosView
from .views import OperacaoCreateView, OperacaoListView, OperacaoUpdateView, OperacaoDeleteView, ImportarOperacoesView
from .views import ResumoView, ResumoAtivoView

urlpatterns = [
    path('criar-ativo/', AtivoCreateView.as_view(), name='criar_ativo'),
    path('listar-ativos/', AtivoListView.as_view(), name='listar_ativos'),
    path('editar-ativo/<int:pk>/', AtivoUpdateView.as_view(), name='editar_ativo'),
    path('deletar-ativo/<int:pk>/', AtivoDeleteView.as_view(), name='deletar_ativo'),
    path("importar-ativos/", ImportarAtivosView.as_view(), name="importar_ativos"),

    path('criar-operacao/', OperacaoCreateView.as_view(), name='criar_operacao'),
    path('listar-operacoes/', OperacaoListView.as_view(), name='listar_operacoes'),
    path('editar-operacao/<int:pk>/', OperacaoUpdateView.as_view(), name='editar_operacao'),
    path('deletar-operacao/<int:pk>/', OperacaoDeleteView.as_view(), name='deletar_operacao'),
    path("importar-operacoes/", ImportarOperacoesView.as_view(), name="importar_operacoes"),

    path('', ResumoView.as_view(), name='resumo'),
    path('ativo/<int:pk>/', ResumoAtivoView.as_view(), name='resumo_ativo'),
]