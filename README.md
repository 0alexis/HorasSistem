# Sistema de Turnos - Backend

Backend del sistema de turnos desarrollado con Django y MySQL.

## Requisitos

- Python 3.11+
- MySQL 8.0+
- Git

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd HorasSistem_Backend
```

2. Crear y activar el entorno virtual:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar la base de datos:
- Crear una base de datos MySQL llamada 'turnos'
- Configurar las credenciales en el archivo `.env`

5. Ejecutar migraciones:
```bash
python manage.py migrate
```

6. Iniciar el servidor:
```bash
python manage.py runserver
```

## Documentación de la API

La documentación de la API está disponible en:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Estructura del Proyecto

```
HorasSistem_Backend/
├── venv/                  # Entorno virtual
├── horas_sistema/        # Proyecto Django
│   ├── settings.py       # Configuraciones
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # Configuración WSGI
├── prueba/              # Aplicación de prueba
├── manage.py            # Script de administración
├── requirements.txt     # Dependencias
├── .env                # Variables de entorno
└── .gitignore         # Archivos a ignorar en git
```

## Características

- API REST con Django REST Framework
- Documentación con Swagger/OpenAPI
- Base de datos MySQL
- CORS configurado
- Autenticación y autorización
- Panel de administración Django

## Desarrollo

Para contribuir al proyecto:

1. Crear una rama para tu feature:
```bash
git checkout -b feature/nueva-funcionalidad
```

2. Hacer commit de tus cambios:
```bash
git commit -m "Añade nueva funcionalidad"
```

3. Subir los cambios:
```bash
git push origin feature/nueva-funcionalidad
```

## Licencia

Este proyecto está bajo la Licencia MIT. 