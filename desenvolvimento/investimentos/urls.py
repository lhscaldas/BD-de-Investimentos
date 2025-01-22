from django.urls import path
from .views import AtivoCreateView, AtivoListView, AtivoUpdateView, AtivoDeleteView, OperacaoCreateView, OperacaoListView, OperacaoUpdateView, OperacaoDeleteView

urlpatterns = [
    path('criar-ativo/', AtivoCreateView.as_view(), name='criar_ativo'),
    path('listar-ativos/', AtivoListView.as_view(), name='listar_ativos'),
    path('editar-ativo/<int:pk>/', AtivoUpdateView.as_view(), name='editar_ativo'),
    path('deletar-ativo/<int:pk>/', AtivoDeleteView.as_view(), name='deletar_ativo'),

    path('criar-operacao/', OperacaoCreateView.as_view(), name='criar_operacao'),
    path('listar-operacoes/', OperacaoListView.as_view(), name='listar_operacoes'),
    path('editar-operacao/<int:pk>/', OperacaoUpdateView.as_view(), name='editar_operacao'),
    path('deletar-operacao/<int:pk>/', OperacaoDeleteView.as_view(), name='deletar_operacao'),
]