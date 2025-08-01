/**
 * JavaScript para la interfaz de códigos de turno
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
        'N': { // Normal
            nombre: 'Turno Normal',
            segmentos: [
                {inicio: '08:00', fin: '16:00', tipo: 'NORMAL'}
            ]
        },
        'F': { // Festivo
            nombre: 'Turno Festivo Estándar',
            segmentos: [
                {inicio: '08:00', fin: '12:00', tipo: 'NORMAL'},
                {inicio: '12:00', fin: '16:00', tipo: 'FESTIVO'}
            ]
        },
        'FO': { // Festivo Ordinario
            nombre: 'Turno Festivo Ordinario',
            segmentos: [
                {inicio: '08:00', fin: '12:00', tipo: 'NORMAL'},
                {inicio: '12:00', fin: '16:00', tipo: 'FESTIVO'}
            ]
        },
        'E': { // Especial
            nombre: 'Turno Especial',
            segmentos: [
                {inicio: '06:00', fin: '08:00', tipo: 'NOCTURNO'},
                {inicio: '08:00', fin: '12:00', tipo: 'NORMAL'},
                {inicio: '12:00', fin: '16:00', tipo: 'FESTIVO'}
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
                        <input type="time" value="${segmento.inicio}" placeholder="Inicio" class="segmento-inicio">
                        <input type="time" value="${segmento.fin}" placeholder="Fin" class="segmento-fin">
                        <select class="segmento-tipo">
                            ${tiposOptions}
                        </select>
                    </div>
                    <div class="segmento-acciones">
                        <button type="button" class="btn-segmento danger btn-eliminar-segmento" data-index="${index}">
                            🗑️ Eliminar
                        </button>
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
                inicio: '08:00',
                fin: '16:00',
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
        
        // Inicializar la interfaz
        new CodigoTurnoAdmin();
    });
    
})(django.jQuery); 