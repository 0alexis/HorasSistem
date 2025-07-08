from datetime import timedelta
from .models import AsignacionTurno


def obtener_patron(modelo_turno):
    # Devuelve una matriz de letras (lista de listas) desde la base de datos
    letras = modelo_turno.letras.order_by('fila', 'columna')
    filas = {}
    for l in letras:
        filas.setdefault(l.fila, []).append(l.valor)
    return [filas[k] for k in sorted(filas.keys())]

class Generador16D:
    def generar(self, empleados, semanas, patron):
        horarios = []
        dia_patron = 0
        total_patrones = len(patron)
        bloques_completos = len(empleados) // total_patrones
        sobrantes = empleados[bloques_completos * total_patrones:]
        empleados_base = empleados[:bloques_completos * total_patrones]

        for semana in range(semanas):
            for i, emp in enumerate(empleados_base):
                patron_fila = patron[i % total_patrones]
                for dia in range(7):
                    idx = (dia_patron + dia) % len(patron_fila)
                    fecha = semana * 7 + dia  # O usa fecha_inicio + timedelta
                    horarios.append({
                        'empleado_id': emp.id,
                        'semana': semana,
                        'dia': dia,
                        'turno': patron_fila[idx]
                    })
            for i, emp in enumerate(sobrantes):
                patron_fila = patron[i % total_patrones]
                for dia in range(7):
                    idx = (dia_patron + dia) % len(patron_fila)
                    fecha = semana * 7 + dia
                    horarios.append({
                        'empleado_id': emp.id,
                        'semana': semana,
                        'dia': dia,
                        'turno': patron_fila[idx]
                    })
            dia_patron = (dia_patron + 7) % len(patron[0])
        return horarios

# ... (puedes adaptar Generador6D y Generador18D_H igual)

class ProgramadorTurnos:
    def __init__(self):
        self.generadores = {
            '16D': Generador16D(),
            # '6D': Generador6D(),
            # '18H': Generador18D_H(),
        }

    def programar(self, modelo_turno, empleados, semanas):
        patron = obtener_patron(modelo_turno)
        gen = self.generadores.get(modelo_turno.tipo_codigo)  # tipo_codigo: '16D', '6D', etc.
        if not gen:
            raise ValueError(f"Modelo de turno '{modelo_turno.tipo_codigo}' no soportado")
        return gen.generar(empleados, semanas, patron)

def programar_turnos(modelo_turno, empleados, fecha_inicio, fecha_fin, programacion):
    letras = modelo_turno.letras.order_by('fila', 'columna')
    
    filas = {}
    for l in letras:
        filas.setdefault(l.fila, []).append(l.valor)
    filas_ordenadas = [filas[k] for k in sorted(filas.keys())]
    dias = (fecha_fin - fecha_inicio).days + 1

    for idx, empleado in enumerate(empleados):
        fila_idx = idx % len(filas_ordenadas)
        fila = filas_ordenadas[fila_idx]
        for dia_offset in range(dias):
            fecha = fecha_inicio + timedelta(days=dia_offset)
            letra = fila[dia_offset % len(fila)]
            AsignacionTurno.objects.create(
                programacion=programacion,
                tercero=empleado,
                dia=fecha,
                letra_turno=letra,
                fila = fila_idx
            )
