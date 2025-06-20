from django.views.generic import ListView, DetailView
from .modelos_turnos.patrones_base import PatronBase

class PatronBaseListView(ListView):
    model = PatronBase
    template_name = 'patronbase_list.html'  # Debes crear este template

class PatronBaseDetailView(DetailView):
    model = PatronBase
    template_name = 'patronbase_detail.html'  # Debes crear este template

# Si en el futuro necesitas vistas personalizadas para ModeloTurno,
# puedes importarlo así:
# from .models import ModeloTurno

# Por ahora, si solo usas el admin, este archivo puede quedar vacío.
