from django.db import models

TIPOS_PATRON = [
    ('5x3', '5x3 (4 filas x 16 columnas)'),
    ('3x3', '3x3 (3 filas x 3 columnas)'),
    # Agrega más tipos si lo necesitas
]

class PatronBase(models.Model):
    """
    Modelo para almacenar patrones base de turnos.
    La matriz debe ser una lista de listas (ejemplo: [['A','B'],['C','D']])
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    tipo_patron = models.CharField(
        max_length=10,
        choices=TIPOS_PATRON,
        help_text="Selecciona el tamaño y tipo de patrón base"
    )
    matriz = models.JSONField(editable=False, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.matriz:
            if self.tipo_patron == '5x3':
                self.matriz = [[""] * 16 for _ in range(4)]
            elif self.tipo_patron == '3x3':
                self.matriz = [[""] * 3 for _ in range(3)]
            # Agrega más patrones aquí si lo necesitas
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_patron_display()})"
