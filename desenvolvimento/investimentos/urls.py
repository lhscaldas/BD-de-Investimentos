from django.urls import path
from .views import AtivoCreateView, AtivoListView, AtivoUpdateView, AtivoDeleteView

urlpatterns = [
    path('criar-ativo/', AtivoCreateView.as_view(), name='criar_ativo'),
    path('listar-ativos/', AtivoListView.as_view(), name='listar_ativos'),
    path('editar-ativo/<int:pk>/', AtivoUpdateView.as_view(), name='editar_ativo'),
    path('deletar-ativo/<int:pk>/', AtivoDeleteView.as_view(), name='deletar_ativo'),

]