from django import forms
from .models import Ativo

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        exclude = ['usuario']  # Remove o campo usuario do formulário
        widgets = {
            'nome_do_ativo': forms.TextInput(attrs={'class': 'form-control'}),
            'classe_do_ativo': forms.Select(attrs={'class': 'form-select'}),
            'subclasse_do_ativo': forms.Select(attrs={'class': 'form-select'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'  # Define o formato correto para exibição
            ),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
