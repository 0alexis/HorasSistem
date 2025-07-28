from rest_framework import serializers
from .models import Empresa, UnidadNegocio, Proyecto, CentroOperativo, CargoPredefinido

def validate_text_no_script(value):
    # Ejemplo muy básico para rechazar etiquetas HTML o script
    if '<script>' in value.lower():
        raise serializers.ValidationError("El texto no puede contener etiquetas HTML o script.")
    return value

class EmpresaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(validators=[validate_text_no_script], max_length=200)
    nit = serializers.CharField(max_length=20)
    
    class Meta:
        model = Empresa
        fields = '__all__'

class UnidadNegocioSerializer(serializers.ModelSerializer):
    empresas_info = serializers.SerializerMethodField()
    nombre = serializers.CharField(validators=[validate_text_no_script], max_length=200)
    
    class Meta:
        model = UnidadNegocio
        fields = '__all__'

    def get_empresas_info(self, obj):
        return [
            {
                'id': empresa.id,
                'nombre': empresa.nombre,
                'nit': empresa.nit
            } for empresa in obj.empresas.all()
        ]

class ProyectoSerializer(serializers.ModelSerializer):
    unidades_negocio_info = serializers.SerializerMethodField()
    nombre = serializers.CharField(validators=[validate_text_no_script], max_length=200)
    
    class Meta:
        model = Proyecto
        fields = '__all__'

    def get_unidades_negocio_info(self, obj):
        return [
            {
                'id': unidad.id,
                'nombre': unidad.nombre,
                'empresas': [
                    {'id': emp.id, 'nombre': emp.nombre}
                    for emp in unidad.empresas.all()
                ]
            }
            for unidad in obj.unidades_negocio.all()
        ]

class CentroOperativoSerializer(serializers.ModelSerializer):
    proyectos_info = serializers.SerializerMethodField()
    promesa_valor = serializers.CharField(max_length=200)

    class Meta:
        model = CentroOperativo
        fields = '__all__'

    def get_proyectos_info(self, obj):
        return [
            {
                'id': proyecto.id_proyecto,
                'nombre': proyecto.nombre
            }
            for proyecto in obj.proyectos.all()
        ]

class CargoPredefinidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoPredefinido
        fields = '__all__'