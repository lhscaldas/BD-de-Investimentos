from django import forms
from .models import Ativo, Operacao

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        exclude = ['usuario']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-select', 'id': 'id_classe'}),
            'subclasse': forms.Select(attrs={'class': 'form-select', 'id': 'id_subclasse'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Criar um dicionário com as subclasses organizadas por classe
        self.subclasses_dict = {classe: sublist for classe, sublist in Ativo.SUBCLASSES}

        # Se for edição, carregar as subclasses corretas
        classe_selecionada = self.instance.classe if self.instance.pk else None
        self.fields['subclasse'].choices = self.subclasses_dict.get(classe_selecionada, [])


class OperacaoForm(forms.ModelForm):
    class Meta:
        model = Operacao
        exclude = ['usuario']
        widgets = {
            'ativo': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.instance.usuario)
        # Reorder fields to have 'ativo' at the top
        self.fields = {k: self.fields[k] for k in ['ativo', 'tipo', 'valor', 'data']}