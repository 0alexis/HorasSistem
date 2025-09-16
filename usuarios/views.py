from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .models import Usuario, Rol
from .serializers import UsuarioSerializer, UsuarioCreateSerializer, RolSerializer
from django.shortcuts import render, redirect
from .forms import TerceroForm, CentroDeCostoForm, CodigoTurnoForm, SystemUserForm
from .models import Tercero, CentroDeCosto, CodigoTurno, Usuario
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

User = get_user_model()  # Esto obtiene el modelo correcto automáticamente

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Por favor proporcione username y password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UsuarioSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    @action(detail=True, methods=['post'])
    def assign_group(self, request, pk=None):
        user = self.get_object()
        group_id = request.data.get('group_id')
        
        try:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            return Response({'message': f'Usuario añadido al grupo {group.name}'})
        except Group.DoesNotExist:
            return Response(
                {'error': 'Grupo no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAuthenticated]



def tercero_create(request):
    if request.method == 'POST':
        form = TerceroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:tercero_list')
    else:
        form = TerceroForm()
    return render(request, 'usuarios/tercero_form.html', {'form': form})

##############TERCEROS(EMPLEAOS)#################
def tercero_list(request):
    terceros = Tercero.objects.all().order_by('-id_tercero')
    return render(request, 'usuarios/tercero_list.html', {'terceros': terceros})

def tercero_detail(request, pk):
    tercero = Tercero.objects.get(pk=pk)
    return render(request, 'usuarios/tercero_detail.html', {'tercero': tercero})

def tercero_update(request, pk):
    tercero = Tercero.objects.get(pk=pk)
    if request.method == 'POST':
        form = TerceroForm(request.POST, instance=tercero)
        if form.is_valid():
            form.save()
            return redirect('usuarios:tercero_list')
    else:
        form = TerceroForm(instance=tercero)
    return render(request, 'usuarios/tercero_form.html', {'form': form, 'tercero': tercero})



############CENTRO DE COSTO############

def centrodecosto_create(request):
    if request.method == 'POST':
        form = CentroDeCostoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('centro_costo:centrodecosto_list')
    else:
        form = CentroDeCostoForm()
    return render(request, 'centro_costo/centrodecosto_form.html', {'form': form})

def centrodecosto_list(request):
    centrosdecosto = CentroDeCosto.objects.all().order_by('-id')
    return render(request, 'centro_costo/centrodecosto_list.html', {'centrosdecosto': centrosdecosto})

def centrodecosto_detail(request, pk):
    centrodecosto = get_object_or_404(CentroDeCosto, pk=pk)
    return render(request, 'centro_costo/centrodecosto_detail.html', {'centrodecosto': centrodecosto})

def centrodecosto_update(request, pk):
    centrodecosto = get_object_or_404(CentroDeCosto, pk=pk)
    if request.method == 'POST':
        form = CentroDeCostoForm(request.POST, instance=centrodecosto)
        if form.is_valid():
            form.save()
            return redirect('centro_costo:centrodecosto_list')
    else:
        form = CentroDeCostoForm(instance=centrodecosto)
    return render(request, 'centro_costo/centrodecosto_form.html', {'form': form, 'centrodecosto': centrodecosto})

############CGRUPOS DE PERMISOS############

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }

def group_list(request):
    groups = Group.objects.all().order_by('name')
    return render(request, 'auth/group_list.html', {'groups': groups})

def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:group_list')
    else:
        form = GroupForm()
    return render(request, 'auth/group_form.html', {'form': form})

def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    return render(request, 'auth/group_detail.html', {'group': group})

def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('usuarios:group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'auth/group_form.html', {'form': form, 'group': group})


############VIEW PARA CODIGO DE TURNOS############


def codigoturno_list(request):
    codigos = CodigoTurno.objects.all().order_by('letra_turno')
    return render(request, 'codigoturno/codigoturno_list.html', {'codigos': codigos})

def codigoturno_create(request):
    hours = [f"{h:02d}" for h in range(24)]
    minutes = ["00", "15", "30", "45"]
    if request.method == 'POST':
        form = CodigoTurnoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:codigoturno_list')
    else:
        form = CodigoTurnoForm()
    return render(request, 'codigoturno/codigoturno_form.html', {
        'form': form,
        'codigo': None,
        'hours': hours,
        'minutes': minutes,
    })
def codigoturno_update(request, pk):
    codigo = get_object_or_404(CodigoTurno, pk=pk)
    hours = [f"{h:02d}" for h in range(24)]
    minutes = ["00", "30"]
    if request.method == 'POST':
        form = CodigoTurnoForm(request.POST, instance=codigo)
        if form.is_valid():
            form.save()
            return redirect('usuarios:codigoturno_list')
    else:
        form = CodigoTurnoForm(instance=codigo)
    return render(request, 'codigoturno/codigoturno_form.html', {
        'form': form,
        'codigo': codigo,
        'hours': hours,
        'minutes': minutes,
    })
def codigoturno_detail(request, pk):
    codigo = get_object_or_404(CodigoTurno, pk=pk)
    return render(request, 'codigoturno/codigoturno_detail.html', {'codigo': codigo})



############USUARIOS QUE USARAN EL SISTEMA############


@login_required
def user_list(request):
    """Listado de usuarios del sistema"""
    try:
        # ✅ USAR all_objects para incluir usuarios inactivos también
        users = Usuario.all_objects.select_related(
            'tercero', 
            'cargo_predefinido', 
            'centro_operativo'
        ).order_by('-fecha_creacion')
        
        # ✅ FILTRO DE BÚSQUEDA
        search_query = request.GET.get('search', '').strip()
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(nombre_usuario__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(tercero__nombre_tercero__icontains=search_query) |
                Q(tercero__apellido_tercero__icontains=search_query) |
                Q(tercero__correo_tercero__icontains=search_query)
            )
        
        # ✅ FILTRO POR ESTADO - CORREGIR LÓGICA
        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'active':
            users = users.filter(estado=True)
        elif status_filter == 'inactive':
            users = users.filter(estado=False)
        # Si no hay filtro, mostrar todos (activos e inactivos)
        
        # ✅ FILTRO POR TIPO DE USUARIO
        tipo_filter = request.GET.get('tipo', '').strip()
        if tipo_filter == 'superuser':
            users = users.filter(is_superuser=True)
        elif tipo_filter == 'staff':
            users = users.filter(is_staff=True, is_superuser=False)
        elif tipo_filter == 'normal':
            users = users.filter(is_staff=False, is_superuser=False)
        
        # ✅ PAGINACIÓN
        paginator = Paginator(users, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # ✅ ESTADÍSTICAS ACTUALIZADAS
        total_users = Usuario.all_objects.count()
        active_users = Usuario.all_objects.filter(estado=True).count()
        inactive_users = Usuario.all_objects.filter(estado=False).count()
        superusers = Usuario.all_objects.filter(is_superuser=True).count()
        staff_users = Usuario.all_objects.filter(is_staff=True, is_superuser=False).count()
        
        context = {
            'users': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'tipo_filter': tipo_filter,
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'superusers': superusers,
            'staff_users': staff_users,
        }
        
        return render(request, 'usuario_acess/user_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar usuarios: {str(e)}')
        return render(request, 'usuario_acess/user_list.html', {
            'users': Usuario.objects.none(),
            'search_query': '',
            'status_filter': '',
            'tipo_filter': '',
            'total_users': 0,
            'active_users': 0,
            'inactive_users': 0,
        })
@login_required
def user_create(request):
    """Crear nuevo usuario del sistema"""
    try:
        if request.method == 'POST':
            form = SystemUserForm(request.POST)
            if form.is_valid():
                # Crear el usuario pero no guardarlo aún
                user = form.save(commit=False)
                
                # Configurar campos automáticos
                user.fecha_creacion = timezone.now()
                user.fecha_actualizacion = timezone.now()
                
                # Guardar el usuario
                user.save()
                
                # Guardar grupos y relaciones many-to-many
                form.save_m2m()
                
                messages.success(request, f'Usuario "{user.username}" creado exitosamente.')
                return redirect('usuarios:user_list')
            else:
                # Si hay errores, mostrarlos
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            form = SystemUserForm()
        
        context = {
            'form': form,
            'form_title': 'Nuevo Usuario del Sistema',
            'action': 'create'
        }
        
        return render(request, 'usuario_acess/user_form.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al crear usuario: {str(e)}')
        return redirect('usuarios:user_list')

@login_required
def user_detail(request, pk):
    """Detalle de usuario del sistema"""
    try:
        user_obj = get_object_or_404(Usuario, pk=pk)
        
        context = {
            'user_obj': user_obj,
        }
        
        return render(request, 'usuario_acess/user_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar usuario: {str(e)}')
        return redirect('usuarios:user_list')

@login_required
def user_edit(request, pk):
    """Editar usuario del sistema"""
    try:
        user_obj = get_object_or_404(Usuario, pk=pk)  # USAR Usuario
        
        if request.method == 'POST':
            form = SystemUserForm(request.POST, instance=user_obj)
            if form.is_valid():
                user = form.save(commit=False)
                user.fecha_actualizacion = timezone.now()
                user.save()
                form.save_m2m()
                
                messages.success(request, f'Usuario "{user.nombre_usuario}" actualizado exitosamente.')
                return redirect('usuarios:user_list')
        else:
            form = SystemUserForm(instance=user_obj)
        
        context = {
            'form': form,
            'form_title': f'Editar Usuario: {user_obj.nombre_usuario}',
            'action': 'edit',
            'user_obj': user_obj
        }
        
        return render(request, 'usuario_acess/user_form.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al editar usuario: {str(e)}')
        return redirect('usuarios:user_list')


@login_required
def user_toggle_status(request, pk):
    """Activar/Desactivar usuario"""
    try:
        user_obj = get_object_or_404(Usuario.all_objects, pk=pk)  # ✅ all_objects para acceder a inactivos también
        user_obj.estado = not user_obj.estado  # ✅ Toggle más simple
        user_obj.save()
        
        status_text = "activado" if user_obj.estado else "desactivado"
        user_name = user_obj.get_display_name()  # ✅ Usar el método del modelo
        messages.success(request, f'Usuario "{user_name}" {status_text} exitosamente.')
        
    except Exception as e:
        messages.error(request, f'Error al cambiar estado: {str(e)}')
    
    return redirect('usuarios:user_list')
