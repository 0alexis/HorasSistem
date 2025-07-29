import threading
from django.utils.deprecation import MiddlewareMixin

# Thread local para almacenar el request actual
_request_local = threading.local()

class RequestMiddleware(MiddlewareMixin):
    """
    Middleware para almacenar el request actual en thread local
    para que los signals puedan acceder a él
    """
    
    def process_request(self, request):
        """Almacena el request en thread local"""
        _request_local.request = request
    
    def process_response(self, request, response):
        """Limpia el request del thread local"""
        if hasattr(_request_local, 'request'):
            delattr(_request_local, 'request')
        return response
    
    def process_exception(self, request, exception):
        """Limpia el request en caso de excepción"""
        if hasattr(_request_local, 'request'):
            delattr(_request_local, 'request')
        return None

def get_current_request():
    """Obtiene el request actual desde thread local"""
    return getattr(_request_local, 'request', None) 