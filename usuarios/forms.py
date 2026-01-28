from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegistroUsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        # Función modificada para pedir los datos que queremos
        fields = ('username', 'email', 'telefono', 'direccion')


class RegistroUsuarioAdminForm(UserCreationForm):
    """Formulario para que el admin registre usuarios con rol asignado"""
    rol = forms.ChoiceField(
        choices=Usuario.ROLES,
        required=True,
        widget=forms.Select(attrs={'class': 'input-custom'})
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'telefono', 'direccion', 'rol')
