// Variables globales
window.letrasValidas = window.letrasValidas || [];
window.programacionId = window.programacionId || null;

// Solo redirigir al módulo de asignación de turno al hacer doble clic
function activarEdicion(span, valorActual) {
    const empleadoId = span.getAttribute('data-empleado-id');
    const fecha = span.getAttribute('data-fecha');
    window.location.href = `/asignacionturno/?empleado=${empleadoId}&fecha=${fecha}`;
}

function redirigirEdicion(span) {
    const empleadoId = span.getAttribute('data-empleado-id');
    const fecha = span.getAttribute('data-fecha');
    const llave = `${empleadoId}_${fecha}`;
    window.location.href = `/asignacionturno/${llave}/change/`;
}