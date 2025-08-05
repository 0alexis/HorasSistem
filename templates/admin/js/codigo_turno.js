/**
 * JavaScript simplificado para formato militar directo
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
            this.forzarFormatoMilitar();
        }
        
        forzarFormatoMilitar() {
            const formatearHora = (valor) => {
                if (!valor) return '';
                
                // Remover cualquier carácter no numérico excepto :
                valor = valor.replace(/[^\d:]/g, '');
                
                // Separar horas, minutos y segundos
                let [horas = 0, minutos = 0, segundos = 0] = valor.split(':').map(n => parseInt(n, 10));
                
                // Validar y ajustar valores
                horas = !isNaN(horas) ? Math.min(23, Math.max(0, horas)) : 0;
                minutos = !isNaN(minutos) ? Math.min(59, Math.max(0, minutos)) : 0;
                segundos = !isNaN(segundos) ? Math.min(59, Math.max(0, segundos)) : 0;
                
                // Retornar formato HH:mm:ss
                return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
            };

            // Reemplazar inputs time con inputs text personalizados
            $('input[type="time"]').each(function() {
                const $original = $(this);
                const $nuevo = $('<input>', {
                    type: 'text',
                    class: $original.attr('class') + ' tiempo-militar',
                    value: formatearHora($original.val()),
                    placeholder: 'HH:mm:ss',
                    maxlength: 8
                });

                // Eventos para el nuevo input
                $nuevo.on('input', function(e) {
                    let valor = $(this).val();
                    
                    // Permitir solo números y :
                    valor = valor.replace(/[^\d:]/g, '');
                    
                    // Auto-insertar : después de 2 y 5 dígitos
                    if (valor.length === 2 && valor.indexOf(':') === -1) {
                        valor += ':';
                    }
                    if (valor.length === 5 && valor.split(':').length === 2) {
                        valor += ':';
                    }
                    
                    $(this).val(valor);
                });

                $nuevo.on('blur', function() {
                    const valorFormateado = formatearHora($(this).val());
                    $(this).val(valorFormateado);
                    $original.val(valorFormateado).trigger('change');
                });

                // Reemplazar el input original
                $original.hide().after($nuevo);
            });

            // Actualizar estilos
            if (!$('#military-time-custom').length) {
                $('head').append(`
                    <style id="military-time-custom">
                        input.tiempo-militar {
                            width: 100px !important;
                            text-align: center !important;
                            font-family: monospace !important;
                            font-size: 14px !important;
                            padding: 5px !important;
                            border: 1px solid #ccc !important;
                            border-radius: 4px !important;
                        }
                        input.tiempo-militar:focus {
                            outline: none !important;
                            border-color: #2271b1 !important;
                            box-shadow: 0 0 0 1px #2271b1 !important;
                        }
                        input.tiempo-militar::placeholder {
                            color: #999 !important;
                        }
                    </style>
                `);
            }
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
                this.validarSegmentos();
            });
        }
        
        cargarSegmentosExistentes() {
            const segmentosJson = $('#id_segmentos_json').val();
            if (segmentosJson) {
                try {
                    this.segmentos = JSON.parse(segmentosJson);
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
                    <strong>ℹ️ Información:</strong> ${info}
                </div>
            `);
        }
        
        renderizarSegmentos() {
            const container = $('.segmentos-lista');
            container.empty();
            
            this.segmentos.forEach((segmento, index) => {
                const html = this.crearHTMLSegmento(segmento, index);
                container.append(html);
            });
            
            // Aplicar formato militar a los nuevos inputs
            this.forzarFormatoMilitar();
            
            this.actualizarJSON();
        }
        
        crearHTMLSegmento(segmento, index) {
            const tiposOptions = SEGMENTO_TIPOS.map(([valor, etiqueta]) => 
                `<option value="${valor}" ${segmento.tipo === valor ? 'selected' : ''}>${etiqueta}</option>`
            ).join('');
            
            return `
                <div class="segmento-item" data-index="${index}">
                    <div class="segmento-numero">${index + 1}</div>
                    <div class="segmento-campos">
                        <input type="text" 
                               value="${segmento.inicio}" 
                               placeholder="HH:mm:ss" 
                               class="segmento-inicio tiempo-militar" 
                               maxlength="8"
                               data-tipo="inicio"
                               aria-label="Hora inicio">
                        <input type="text" 
                               value="${segmento.fin}" 
                               placeholder="HH:mm:ss" 
                               class="segmento-fin tiempo-militar" 
                               maxlength="8"
                               data-tipo="fin"
                               aria-label="Hora fin">
                        <select class="segmento-tipo">
                            ${tiposOptions}
                        </select>
                    </div>
                </div>
            `;
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
            
            // Validar formato militar
            for (let i = 0; i < this.segmentos.length; i++) {
                const segmento = this.segmentos[i];
                const regex = /^([0-1][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$/;
                
                if (segmento.inicio && !regex.test(segmento.inicio)) {
                    errores.push(`Segmento ${i + 1}: Hora de inicio debe estar en formato militar (00:00:00 a 23:59:59)`);
                }
                
                if (segmento.fin && !regex.test(segmento.fin)) {
                    errores.push(`Segmento ${i + 1}: Hora de fin debe estar en formato militar (00:00:00 a 23:59:59)`);
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
        
        validarFormatoTiempo(valor) {
            if (!valor) return false;
            
            // Validar formato HH:mm:ss
            const regex = /^([0-1][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$/;
            if (!regex.test(valor)) return false;
            
            const [horas, minutos, segundos] = valor.split(':').map(Number);
            return (
                horas >= 0 && horas <= 23 &&
                minutos >= 0 && minutos <= 59 &&
                segundos >= 0 && segundos <= 59
            );
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
        
        mostrarErrores(errores) {
            $('.segmentos-error').remove();
            
            if (errores.length > 0) {
                const errorHtml = `
                    <div class="segmentos-error tipo-turno-info error">
                        <strong>⚠️ Errores de validación:</strong>
                        <ul>
                            ${errores.map(error => `<li>${error}</li>`).join('')}
                        </ul>
                    </div>
                `;
                $('.segmentos-container').before(errorHtml);
            }
        }
        
        actualizarJSON() {
            $('#id_segmentos_json').val(JSON.stringify(this.segmentos));
        }
    }
    
    // Inicializar cuando el DOM esté listo
    $(document).ready(function() {
        // Agregar controles de segmentos si no existen
        if ($('.segmentos-container').length === 0) {
            const controlesHTML = `
                <div class="segmentos-container">
                    <h4>Configuración de Segmentos</h4>
                    <div class="controles-segmentos">
                        <button type="button" class="btn-segmento success btn-agregar-segmento">
                            ➕ Agregar Segmento
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="N">
                            📋 Normal
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="F">
                            📋 Festivo
                        </button>
                        <button type="button" class="btn-segmento btn-plantilla" data-plantilla="E">
                            📋 Especial
                        </button>
                    </div>
                    <div class="segmentos-lista"></div>
                </div>
            `;
            
            $('#id_segmentos_json').closest('.form-row').after(controlesHTML);
        }
        
        // Inicializar la interfaz y guardar la instancia globalmente
        window.codigoTurnoAdmin = new CodigoTurnoAdmin();
        console.log('✅ Interfaz inicializada correctamente');
    });
    
})(django.jQuery);