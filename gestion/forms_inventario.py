from django import forms
from .models import Insumo


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'codigo', 'categoria', 'stock_actual',
                  'capacidad_maxima', 'unidad_medida', 'precio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input-modern', 'placeholder': 'Ej. Detergente Ariel'}),
            'codigo': forms.TextInput(attrs={'class': 'input-modern', 'placeholder': 'Lote-001'}),
            'categoria': forms.Select(attrs={'class': 'input-modern'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'input-modern'}),
            'capacidad_maxima': forms.NumberInput(attrs={'class': 'input-modern'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'input-modern', 'placeholder': 'Lts, Kg...'}),
            'precio': forms.NumberInput(attrs={'class': 'input-modern'}),
        }
