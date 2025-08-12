/* 
 * Holiday data for calendar
 * This file is processed as a Django template
 */

document.addEventListener('DOMContentLoaded', function() {
    // Lista dinámica de códigos utilizados en esta programación
    const codigosUtilizados = [
        {% for codigo in codigos_turno %}
        '{{ codigo.codigo }}',
        {% endfor %}
    ];
    
    // Horas por código dinámicas
    const horasPorTurno = {
        {% for codigo in codigos_turno %}
        '{{ codigo.codigo }}': {{ codigo.horas }},
        {% endfor %}
    };
    
    console.log('Códigos utilizados en esta programación:', codigosUtilizados);
    console.log('Horas por turno:', horasPorTurno);
    
    // Apply turno color class when input changes
    document.querySelectorAll('.turno-input').forEach(function(input) {
        input.addEventListener('input', function() {
            var value = this.value.toUpperCase();
            this.value = value;
            
            // Remove all existing turno classes
            var classList = this.parentElement.classList;
            for (var i = classList.length - 1; i >= 0; i--) {
                if (classList[i].startsWith('turno-')) {
                    this.parentElement.classList.remove(classList[i]);
                }
            }
            
            // Add the appropriate class if it's a code used in this programming
            if (codigosUtilizados.includes(value)) {
                this.parentElement.classList.add('turno-' + value);
            }
            
            // Recalcular totales
            calcularTotales();
        });
    });
    
    // Función para calcular totales
    function calcularTotales() {
        // Solo proceder si hay códigos utilizados
        if (codigosUtilizados.length === 0) {
            return;
        }
        
        // Initialize grand totals
        let granTotalHoras = 0;
        let granTotalFinde = 0;
        let granTotalFestivos = 0;
        
        // Initialize counters for each shift type used in this programming
        const granTotalPorCodigo = {};
        codigosUtilizados.forEach(codigo => {
            granTotalPorCodigo[codigo] = 0;
        });
        
        // Process each employee
        document.querySelectorAll('.empleado-resumen').forEach(function(fila) {
            const terceroId = fila.dataset.terceroId;
            let totalHoras = 0;
            let horasFinde = 0;
            let horasFestivos = 0;
            
            // Initialize counters for this employee
            const turnosPorCodigo = {};
            codigosUtilizados.forEach(codigo => {
                turnosPorCodigo[codigo] = 0;
            });
            
            // Get all inputs for this employee
            document.querySelectorAll(`input[name^="letra_${terceroId}_"]`).forEach(function(input) {
                const letra = input.value.toUpperCase();
                
                // Only count codes used in this programming
                if (codigosUtilizados.includes(letra)) {
                    // Count this code
                    turnosPorCodigo[letra]++;
                    
                    // Add hours
                    const horas = horasPorTurno[letra] || 0;
                    totalHoras += horas;
                    
                    // Extract date from input name (format: letra_ID_YYYY-MM-DD)
                    const fechaStr = input.name.split('_')[2];
                    
                    // Check if weekend
                    if (input.parentElement.classList.contains('weekend') && horas > 0) {
                        horasFinde += horas;
                    }
                    
                    // Check if holiday (if esFestivo function is available)
                    if (typeof esFestivo === 'function' && esFestivo(fechaStr) && horas > 0) {
                        horasFestivos += horas;
                    }
                }
            });
            
            // Update employee summary
            const totalHorasElement = document.getElementById(`total-horas-${terceroId}`);
            const horasFindeElement = document.getElementById(`horas-finde-${terceroId}`);
            const horasFestivosElement = document.getElementById(`horas-festivos-${terceroId}`);
            
            if (totalHorasElement) totalHorasElement.textContent = totalHoras;
            if (horasFindeElement) horasFindeElement.textContent = horasFinde;
            if (horasFestivosElement) horasFestivosElement.textContent = horasFestivos;
            
            // Update shift counts for this employee
            codigosUtilizados.forEach(codigo => {
                const element = document.getElementById(`turnos-${codigo}-${terceroId}`);
                if (element) {
                    element.textContent = turnosPorCodigo[codigo];
                }
                
                // Add to grand totals
                granTotalPorCodigo[codigo] += turnosPorCodigo[codigo];
            });
            
            // Add to grand totals
            granTotalHoras += totalHoras;
            granTotalFinde += horasFinde;
            granTotalFestivos += horasFestivos;
        });
        
        // Update grand totals
        const granTotalHorasElement = document.getElementById('gran-total-horas');
        const granTotalFindeElement = document.getElementById('gran-total-finde');
        const granTotalFestivosElement = document.getElementById('gran-total-festivos');
        
        if (granTotalHorasElement) granTotalHorasElement.textContent = granTotalHoras;
        if (granTotalFindeElement) granTotalFindeElement.textContent = granTotalFinde;
        if (granTotalFestivosElement) granTotalFestivosElement.textContent = granTotalFestivos;
        
        // Update grand totals for each code
        codigosUtilizados.forEach(codigo => {
            const element = document.getElementById(`gran-total-${codigo}`);
            if (element) {
                element.textContent = granTotalPorCodigo[codigo];
            }
        });
    }
    
    // Calculate totals on page load
    setTimeout(calcularTotales, 100); // Small delay to ensure DOM is ready
    
    // Recalculate when any input changes
    document.querySelectorAll('.turno-input').forEach(function(input) {
        input.addEventListener('change', calcularTotales);
        input.addEventListener('keyup', calcularTotales);
    });
});