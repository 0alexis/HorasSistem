from django.db import models

# Create your models here.

class Prueba(models.Model):
    """
    Modelo de prueba para demostrar la funcionalidad de la API
    """
    nombre = models.CharField(max_length=100, help_text="Nombre de la prueba")
    descripcion = models.TextField(help_text="Descripción detallada de la prueba")
    fecha_creacion = models.DateTimeField(auto_now_add=True, help_text="Fecha de creación del registro")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Prueba"
        verbose_name_plural = "Pruebas"
        ordering = ['-fecha_creacion']
