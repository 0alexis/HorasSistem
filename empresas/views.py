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
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy

from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Empresa, Proyecto, CentroOperativo
from .forms import EmpresaFiltroForm, EmpresaForm

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
        from .models import Proyecto
        proyectos = Proyecto.objects.all().order_by('-id')
        paginator = Paginator(proyectos, 10)
        page_number = request.GET.get('page')
        proyectos_page = paginator.get_page(page_number)
        context = {'proyectos': proyectos_page}
    except:
        context = {'proyectos': [], 'mensaje': 'En desarrollo'}
    return render(request, 'empresas/proyectos_list.html', context)

@login_required
def proyecto_create(request):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Proyectos'})

@login_required
def proyecto_detail(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Proyectos'})

@login_required
def proyecto_update(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Proyectos'})

@login_required
def proyecto_delete(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Proyectos'})

# =======================
#  CRUD DE CENTROS OPERATIVOS (EN DESARROLLO)
# =======================

@login_required
def centros_operativos_list(request):
    """Lista de centros operativos"""
    try:
        from .models import CentroOperativo
        centros = CentroOperativo.objects.all().order_by('-id')
        paginator = Paginator(centros, 10)
        page_number = request.GET.get('page')
        centros_page = paginator.get_page(page_number)
        context = {'centros_operativos': centros_page}
    except:
        context = {'centros_operativos': [], 'mensaje': 'En desarrollo'}
    return render(request, 'empresas/centros_operativos_list.html', context)

@login_required
def centro_operativo_create(request):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Centros Operativos'})

@login_required
def centro_operativo_detail(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Centros Operativos'})

@login_required
def centro_operativo_update(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Centros Operativos'})

@login_required
def centro_operativo_delete(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Centros Operativos'})

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

# =======================
#       CRUD DE CARGOS (EN DESARROLLO)
# =======================

@login_required
def cargos_list(request):
    """Lista de cargos predefinidos"""
    try:
        from .models import CargoPredefinido
        cargos = CargoPredefinido.objects.all().order_by('-id')
        paginator = Paginator(cargos, 10)
        page_number = request.GET.get('page')
        cargos_page = paginator.get_page(page_number)
        context = {'cargos': cargos_page}
    except:
        context = {'cargos': [], 'mensaje': 'En desarrollo'}
    return render(request, 'empresas/cargos_list.html', context)

@login_required
def cargo_create(request):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Cargos'})

@login_required
def cargo_detail(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Cargos'})

@login_required
def cargo_update(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Cargos'})

@login_required
def cargo_delete(request, pk):
    return render(request, 'empresas/en_desarrollo.html', {'modulo': 'Cargos'})

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
