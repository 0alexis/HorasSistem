# Guía de Programación de Turnos

## Descripción General

El sistema de programación de turnos permite crear programaciones automáticas de horarios para empleados basándose en modelos de turno predefinidos. **El sistema funciona únicamente desde los templates personalizados** y cada programación se asocia a un centro operativo específico y un cargo predefinido.

## ⚠️ IMPORTANTE: Solo Templates

**El admin de Django ya no se utiliza para la programación de turnos.** Todo el proceso se realiza a través de:
- Templates personalizados
- Vistas específicas
- API REST (opcional)

## Componentes del Sistema

### 1. Modelos Principales

- **ProgramacionHorario**: Define una programación específica
- **ModeloTurno**: Define el patrón de turnos (matriz de letras)
- **LetraTurno**: Define las letras individuales del modelo
- **AsignacionTurno**: Asigna un turno específico a un empleado en una fecha
- **CargoPredefinido**: Define los cargos disponibles
- **CentroOperativo**: Define los centros donde se aplican las programaciones

### 2. Flujo de Trabajo

```
1. Crear Modelo de Turno → 2. Configurar Letras → 3. Crear Programación → 4. Generar Asignaciones
```

## Configuración Requerida

### Paso 1: Modelo de Turno

Antes de crear una programación, debe existir un modelo de turno con letras configuradas:

```python
# Ejemplo de modelo de turno 4x4
# Fila 0: [A, B, C, D]
# Fila 1: [B, C, D, A]
# Fila 2: [C, D, A, B]
# Fila 3: [D, A, B, C]
```

### Paso 2: Verificar Datos

Asegúrese de que existan:
- ✅ Centro operativo activo
- ✅ Cargo predefinido activo
- ✅ Modelo de turno con letras configuradas
- ✅ Terceros asignados al centro con el cargo correcto
- ✅ Terceros activos (estado_tercero = 1)

## Crear Programación

### ✅ Opción ÚNICA: Desde el Template Personalizado

1. Ir a la vista de crear programación
2. Seleccionar:
   - **Centro operativo** (obligatorio)
   - **Modelo de turno** (obligatorio)
   - **Cargo predefinido** (obligatorio)
   - **Fechas de inicio y fin** (obligatorio)
3. El sistema validará automáticamente:
   - Que existan terceros en el centro seleccionado
   - Que los terceros tengan el cargo especificado
   - Que los terceros estén activos
4. Se creará la programación
5. Se generarán automáticamente las asignaciones

### 🔍 Validaciones Automáticas

El sistema realiza las siguientes validaciones antes de crear la programación:

```python
# Verificación de terceros válidos
terceros_disponibles = AsignacionTerceroEmpresa.objects.filter(
    centro_operativo=programacion.centro_operativo,
    activo=True
).filter(
    tercero__cargo_predefinido=programacion.cargo_predefinido,
    tercero__estado_tercero=1
).count()

if terceros_disponibles == 0:
    # Error: No hay terceros válidos
    # La programación se elimina automáticamente
```

## Generación de Asignaciones

### Lógica de Filtrado

El sistema **SOLO** considera terceros que cumplan **TODAS** estas condiciones:

1. **Asignados al centro operativo seleccionado**
2. **Con el cargo predefinido específico**
3. **Activos (estado_tercero = 1)**
4. **Con asignación activa al centro**

### Lógica de Asignación

1. **Filtrado de Empleados**: Solo se consideran empleados válidos según los criterios anteriores
2. **Distribución por Filas**: Los empleados se distribuyen en filas del modelo:
   - Empleado 1 → Fila 0
   - Empleado 2 → Fila 1
   - Empleado 3 → Fila 2
   - Empleado 4 → Fila 0 (cicla)
3. **Distribución por Días**: Los días se distribuyen en columnas del modelo:
   - Día 1 → Columna 0
   - Día 2 → Columna 1
   - Día 3 → Columna 2
   - Día 4 → Columna 0 (cicla)

### Ejemplo de Asignación

```
Modelo 4x4:
Fila 0: [A, B, C, D]
Fila 1: [B, C, D, A]

Empleados válidos: Juan, María
Días: 1 al 7

Resultado:
Juan (Fila 0): Día1=A, Día2=B, Día3=C, Día4=D, Día5=A, Día6=B, Día7=C
María (Fila 1): Día1=B, Día2=C, Día3=D, Día4=A, Día5=B, Día6=C, Día7=D
```

## Solución de Problemas

### Error: "No hay empleados con el cargo seleccionado"

**Causas posibles:**
1. Los terceros no están asignados al centro operativo
2. Los terceros no tienen asignado el cargo correcto
3. Los terceros no están activos
4. Las asignaciones al centro no están activas

**Solución:**
```python
# Verificar asignaciones
from empresas.models import AsignacionTerceroEmpresa

asignaciones = AsignacionTerceroEmpresa.objects.filter(
    centro_operativo=centro,
    activo=True
)

for asignacion in asignaciones:
    tercero = asignacion.tercero
    print(f"Tercero: {tercero.nombre_tercero}")
    print(f"Cargo: {getattr(tercero, 'cargo_predefinido', 'SIN CARGO')}")
    print(f"Estado: {tercero.estado_tercero}")
    print("---")
```

### Error: "No hay letras de turno para el modelo"

**Causa:** El modelo de turno no tiene letras configuradas

**Solución:**
```python
# Verificar letras del modelo
from programacion_models.models import LetraTurno

letras = LetraTurno.objects.filter(modelo_turno=modelo)
print(f"Letras encontradas: {letras.count()}")

for letra in letras:
    print(f"Fila {letra.fila}, Columna {letra.columna}: {letra.valor}")
```

### Error: "Para modelos de tipo FIJO se requieren al menos X personas"

**Causa:** No hay suficientes empleados para el modelo fijo

**Solución:** 
- Agregar más empleados al centro
- O cambiar a un modelo de tipo variable

## Pruebas

### Script de Prueba Principal

Ejecute el script de prueba para verificar la funcionalidad:

```bash
python test_programacion_centro_cargo.py
```

Este script:
1. Verifica que existan todos los datos necesarios
2. Analiza detalladamente los terceros en cada centro
3. Verifica el filtrado por cargo y centro operativo
4. Crea una programación de prueba
5. Genera las asignaciones
6. Verifica que se crearon correctamente
7. Limpia los datos de prueba

### Script de Prueba Básico

```bash
python test_programacion.py
```

### Verificación Manual

1. **Crear programación** desde el template personalizado
2. **Verificar asignaciones** en la tabla `AsignacionTurno`
3. **Revisar logs** en la consola para debugging

## Logs y Debugging

El sistema genera logs detallados durante la generación de asignaciones:

```
=== INICIANDO GENERACIÓN DE ASIGNACIONES ===
Programación ID: 123
Centro operativo: Centro A
Modelo de turno: Modelo 4x4
Cargo predefinido: Operador
Fechas: 2024-01-01 - 2024-01-31

=== ANÁLISIS DE ASIGNACIONES DEL CENTRO ===
Total de asignaciones al centro: 15

=== TERCEROS SELECCIONADOS PARA PROGRAMACIÓN ===
Terceros del centro 'Centro A' con cargo 'Operador': 8
   1. Juan Pérez
   2. María García
   ...

=== CONFIGURACIÓN DEL MODELO DE TURNO ===
Letras de turno encontradas: 16
Dimensiones: 4 filas × 4 columnas

=== PARÁMETROS DE PROGRAMACIÓN ===
Rango de días: 31 días
Total de terceros: 8
Total de asignaciones a crear: 248

=== INICIANDO CREACIÓN DE ASIGNACIONES ===
👤 Tercero 1: Juan Pérez - Asignado a Fila 0
   ✅ 2024-01-01: A
   ✅ 2024-01-02: B
   ...

=== PROGRAMACIÓN COMPLETADA ===
✅ Total de asignaciones creadas: 248
✅ Total de asignaciones en BD: 248
✅ Programación exitosa para 8 terceros en 31 días
```

## Consideraciones Importantes

1. **Integridad de Datos**: Las asignaciones se eliminan y recrean cada vez
2. **Filtrado Estricto**: Solo se consideran terceros que cumplan TODOS los criterios
3. **Validaciones Automáticas**: El sistema valida antes de crear la programación
4. **Transacciones**: Las operaciones son atómicas (todo o nada)
5. **Solo Templates**: No se usa el admin de Django

## Personalización

### Agregar Nuevos Tipos de Modelo

Para agregar nuevos tipos de patrones, modifique la función `generar_asignaciones` en `serializers.py`.

### Cambiar Lógica de Distribución

Modifique la lógica de asignación de filas y columnas según sus necesidades específicas.

### Agregar Nuevas Validaciones

Para agregar nuevas validaciones, modifique la vista `crear_programacion_view` en `views.py`.

## Soporte

Si encuentra problemas:

1. **Revisar logs** en la consola
2. **Verificar datos** con el script de prueba
3. **Comprobar relaciones** entre modelos
4. **Revisar estado** de registros (activo/inactivo)
5. **Verificar asignaciones** de terceros al centro operativo
6. **Confirmar cargos** asignados a los terceros

## Cambios Recientes

### ✅ Mejoras Implementadas

1. **Filtrado Mejorado**: Solo terceros del centro operativo seleccionado con cargo específico
2. **Validaciones Automáticas**: Verificación previa de terceros válidos
3. **Logging Detallado**: Información completa del proceso de generación
4. **Manejo de Errores**: Eliminación automática de programaciones inválidas
5. **Solo Templates**: Eliminación de dependencia del admin de Django

### 🔧 Archivos Modificados

- `programacion_turnos/serializers.py` - Función `generar_asignaciones` optimizada
- `programacion_turnos/views.py` - Vista `crear_programacion_view` mejorada
- `test_programacion_centro_cargo.py` - Script de prueba específico creado
- `PROGRAMACION_TURNOS_GUIA.md` - Documentación actualizada 