from django import forms
from .models import CentroDeCosto, Tercero, CodigoTurno
from django import forms
from django.contrib.auth.models import Group, Permission
from django import forms


class TerceroForm(forms.ModelForm):
    class Meta:
        model = Tercero
        fields = [
            'documento', 'correo_tercero', 'nombre_tercero', 'apellido_tercero',
            'cargo_predefinido', 'centro_operativo', 'unidad_negocio',
            'centro_de_costo', 'proyecto'
        ]

class CentroDeCostoForm(forms.ModelForm):
    class Meta:
        model = CentroDeCosto
        fields = [
            'codigo', 'nombre',
        ]


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }


class CodigoTurnoForm(forms.ModelForm):
    class Meta:
        model = CodigoTurno
        fields = [
            'letra_turno',
            'tipo',
            'hora_inicio',
            'hora_final',
            'duracion_total',
            'descripcion_novedad',
            'estado_codigo'
        ]
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_final': forms.TimeInput(attrs={'type': 'time'}),
        }