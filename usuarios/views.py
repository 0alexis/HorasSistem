from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Usuario, Rol
from .serializers import UsuarioSerializer, UsuarioCreateSerializer, RolSerializer
from django.shortcuts import render, redirect
from .forms import TerceroForm, CentroDeCostoForm
from .models import Tercero, CentroDeCosto, CodigoTurno
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django import forms
from .forms import CodigoTurnoForm

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
    if request.method == 'POST':
        form = CodigoTurnoForm(request.POST, instance=codigo)
        if form.is_valid():
            form.save()
            return redirect('usuarios:codigoturno_list')
    else:
        form = CodigoTurnoForm(instance=codigo)
    return render(request, 'codigoturno/codigoturno_form.html', {'form': form, 'codigo': codigo})

def codigoturno_detail(request, pk):
    codigo = get_object_or_404(CodigoTurno, pk=pk)
    return render(request, 'codigoturno/codigoturno_detail.html', {'codigo': codigo})