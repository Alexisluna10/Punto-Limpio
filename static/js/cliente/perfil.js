document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.perfil-form-premium');
    const btnGuardar = document.getElementById('btnGuardar');

    if (!form || !btnGuardar) {
        console.warn('Formulario de perfil o botón Guardar no encontrados');
        return;
    }

    const inputs = form.querySelectorAll('input:not([disabled]), textarea');
    const valoresOriginales = {};

    inputs.forEach(input => {
        valoresOriginales[input.name] = input.value;
        input.addEventListener('input', verificarCambios);
    });

    function verificarCambios() {
        let hayCambios = false;

        inputs.forEach(input => {
            if (input.value !== valoresOriginales[input.name]) {
                hayCambios = true;
            }
        });

        if (hayCambios) {
            btnGuardar.disabled = false;
            btnGuardar.classList.add('activo');
        } else {
            btnGuardar.disabled = true;
            btnGuardar.classList.remove('activo');
        }
    }
});
