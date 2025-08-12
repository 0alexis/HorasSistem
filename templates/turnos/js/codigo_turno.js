/**
 * JavaScript completo para manejo de códigos de turno con segmentos
 */

(function($) {
    'use strict';
    
    // Configuración
    const SEGMENTO_TIPOS = [
        ['NORMAL', 'Normal'],
        ['FESTIVO', 'Festivo'],
        ['NOCTURNO', 'Nocturno'],
        ['DOMINGO', 'Domingo'],
        ['EXTRA', 'Extra'],
        ['COMPENSATORIO', 'Compensatorio']
    ];
    
    // Plantillas predefinidas
    const PLANTILLAS = {
        'N': {
            nombre: 'Turno Normal',
            segmentos: [{inicio: '', fin: '', tipo: 'NORMAL'}]
        },
        'F': {
            nombre: 'Turno Festivo',
            segmentos: [
                {inicio: '', fin: '', tipo: 'NORMAL'},
                {inicio: '', fin: '', tipo: 'FESTIVO'}
            ]
        },
        'E': {
            nombre: 'Turno Especial',
            segmentos: [
                {inicio: '', fin: '', tipo: 'NOCTURNO'},
                {inicio: '', fin: '', tipo: 'NORMAL'},
                {inicio: '', fin: '', tipo: 'FESTIVO'}
            ]
        }
    };
    
    class CodigoTurnoAdmin {
        constructor() {
            this.segmentos = [];
            this.tipoTurno = null;
            this.init();
        }
        
        init() {
            this.bindEvents();
            this.cargarSegmentosExistentes();
            this.actualizarInterfaz();
            this.configurarInputsTiempo();
        }
        
        configurarInputsTiempo() {
            // Configurar inputs de tiempo para formato 24 horas
            $('input[type="time"]').each(function() {
                $(this)
                    .attr('step', '900') // 15 minutos
                    .attr('min', '00:00')
                    .attr('max', '23:59');
            });
        }
        
        bindEvents() {
            // Cambio de tipo de turno
            $('#id_tipo').on('change', (e) => {
                this.tipoTurno = $(e.target).val();
                this.actualizarInterfaz();
            });
            
            // Botones de control
            $(document).on('click', '.btn-agregar-segmento', (e) => {
                e.preventDefault();
                this.agregarSegmento();
            });
            
            $(document).on('click', '.btn-eliminar-segmento', (e) => {
                e.preventDefault();
                const index = $(e.target).data('index');
                this.eliminarSegmento(index);
            });
            
            $(document).on('click', '.btn-plantilla', (e) => {
                e.preventDefault();
                const plantilla = $(e.target).data('plantilla');
                this.aplicarPlantilla(plantilla);
            });
            
            // Validación en tiempo real
            $(document).on('change', '.segmento-campos input, .segmento-campos select', () => {
                this.actualizarSegmentosDesdeDOM();
                this.validarSegmentos();
            });
        }
        
        cargarSegmentosExistentes() {
            // Buscar el campo correcto
            const segmentosField = $('#id_segmentos_horas');
            const segmentosJson = segmentosField.val();
            
            if (segmentosJson) {
                try {
                    this.segmentos = JSON.parse(segmentosJson);
                    this.renderizarSegmentos();
                } catch (e) {
                    console.error('Error al cargar segmentos:', e);
                    this.segmentos = [];
                }
            }
        }
        
        actualizarInterfaz() {
            const tipo = $('#id_tipo').val();
            
            // Ocultar/mostrar campos según el tipo
            if (tipo === 'D' || tipo === 'ND') {
                $('.segmentos-container').hide();
                $('.controles-segmentos').hide();
                this.mostrarInfoTipo(tipo);
            } else {
                $('.segmentos-container').show();
                $('.controles-segmentos').show();
                this.renderizarSegmentos();
                this.mostrarInfoTipo(tipo);
            }
            
            // Mostrar campo de descripción para No Devengado
            if (tipo === 'ND') {
                $('#id_descripcion_novedad').closest('.form-row').show();
            } else {
                $('#id_descripcion_novedad').closest('.form-row').hide();
            }
        }
        
        mostrarInfoTipo(tipo) {
            let info = '';
            
            switch(tipo) {
                case 'N':
                    info = 'Turno Normal: Debe tener exactamente 1 segmento de tipo NORMAL.';
                    break;
                case 'D':
                    info = 'Turno Descanso: No requiere segmentos ni horarios.';
                    break;
                case 'F':
                case 'FO':
                    info = 'Turno Festivo: Puede tener múltiples segmentos con diferentes tipos.';
                    break;
                case 'E':
                    info = 'Turno Especial: Configuración personalizada con múltiples segmentos.';
                    break;
                case 'ND':
                    info = 'Turno No Devengado: Requiere descripción de la novedad.';
                    break;
            }
            
            $('.tipo-turno-info').remove();
            $('.segmentos-container').before(`
                <div class="tipo-turno-info">
                    <strong>Información:</strong> ${info}
                </div>
            `);
        }
        
        crearHTMLSegmento(segmento, index) {
            const tiposOptions = SEGMENTO_TIPOS.map(([valor, etiqueta]) => 
                `<option value="${valor}" ${segmento.tipo === valor ? 'selected' : ''}>${etiqueta}</option>`
            ).join('');
            
            return `
                <div class="segmento-item" data-index="${index}">
                    <div class="segmento-numero">${index + 1}</div>
                    <div class="segmento-campos">
                        <input type="time" value="${segmento.inicio || ''}" placeholder="Inicio" 
                               class="segmento-inicio" step="900" min="00:00" max="23:59">
                        <input type="time" value="${segmento.fin || ''}" placeholder="Fin" 
                               class="segmento-fin" step="900" min="00:00" max="23:59">
                        <select class="segmento-tipo">
                            ${tiposOptions}
                        </select>
                    </div>
                    <div class="segmento-acciones">
                        <button type="button" class="btn-segmento danger btn-eliminar-segmento" data-index="${index}">
                            Eliminar
                        </button>
                    </div>
                </div>
            `;
        }
        
        renderizarSegmentos() {
            const container = $('.segmentos-lista');
            container.empty();
            
            this.segmentos.forEach((segmento, index) => {
                const html = this.crearHTMLSegmento(segmento, index);
                container.append(html);
            });
            
            // Aplicar formato a los nuevos inputs
            this.configurarInputsTiempo();
            
            this.actualizarJSON();
        }
        
        agregarSegmento() {
            if (this.segmentos.length >= 8) {
                alert('Máximo 8 segmentos permitidos');
                return;
            }
            
            const nuevoSegmento = {
                inicio: '',
                fin: '',
                tipo: 'NORMAL'
            };
            
            this.segmentos.push(nuevoSegmento);
            this.renderizarSegmentos();
        }
        
        eliminarSegmento(index) {
            if (confirm('¿Estás seguro de eliminar este segmento?')) {
                this.segmentos.splice(index, 1);
                this.renderizarSegmentos();
            }
        }
        
        aplicarPlantilla(plantillaKey) {
            const plantilla = PLANTILLAS[plantillaKey];
            if (plantilla) {
                this.segmentos = [...plantilla.segmentos];
                this.renderizarSegmentos();
                alert(`Plantilla "${plantilla.nombre}" aplicada`);
            }
        }
        
        validarSegmentos() {
            // Recopilar datos actuales
            this.actualizarSegmentosDesdeDOM();
            
            // Validaciones
            const errores = [];
            
            if (this.segmentos.length === 0 && !['D', 'ND'].includes(this.tipoTurno)) {
                errores.push('Debe tener al menos 1 segmento');
            }
            
            if (this.segmentos.length > 8) {
                errores.push('Máximo 8 segmentos permitidos');
            }
            
            // Validar formato de tiempo
            for (let i = 0; i < this.segmentos.length; i++) {
                const segmento = this.segmentos[i];
                const regex = /^([0-1][0-9]|2[0-3]):([0-5][0-9])$/;
                
                if (segmento.inicio && !regex.test(segmento.inicio)) {
                    errores.push(`Segmento ${i + 1}: Hora de inicio debe estar en formato 24h (00:00 a 23:59)`);
                }
                
                if (segmento.fin && !regex.test(segmento.fin)) {
                    errores.push(`Segmento ${i + 1}: Hora de fin debe estar en formato 24h (00:00 a 23:59)`);
                }
            }
            
            // Validar continuidad
            for (let i = 0; i < this.segmentos.length - 1; i++) {
                if (this.segmentos[i].fin !== this.segmentos[i + 1].inicio) {
                    errores.push(`Gap detectado entre ${this.segmentos[i].fin} y ${this.segmentos[i + 1].inicio}`);
                }
            }
            
            // Validar tipo Normal
            if (this.tipoTurno === 'N') {
                if (this.segmentos.length !== 1) {
                    errores.push('Los turnos normales deben tener exactamente 1 segmento');
                } else if (this.segmentos[0].tipo !== 'NORMAL') {
                    errores.push('Los turnos normales solo pueden tener segmentos de tipo NORMAL');
                }
            }
            
            // Mostrar errores
            this.mostrarErrores(errores);
            
            return errores.length === 0;
        }
        
        mostrarErrores(errores) {
            $('.segmentos-error').remove();
            
            if (errores.length > 0) {
                const errorHtml = `
                    <div class="segmentos-error tipo-turno-info error">
                        <strong>Errores de validación:</strong>
                        <ul>
                            ${errores.map(error => `<li>${error}</li>`).join('')}
                        </ul>
                    </div>
                `;
                $('.segmentos-container').before(errorHtml);
            }
        }
        
        actualizarSegmentosDesdeDOM() {
            this.segmentos = [];
            $('.segmento-item').each((index, elemento) => {
                const $elemento = $(elemento);
                const segmento = {
                    inicio: $elemento.find('.segmento-inicio').val(),
                    fin: $elemento.find('.segmento-fin').val(),
                    tipo: $elemento.find('.segmento-tipo').val()
                };
                this.segmentos.push(segmento);
            });
        }
        
        actualizarJSON() {
            // Actualizar el campo segmentos_horas
            $('#id_segmentos_horas').val(JSON.stringify(this.segmentos));
        }
    }
    
    // Inicializar cuando el DOM esté listo
    $(document).ready(function() {
        console.log('✅ DOM listo - Inicializando interfaz de segmentos');
        
        // Agregar controles de segmentos si no existen
        if ($('.segmentos-container').length === 0) {
            console.log('Creando controles de segmentos...');
            
            const controlesHTML = `
                <div class="segmentos-container">
                    <h4>Configuración de Segmentos</h4>
                    <div class="controles-segmentos">
                        <button type="button" class="btn-segmento success btn-agregar-segmento">
                            Agregar Segmento
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="N">
                            Normal
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="F">
                            Festivo
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="E">
                            Especial
                        </button>
                    </div>
                    <div class="segmentos-lista"></div>
                </div>
            `;
            
            // Buscar el campo segmentos_horas y insertar después
            const segmentosField = $('#id_segmentos_horas');
            if (segmentosField.length) {
                console.log('Campo segmentos_horas encontrado, insertando controles...');
                segmentosField.closest('.form-row').after(controlesHTML);
            } else {
                console.log('Campo segmentos_horas no encontrado, insertando al final del formulario...');
                $('form').append(controlesHTML);
            }
        }
        
        // Inicializar la interfaz
        window.codigoTurnoAdmin = new CodigoTurnoAdmin();
        window.codigoTurnoAdmin.init();
        console.log('✅ Interfaz de segmentos inicializada');
    });
    
})(django.jQuery); 