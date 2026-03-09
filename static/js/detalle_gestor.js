// Función principal que maneja el formulario PQRS
function initPQRSForm() {
    // Elementos del DOM
    const estadoSelector = document.getElementById('estado-pqrs');
    const fechaInput = document.getElementById('fecha-respuesta');
    const form = document.querySelector('form');
    const notaEstado = document.getElementById('nota_estado');
    const calendarIcon = document.querySelector('.calendar-icon');

    // Obtener la última fecha de respuesta almacenada (pasada desde Django)
    const ultimaFechaRespuesta = fechaInput.dataset.ultimaFecha || null;

    // Función para formatear fecha al formato YYYY-MM-DDThh:mm
    function formatDateTime(date) {
        return date.toISOString().slice(0, 16);
    }

    // Configuración inicial del campo de fecha
    if (fechaInput) {
        // 1. Permitir edición manual
        fechaInput.readOnly = false;

        // 2. Configurar el campo con la fecha existente o vacío
        if (!fechaInput.value) {
            fechaInput.value = '';
        }

        // 3. Manejar clic en el icono de calendario
        if (calendarIcon) {
            calendarIcon.addEventListener('click', function() {
                fechaInput.showPicker();
            });
        }

        // 4. Habilitar edición con doble clic
        fechaInput.addEventListener('dblclick', function() {
            this.readOnly = !this.readOnly;
            this.classList.toggle('editing');

            const container = this.closest('.editable-date-container');
            if (container) container.classList.toggle('editing');

            if (!this.readOnly) {
                this.focus();
            }
        });
    }

    // Validación del formulario
    if (form && notaEstado) {
        form.addEventListener('submit', function(e) {
            const notaValue = notaEstado.value.trim();
            const placeholderText = notaEstado.getAttribute('placeholder') || '';
            const fechaSeleccionada = fechaInput.value;

            // Validar que la nota no esté vacía
            if (!notaValue || notaValue === placeholderText) {
                e.preventDefault();
                showValidationError('Debe ingresar una nota válida para el cambio de estado');
                return;
            }

            // Validar que se haya seleccionado una fecha de respuesta
            if (!fechaSeleccionada) {
                e.preventDefault();
                showValidationError('Debe seleccionar una fecha de respuesta', fechaInput);
                return;
            }

            // Validar formato de fecha
            if (!isValidDateTime(fechaSeleccionada)) {
                e.preventDefault();
                showValidationError('Formato de fecha/hora inválido', fechaInput);
                return;
            }

            // Validar que la fecha sea diferente a la última registrada
            if (ultimaFechaRespuesta && fechaSeleccionada === ultimaFechaRespuesta) {
                e.preventDefault();
                showValidationError('Debe modificar la fecha de respuesta para cambiar el estado', fechaInput);
                return;
            }
        });

        // Limpiar errores al escribir
        notaEstado.addEventListener('input', clearValidationMessages);
        fechaInput.addEventListener('input', clearValidationMessages);
    }

    // Mostrar error de validación
    function showValidationError(message, inputElement = null) {
        clearValidationMessages();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-error';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;

        form.prepend(errorDiv);

        if (inputElement) {
            inputElement.classList.add('error-field');
        } else {
            notaEstado.classList.add('error-field');
        }

        errorDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Limpiar mensajes de error
    function clearValidationMessages() {
        document.querySelectorAll('.alert-error').forEach(alert => alert.remove());
        document.querySelectorAll('.error-field').forEach(field => field.classList.remove('error-field'));
    }

    // Validar formato de fecha
    function isValidDateTime(dateTimeString) {
        const pattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
        return pattern.test(dateTimeString);
    }
}

// Inicialización
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    initPQRSForm();
} else {
    document.addEventListener('DOMContentLoaded', initPQRSForm);
}