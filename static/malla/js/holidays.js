/* 
 * Holiday data for calendar
 * This file is processed as a Django template
 */

    /*
     * Marca visualmente los días festivos y domingos en la malla.
     * Requiere que el template incluya:
     *   const festivos = [...]; // lista de fechas en formato 'YYYY-MM-DD'
     *   function esFestivo(fechaStr) { return festivos.includes(fechaStr); }
     *   function esDomingo(fechaStr) { return new Date(fechaStr + 'T00:00:00').getDay() === 0; }
     */
    
    document.addEventListener('DOMContentLoaded', function() {
        // Busca todos los inputs/celdas con atributo data-fecha
        document.querySelectorAll('input[data-fecha], td[data-fecha]').forEach(function(element) {
            const fechaStr = element.getAttribute('data-fecha');
            if (fechaStr) {
                // Marcar festivos (prioridad alta)
                if (typeof esFestivo === 'function' && esFestivo(fechaStr)) {
                    element.classList.add('festivo');
                    if (element.tagName === 'INPUT' && element.parentElement) {
                        element.parentElement.classList.add('festivo');
                    }
                }
                // Marcar domingos (solo si no es festivo)
                else if (typeof esDomingo === 'function' && esDomingo(fechaStr)) {
                    element.classList.add('domingo');
                    if (element.tagName === 'INPUT' && element.parentElement) {
                        element.parentElement.classList.add('domingo');
                    }
                }
            }
        });
    });

