from django import forms
from .models import Ativo, Operacao, SUBCLASSES, SUBCLASSES_POR_CLASSE

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = ['nome', 'classe', 'subclasse', 'banco', 'valor_inicial', 'data_aquisicao', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'subclasse': forms.Select(attrs={'class': 'form-select'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'classe' in self.data:
            classe_selecionada = self.data.get('classe')
            subclasses_filtradas = SUBCLASSES_POR_CLASSE.get(classe_selecionada, [])
            self.fields['subclasse'].choices = [(sub, sub) for sub in subclasses_filtradas]
        else:
            self.fields['subclasse'].choices = SUBCLASSES


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
        ativo_id = kwargs.pop('ativo_id', None)  # Pega o ID do ativo da URL
        super().__init__(*args, **kwargs)
        self.fields['ativo'].queryset = Ativo.objects.filter(usuario=self.instance.usuario)
        self.fields = {k: self.fields[k] for k in ['ativo', 'tipo', 'valor', 'data']}

        if ativo_id:
            self.fields['ativo'].queryset = Ativo.objects.filter(id=ativo_id)  # Restringe o dropdown a esse ativo
            self.fields['ativo'].initial = ativo_id  # Preenche o campo com o ativo correto


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label="Selecione um arquivo CSV")