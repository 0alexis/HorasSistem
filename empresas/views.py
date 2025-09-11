"""
=========================================================================
NO MODIFICAR ESTE CÓDIGO.
Este archivo es funcional y cualquier cambio puede afectar el sistema.
=========================================================================
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import OperationalError
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView
from django.urls import reverse_lazy

from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Empresa, Proyecto, CentroOperativo
from .forms import EmpresaFiltroForm, EmpresaForm, ProyectoForm

# =======================
#   APIs DE SISTEMA
# =======================

@api_view(['GET'])
def database_health_check(request):
    """Verificar salud de la base de datos"""
    try:
        count = Empresa.objects.count()
        return Response(
            {"status": "healthy", "empresas_count": count},
            status=status.HTTP_200_OK
        )
    except OperationalError:
        return Response(
            {"status": "unhealthy", "message": "Database connection failed"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@login_required
def debug_models_info(request):
    """Vista para verificar los campos del modelo Empresa"""
    info = {'empresa_fields': [], 'total_empresas': 0}
    try:
        for field in Empresa._meta.get_fields():
            info['empresa_fields'].append({
                'name': field.name,
                'type': str(type(field).__name__),
                'related': hasattr(field, 'related_model')
            })
        info['total_empresas'] = Empresa.objects.count()
    except Exception as e:
        info['error'] = str(e)
    return JsonResponse(info, indent=2)

# =======================
#       DASHBOARD
# =======================

@login_required
def empresas_dashboard(request):
    """Dashboard del módulo Empresas con métricas completas"""
     
     # Fecha actual y hace un mes
    ahora = timezone.now()
        
    hace_un_mes = ahora - timedelta(days=30)
        
    context = {
            'total_empresas': Empresa.objects.count(),
            'empresa_activa': Empresa.objects.filter(activo=True).count(),
            'empresas_inactivas': Empresa.objects.filter(activo=False).count(),
            'empresas_mes_actual': Empresa.objects.filter(creado_en__gte=hace_un_mes).count(),
            'empresas_recientes': Empresa.objects.all().order_by('-creado_en')[:10],


 # Métricas de Proyectos
            'proyectos_activos': Proyecto.objects.filter(activo=True).count(),
            'total_proyectos': Proyecto.objects.count(),

            # Métricas de Centros Operativos
            'centros_operativos_activos': CentroOperativo.objects.filter(activo=True).count(),
            'total_centros_operativos': CentroOperativo.objects.count(),

        # Usuario actual
            'user': request.user,
        }
        
    return render(request, 'dashboard.html', context)

# =======================
#     CRUD DE EMPRESAS
# =======================

@login_required
def empresas_list(request):
    """Lista de empresas con filtros y búsqueda (incluye redirección por NIT)"""
    try:
        form = EmpresaFiltroForm(request.GET or None)
        empresas = Empresa.objects.all().order_by('-id_empresa')
        
        # Verificar si es una búsqueda por NIT exacto para redirección directa
        if form.is_valid():
            search = form.cleaned_data.get('search')
            
            # Redirección directa por NIT exacto
            if search and form.is_nit_search():
                empresa = form.get_empresa_by_nit()
                if empresa:
                    messages.success(request, f'🎯 Empresa encontrada: {empresa.nombre}')
                    return redirect('empresas:empresa_detail', pk=empresa.id_empresa)
                else:
                    messages.warning(request, f'❌ No se encontró empresa con NIT: {search}')
            
            # Filtros normales si no es búsqueda por NIT o no se encontró
            if search:
                empresas = empresas.filter(
                    Q(nombre__icontains=search) | 
                    Q(nit__icontains=search) | 
                    Q(email__icontains=search)
                )
            
            # Filtro por estado
            activo = form.cleaned_data.get('activo')
            if activo == 'true':
                empresas = empresas.filter(activo=True)
            elif activo == 'false':
                empresas = empresas.filter(activo=False)
            
            # Ordenamiento
            ordenar_por = form.cleaned_data.get('ordenar_por')
            if ordenar_por:
                empresas = empresas.order_by(ordenar_por)
        
        # Paginación
        paginator = Paginator(empresas, 10)
        page_number = request.GET.get('page')
        empresas_page = paginator.get_page(page_number)
        
        # Variables para mantener compatibilidad con template existente
        search = request.GET.get('search', '')
        activo = request.GET.get('activo', '')
        
        context = {
            'form': form,
            'empresas': empresas_page,
            'search': search,
            'activo': activo,
            'total_empresas': empresas.count(),
            'is_filtered': bool(search or activo)
        }
        
    except Exception as e:
        messages.error(request, f'Error al cargar empresas: {str(e)}')
        context = {
            'form': EmpresaFiltroForm(),
            'empresas': [],
            'search': '',
            'activo': '',
            'total_empresas': 0,
            'is_filtered': False
        }
    
    return render(request, 'empresas/empresas_list.html', context)

@login_required
def empresa_create(request):
    """Crear nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            try:
                empresa = form.save()
                messages.success(request, f'Empresa "{empresa.nombre}" creada exitosamente.')
                return redirect('empresas:empresa_detail', pk=empresa.pk)
            except Exception as e:
                messages.error(request, f'Error al crear empresa: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EmpresaForm()
    return render(request, 'empresas/empresa_form.html', {'form': form, 'title': 'Nueva Empresa', 'action': 'Crear'})

@login_required
def empresa_detail(request, pk):
    """Detalle de empresa"""
    try:
        empresa = get_object_or_404(Empresa, pk=pk)
        context = {'empresa': empresa}
    except Exception as e:
        messages.error(request, f'Error al cargar empresa: {str(e)}')
        return redirect('empresas:empresas_list')
    return render(request, 'empresas/empresa_detail.html', context)

@login_required
def empresa_update(request, pk):
    """Editar empresa"""
    try:
        empresa = get_object_or_404(Empresa, pk=pk)
        if request.method == 'POST':
            form = EmpresaForm(request.POST, instance=empresa)
            if form.is_valid():
                empresa = form.save()
                messages.success(request, f'Empresa "{empresa.nombre}" actualizada exitosamente.')
                return redirect('empresas:empresa_detail', pk=empresa.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = EmpresaForm(instance=empresa)
        return render(request, 'empresas/empresa_form.html', {'form': form, 'title': f'Editar Empresa: {empresa.nombre}', 'action': 'Actualizar', 'empresa': empresa})
    except Exception as e:
        messages.error(request, f'Error al editar empresa: {str(e)}')
        return redirect('empresas:empresas_list')
    
@login_required
def empresa_delete(request, pk):
    """Eliminar empresa"""
    try:
        empresa = get_object_or_404(Empresa, pk=pk)
        if request.method == 'POST':
            empresa_nombre = empresa.nombre
            empresa.delete()
            messages.success(request, f'Empresa "{empresa_nombre}" eliminada exitosamente.')
            return redirect('empresas:empresas_list')
        return render(request, 'empresas/empresa_confirm_delete.html', {'empresa': empresa})
    except Exception as e:
        messages.error(request, f'Error al eliminar empresa: {str(e)}')
        return redirect('empresas:empresas_list')

@login_required
def proyecto_detail(request, pk):
    """Detalle de proyecto"""
    try:
        proyecto = get_object_or_404(
            Proyecto.objects.select_related('id_proyecto').prefetch_related('centros_operativos'),
            pk=pk
        )
        
        # ✅ OBTENER CENTROS OPERATIVOS CORRECTAMENTE
        # La relación está en CentroOperativo -> proyectos (ManyToMany)
        centros_operativos = CentroOperativo.objects.filter(proyectos=proyecto)
        
        context = {
            'proyecto': proyecto,
            # ✅ AGREGAR ESTAS VARIABLES QUE EL TEMPLATE ESPERA
            'centros_operativos': centros_operativos,
            'centros_count': centros_operativos.count(),
            # Variables adicionales
            'total_centros': centros_operativos.count(),
            'centros_activos': centros_operativos.filter(activo=True).count(),
        }
        
    except Exception as e:
        messages.error(request, f'Error al cargar proyecto: {str(e)}')
        return redirect('empresas:proyectos_list')
    
    return render(request, 'proyectos/proyecto_detail.html', context)

@login_required
def empresa_update(request, pk):
    """Editar empresa"""
    try:
        empresa = get_object_or_404(Empresa, pk=pk)
        if request.method == 'POST':
            form = EmpresaForm(request.POST, instance=empresa)
            if form.is_valid():
                empresa = form.save()
                messages.success(request, f'Empresa "{empresa.nombre}" actualizada exitosamente.')
                return redirect('empresas:empresa_detail', pk=empresa.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = EmpresaForm(instance=empresa)
        return render(request, 'empresas/empresa_form.html', {'form': form, 'title': f'Editar Empresa: {empresa.nombre}', 'action': 'Actualizar', 'empresa': empresa})
    except Exception as e:
        messages.error(request, f'Error al editar empresa: {str(e)}')
        return redirect('empresas:empresas_list')

@login_required
def empresa_delete(request, pk):
    """Eliminar empresa"""
    try:
        empresa = get_object_or_404(Empresa, pk=pk)
        if request.method == 'POST':
            empresa_nombre = empresa.nombre
            empresa.delete()
            messages.success(request, f'Empresa "{empresa_nombre}" eliminada exitosamente.')
            return redirect('empresas:empresas_list')
        return render(request, 'empresas/empresa_confirm_delete.html', {'empresa': empresa})
    except Exception as e:
        messages.error(request, f'Error al eliminar empresa: {str(e)}')
        return redirect('empresas:empresas_list')

# =======================
#         APIs
# =======================

@login_required
def empresas_activas_api(request):
    """API para obtener empresas activas"""
    try:
        empresas = Empresa.objects.filter(activo=True).values('id_empresa', 'nombre')
        return JsonResponse({'empresas': list(empresas)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =======================
#     CRUD DE PROYECTOS (EN DESARROLLO)
# =======================


@login_required
def proyectos_list(request):
    """Lista de proyectos"""
    try:
        from .models import Proyecto, UnidadNegocio
        from django.db import models
        
        # Obtener parámetros de filtro
        search = request.GET.get('search', '')
        activo = request.GET.get('activo', '')
        unidad_negocio = request.GET.get('unidad_negocio', '')
        
        # Base queryset
        proyectos = Proyecto.objects.all()
        
        # Aplicar filtros
        if search:
            proyectos = proyectos.filter(
                models.Q(nombre__icontains=search) |
                models.Q(descripcion__icontains=search) |
                models.Q(ubicacion__icontains=search)
            )
        
        if activo == 'true':
            proyectos = proyectos.filter(activo=True)
        elif activo == 'false':
            proyectos = proyectos.filter(activo=False)
            
        if unidad_negocio:
            proyectos = proyectos.filter(unidad_negocio_id=unidad_negocio)
        
        # Ordenar y paginar
        proyectos = proyectos.order_by('-id_proyecto')
        paginator = Paginator(proyectos, 10)
        page_number = request.GET.get('page')
        proyectos_page = paginator.get_page(page_number)
        
        # Datos adicionales
        unidades_disponibles = UnidadNegocio.objects.filter(activo=True).order_by('nombre')
        total_proyectos = Proyecto.objects.count()
        is_filtered = bool(search or activo or unidad_negocio)
        
        context = {
            'proyectos': proyectos_page,
            'search': search,
            'activo': activo,
            'unidad_negocio': unidad_negocio,
            'unidades_disponibles': unidades_disponibles,
            'total_proyectos': total_proyectos,
            'is_filtered': is_filtered,
        }
        
    except Exception as e:
        messages.error(request, f'Error al cargar proyectos: {str(e)}')
        context = {
            'proyectos': [],
            'total_proyectos': 0,
            'unidades_disponibles': [],
            'is_filtered': False,
        }
    
    
    return render(request, 'proyectos/proyecto_list.html', context)

@login_required
def proyecto_create(request):
    """Crear nuevo proyecto"""
    try:
        from .forms import ProyectoForm
        
        if request.method == 'POST':
            form = ProyectoForm(request.POST)
            if form.is_valid():
                proyecto = form.save()
                messages.success(request, f'✅ Proyecto "{proyecto.nombre}" creado exitosamente!')
                return redirect('empresas:proyecto_detail', pk=proyecto.id_proyecto)
            else:
                messages.error(request, '❌ Error al crear el proyecto. Revise los campos marcados.')
        else:
            form = ProyectoForm()
        
        context = {
            'form': form,
            'title': 'Nuevo Proyecto',
            'action': 'Crear'
        }
        
    except Exception as e:
        messages.error(request, f'Error al crear proyecto: {str(e)}')
        return redirect('empresas:proyectos_list')
    
    return render(request, 'proyectos/proyecto_form.html', context)


@login_required
def proyecto_detail(request, pk):
    """Detalle de proyecto"""
    try:
        proyecto = get_object_or_404(
            # ✅ CORREGIR LA RELACIÓN
            Proyecto.objects.select_related('id_empresa_proyecto'),
            pk=pk
        )
        
        # ✅ OBTENER CENTROS OPERATIVOS CORRECTAMENTE
        # La relación está en CentroOperativo -> proyectos (ManyToMany)
        centros_operativos = CentroOperativo.objects.filter(proyectos=proyecto)
        
        context = {
            'proyecto': proyecto,
            # ✅ VARIABLES QUE EL TEMPLATE ESPERA
            'centros_operativos': centros_operativos,
            'centros_count': centros_operativos.count(),
            'centros_activos': centros_operativos.filter(activo=True).count(),
            'total_centros': centros_operativos.count(),
        }
        
    except Exception as e:
        messages.error(request, f'Error al cargar proyecto: {str(e)}')
        return redirect('empresas:proyectos_list')
    
    return render(request, 'proyectos/proyecto_detail.html', context)

@login_required
def proyecto_update(request, pk):
    """Actualizar proyecto"""
    try:
        proyecto = get_object_or_404(Proyecto, pk=pk)
        
        if request.method == 'POST':
            form = ProyectoForm(request.POST, instance=proyecto)  # ✅ PASAR INSTANCE
            if form.is_valid():
                proyecto_actualizado = form.save()
                messages.success(request, f'✅ Proyecto "{proyecto_actualizado.nombre}" actualizado exitosamente!')
                return redirect('empresas:proyecto_detail', pk=proyecto_actualizado.pk)
        else:
            form = ProyectoForm(instance=proyecto)  # ✅ PASAR INSTANCE AL GET
        
        context = {
            'form': form,
            'proyecto': proyecto,  # ✅ PASAR EL PROYECTO TAMBIÉN
        }
        
    except Exception as e:
        messages.error(request, f'Error al actualizar proyecto: {str(e)}')
        return redirect('empresas:proyectos_list')
    
    return render(request, 'proyectos/proyecto_form.html', context)

# ✅ REEMPLAZAR LA VISTA proyecto_delete CON ESTA:
@login_required
def proyecto_delete(request, pk):
    """Eliminar proyecto con confirmación"""
    try:
        proyecto = get_object_or_404(Proyecto, pk=pk)
        
        # Obtener centros operativos asociados para mostrar en la confirmación
        centros_operativos = CentroOperativo.objects.filter(proyectos=proyecto)
        
        if request.method == 'POST':
            # Nombre del proyecto para el mensaje
            nombre_proyecto = proyecto.nombre
            
            # Eliminar el proyecto (las relaciones M2M se eliminan automáticamente)
            proyecto.delete()
            
            messages.success(
                request, 
                f'✅ Proyecto "{nombre_proyecto}" eliminado exitosamente.'
            )
            return redirect('empresas:proyectos_list')
        
        context = {
            'object': proyecto,  # ✅ USAR 'object' COMO ESPERA EL TEMPLATE
            'centros_operativos': centros_operativos,
            'centros_count': centros_operativos.count(),
        }
        
    except Exception as e:
        messages.error(request, f'Error al eliminar proyecto: {str(e)}')
        return redirect('empresas:proyectos_list')
    
    # ✅ APUNTAR AL TEMPLATE CORRECTO
    return render(request, 'proyectos/proyecto_delete.html', context)


# =======================
#  API PARA PROYECTOS
# =======================

@login_required
def proyectos_activos_api(request):
    """API para obtener proyectos activos"""
    try:
        proyectos = Proyecto.objects.filter(activo=True).values(
            'id_proyecto', 
            'nombre', 
            'id_empresa_proyecto__nombre'
        )
        return JsonResponse({'proyectos': list(proyectos)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def proyecto_centros_api(request, pk):
    """API para obtener centros operativos de un proyecto"""
    try:
        proyecto = get_object_or_404(Proyecto, pk=pk)
        centros = proyecto.centros_operativos.filter(activo=True).values(
            'id_centro',
            'nombre',
            'ciudad'
        )
        return JsonResponse({
            'proyecto': proyecto.nombre,
            'centros': list(centros),
            'total': centros.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =======================
#  CRUD DE CENTROS OPERATIVOS - IMPLEMENTACIÓN COMPLETA
# =======================

@login_required
def centros_operativos_list(request):
    """Lista de centros operativos con filtros y búsqueda"""
    try:
        centros = CentroOperativo.objects.all().order_by('-id_centro')
        
        # Filtros de búsqueda
        search = request.GET.get('search', '')
        if search:
            centros = centros.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search) |
                Q(direccion__icontains=search) |
                Q(ciudad__icontains=search)
            )
        
        # Filtro por estado activo
        activo = request.GET.get('activo', '')
        if activo == 'true':
            centros = centros.filter(activo=True)
        elif activo == 'false':
            centros = centros.filter(activo=False)
        
        # Filtro por ciudad
        ciudad = request.GET.get('ciudad', '')
        if ciudad:
            centros = centros.filter(ciudad__icontains=ciudad)
        
        # Paginación
        paginator = Paginator(centros, 15)
        page_number = request.GET.get('page')
        centros_page = paginator.get_page(page_number)
        
        # Ciudades disponibles para filtro
        ciudades_disponibles = CentroOperativo.objects.values_list('ciudad', flat=True).distinct().order_by('ciudad')
        
        context = {
            'centros': centros_page,
            'ciudades_disponibles': ciudades_disponibles,
            'search': search,
            'ciudad': ciudad,
            'activo': activo,
            'total_centros': centros.count(),
            'is_filtered': bool(search or ciudad or activo)
        }
        
    except Exception as e:
        messages.error(request, f'Error al cargar centros operativos: {str(e)}')
        context = {
            'centros': [],
            'ciudades_disponibles': [],
            'search': '',
            'ciudad': '',
            'activo': '',
            'total_centros': 0,
            'is_filtered': False
        }
    
    return render(request, 'centro_operativo/centrooperativo_list.html', context)


@login_required
def centro_operativo_create(request):
    """Crear nuevo centro operativo"""
    try:
        from .forms import CentroOperativoForm
        
        if request.method == 'POST':
            # ✅ PASAR EL USUARIO AL FORMULARIO
            form = CentroOperativoForm(request.POST, user=request.user)
            if form.is_valid():
                centro = form.save()
                messages.success(request, f'✅ Centro Operativo "{centro.nombre}" creado exitosamente!')
                return redirect('empresas:centro_operativo_detail', pk=centro.id_centro)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            # ✅ PASAR EL USUARIO AL FORMULARIO
            form = CentroOperativoForm(user=request.user)
        
        context = {
            'form': form,
            'title': 'Nuevo Centro Operativo',
            'action': 'Crear',
            'centro': None,
            'usuario_responsable': request.user  # ✅ AÑADIR USUARIO AL CONTEXTO
        }
        
    except Exception as e:
        messages.error(request, f'Error al crear centro operativo: {str(e)}')
        return redirect('empresas:centros_operativos_list')
    
    return render(request, 'centro_operativo/centrooperativo_form.html', context)

@login_required
def centro_operativo_update(request, pk):
    """Editar centro operativo"""
    try:
        from .forms import CentroOperativoForm
        
        centro = get_object_or_404(CentroOperativo, pk=pk)
        
        if request.method == 'POST':
            # ✅ PASAR EL USUARIO AL FORMULARIO
            form = CentroOperativoForm(request.POST, instance=centro, user=request.user)
            if form.is_valid():
                centro = form.save()
                messages.success(request, f'✅ Centro Operativo "{centro.nombre}" actualizado exitosamente!')
                return redirect('empresas:centro_operativo_detail', pk=centro.id_centro)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            # ✅ PASAR EL USUARIO AL FORMULARIO
            form = CentroOperativoForm(instance=centro, user=request.user)
        
        context = {
            'form': form,
            'title': f'Editar Centro: {centro.nombre}',
            'action': 'Actualizar',
            'centro': centro,
            'usuario_responsable': request.user  # ✅ AÑADIR USUARIO AL CONTEXTO
        }
        
    except Exception as e:
        messages.error(request, f'Error al editar centro operativo: {str(e)}')
        return redirect('empresas:centros_operativos_list')
    
    return render(request, 'centro_operativo/centrooperativo_form.html', context)

@login_required
def centro_operativo_detail(request, pk):
    """Detalle de centro operativo"""
    try:
        centro = get_object_or_404(CentroOperativo, pk=pk)
        context = {'centro': centro}
    except Exception as e:
        messages.error(request, f'Error al cargar centro operativo: {str(e)}')
        return redirect('empresas:centros_operativos_list')
    # ✅ CAMBIAR ESTA LÍNEA
    return render(request, 'centro_operativo/centrooperativo_detail.html', context)

@login_required
def centro_operativo_delete(request, pk):
    """Eliminar centro operativo"""
    try:
        centro = get_object_or_404(CentroOperativo, pk=pk)
        
        if request.method == 'POST':
            centro_nombre = centro.nombre
            centro.delete()
            messages.success(request, f'✅ Centro Operativo "{centro_nombre}" eliminado exitosamente!')
            return redirect('empresas:centros_operativos_list')
        
        context = {'centro': centro}
        
    except Exception as e:
        messages.error(request, f'Error al eliminar centro operativo: {str(e)}')
        return redirect('empresas:centros_operativos_list')
    
    # ✅ CAMBIAR ESTA LÍNEA
    return render(request, 'centro_operativo/centrooperativo_confirm_delete.html', context)


# =======================
#  CRUD DE UNIDADES DE NEGOCIO (EN DESARROLLO)
# =======================

@login_required
def unidades_negocio_list(request):
    """Lista de unidades de negocio"""
    try:
        from .models import UnidadNegocio
        unidades = UnidadNegocio.objects.all().order_by('-id')
        paginator = Paginator(unidades, 10)
        page_number = request.GET.get('page')
        unidades_page = paginator.get_page(page_number)
        context = {'unidades_negocio': unidades_page}
    except:
        context = {'unidades_negocio': [], 'mensaje': 'En desarrollo'}
    return render(request, 'empresas/unidades_negocio_list.html', context)

@login_required
def unidad_negocio_create(request):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Unidades de Negocio'})

@login_required
def unidad_negocio_detail(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Unidades de Negocio'})

@login_required
def unidad_negocio_update(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Unidades de Negocio'})

@login_required
def unidad_negocio_delete(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Unidades de Negocio'})





class EmpresaDetailView(DetailView):
    model = Empresa
    template_name = 'empresas/empresa_detail.html'
    context_object_name = 'empresa'
##DETALLE DE LA EMPRESA, TAMBIEN EDITAR DETALLES Y ACTUALIZARLE##
class EmpresaCreateView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Empresa "{form.instance.nombre}" creada exitosamente!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirige al detalle de la empresa recién creada
        return reverse_lazy('empresas:empresa_detail', kwargs={'pk': self.object.pk})

class EmpresaUpdateView(UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Empresa "{form.instance.nombre}" actualizada exitosamente!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirige al detalle de la empresa editada
        return reverse_lazy('empresas:empresa_detail', kwargs={'pk': self.object.pk})
    

# =======================
#  CRUD DE CARGOS PREDEFINIDOS - IMPLEMENTACIÓN COMPLETA
# =======================
# Vista para listar, crear, editar y eliminar cargos predefinidos

@login_required
def cargopredefinido_list(request):
    """Lista de cargos predefinidos con filtros y búsqueda"""
    try:
        from .models import CargoPredefinido
        cargos = CargoPredefinido.objects.all().order_by('-id_cargo_predefinido')
        
        # Filtros de búsqueda
        search = request.GET.get('search', '')
        if search:
            cargos = cargos.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search) |
                Q(estado_cargo__icontains=search)
            )
        
        # Filtro por estado activo
        activo = request.GET.get('activo', '')
        if activo == 'true':
            cargos = cargos.filter(activo=True)
        elif activo == 'false':
            cargos = cargos.filter(activo=False)
        
        # Paginación
        paginator = Paginator(cargos, 15)
        page_number = request.GET.get('page')
        cargos_page = paginator.get_page(page_number)
        
        # Cargos activos para estadísticas
        cargos_activos = CargoPredefinido.objects.filter(activo=True)
        
        context = {
            'cargos': cargos_page,
            'cargos_activos': cargos_activos,
            'search': search,
            'activo': activo,
            'total_cargos': cargos.count(),
            'is_filtered': bool(search or activo)
        }
    except Exception as e:
        messages.error(request, f'Error al cargar cargos predefinidos: {str(e)}')
        context = {
            'cargos': [],
            'cargos_activos': [],
            'search': '',
            'activo': '',
            'total_cargos': 0,
            'is_filtered': False
        }
    
    return render(request, 'cargo/cargopredefinido_list.html', context)


@login_required
def cargopredefinido_detail(request, pk):
    """Detalle de cargo predefinido"""
    try:
        from .models import CargoPredefinido
        cargo = get_object_or_404(CargoPredefinido, pk=pk)
        context = {'cargo': cargo}
    except Exception as e:
        messages.error(request, f'Error al cargar cargo predefinido: {str(e)}')
        return redirect('empresas:cargopredefinido_list')
    return render(request, 'cargo/cargopredefinido_detail.html', context)

@login_required
def cargopredefinido_create(request):
    """Crear nuevo cargo predefinido"""
    try:
        from .models import CargoPredefinido
        from .forms import CargoPredefinidoForm
        
        if request.method == 'POST':
            form = CargoPredefinidoForm(request.POST)
            if form.is_valid():
                cargo = form.save()
                messages.success(request, f'✅ Cargo "{cargo.nombre}" creado exitosamente!')
                return redirect('empresas:cargopredefinido_detail', pk=cargo.id_cargo_predefinido)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = CargoPredefinidoForm()
        
        context = {
            'form': form,
            'title': 'Nuevo Cargo Predefinido',
            'action': 'Crear',
            'cargo': None
        }
        
    except Exception as e:
        messages.error(request, f'Error al crear cargo predefinido: {str(e)}')
        return redirect('empresas:cargopredefinido_list')
    
    return render(request, 'cargo/cargopredefinido_form.html', context)

@login_required
def cargopredefinido_update(request, pk):
    """Editar cargo predefinido"""
    try:
        from .models import CargoPredefinido
        from .forms import CargoPredefinidoForm
        
        cargo = get_object_or_404(CargoPredefinido, pk=pk)
        
        if request.method == 'POST':
            form = CargoPredefinidoForm(request.POST, instance=cargo)
            if form.is_valid():
                cargo = form.save()
                messages.success(request, f'✅ Cargo "{cargo.nombre}" actualizado exitosamente!')
                return redirect('empresas:cargopredefinido_detail', pk=cargo.id_cargo_predefinido)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = CargoPredefinidoForm(instance=cargo)
        
        context = {
            'form': form,
            'title': f'Editar Cargo: {cargo.nombre}',
            'action': 'Actualizar',
            'cargo': cargo
        }
        
    except Exception as e:
        messages.error(request, f'Error al editar cargo predefinido: {str(e)}')
        return redirect('empresas:cargopredefinido_list')
    
    return render(request, 'cargo/cargopredefinido_form.html', context)

@login_required
def cargopredefinido_delete(request, pk):
    """Eliminar cargo predefinido"""
    try:
        from .models import CargoPredefinido
        cargo = get_object_or_404(CargoPredefinido, pk=pk)
        
        if request.method == 'POST':
            cargo_nombre = cargo.nombre
            cargo.delete()
            messages.success(request, f'✅ Cargo "{cargo_nombre}" eliminado exitosamente!')
            return redirect('empresas:cargopredefinido_list')
        
        context = {'cargo': cargo}
        
    except Exception as e:
        messages.error(request, f'Error al eliminar cargo predefinido: {str(e)}')
        return redirect('empresas:cargopredefinido_list')
    
    return render(request, 'cargo/cargopredefinido_confirm_delete.html', context)


        
# Vistas basadas en clases para CargoPredefinido (alternativa)
class CargoPredefinidoListView(ListView):
    template_name = 'cargo/cargopredefinido_list.html'
    context_object_name = 'cargos'
    paginate_by = 15
    
    def get_queryset(self):
        from .models import CargoPredefinido
        queryset = CargoPredefinido.objects.all().order_by('-id_cargo_predefinido')
        
        # Filtros de búsqueda
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search) |
                Q(estado_cargo__icontains=search)
            )
        
        # Filtro por estado activo
        activo = self.request.GET.get('activo', '')
        if activo == 'true':
            queryset = queryset.filter(activo=True)
        elif activo == 'false':
            queryset = queryset.filter(activo=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        from .models import CargoPredefinido
        context = super().get_context_data(**kwargs)
        context['cargos_activos'] = CargoPredefinido.objects.filter(activo=True)
        context['search'] = self.request.GET.get('search', '')
        context['activo'] = self.request.GET.get('activo', '')
        context['total_cargos'] = self.get_queryset().count()
        context['is_filtered'] = bool(context['search'] or context['activo'])
        return context

class CargoPredefinidoDetailView(DetailView):
    template_name = 'cargo/cargopredefinido_detail.html'
    context_object_name = 'cargo'
    
    def get_queryset(self):
        from .models import CargoPredefinido
        return CargoPredefinido.objects.all()

class CargoPredefinidoCreateView(CreateView):
    template_name = 'cargo/cargopredefinido_form.html'
    
    def get_form_class(self):
        from .forms import CargoPredefinidoForm
        return CargoPredefinidoForm
    
    def get_queryset(self):
        from .models import CargoPredefinido
        return CargoPredefinido.objects.all()
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Cargo "{form.instance.nombre}" creado exitosamente!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('empresas:cargopredefinido_detail', kwargs={'pk': self.object.id_cargo_predefinido})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cargo Predefinido'
        context['action'] = 'Crear'
        context['cargo'] = None
        return context

class CargoPredefinidoUpdateView(UpdateView):
    template_name = 'cargo/cargopredefinido_form.html'
    context_object_name = 'cargo'
    
    def get_form_class(self):
        from .forms import CargoPredefinidoForm
        return CargoPredefinidoForm
    
    def get_queryset(self):
        from .models import CargoPredefinido
        return CargoPredefinido.objects.all()
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Cargo "{form.instance.nombre}" actualizado exitosamente!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('empresas:cargopredefinido_detail', kwargs={'pk': self.object.id_cargo_predefinido})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Cargo: {self.object.nombre}'
        context['action'] = 'Actualizar'
        return context

class CargoPredefinidoDeleteView(DeleteView):
    template_name = 'cargo/cargopredefinido_confirm_delete.html'
    context_object_name = 'cargo'
    
    def get_queryset(self):
        from .models import CargoPredefinido
        return CargoPredefinido.objects.all()
    
    def delete(self, request, *args, **kwargs):
        cargo = self.get_object()
        messages.success(request, f'✅ Cargo "{cargo.nombre}" eliminado exitosamente!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('empresas:cargopredefinido_list')


# =======================
#  API PARA CARGOS PREDEFINIDOS
# =======================
@login_required
def cargos_activos_api(request):
    """API para obtener cargos predefinidos activos"""
    try:
        from .models import CargoPredefinido
        cargos = CargoPredefinido.objects.filter(activo=True).values('id_cargo_predefinido', 'nombre', 'estado_cargo')
        return JsonResponse({'cargos': list(cargos)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
