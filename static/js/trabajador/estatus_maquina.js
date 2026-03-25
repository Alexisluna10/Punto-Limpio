document.addEventListener("DOMContentLoaded", function () {
    // Iniciar los cronómetros inmediatamente y luego actualizar cada segundo
    actualizarCronometros();
    setInterval(actualizarCronometros, 1000);
});

// --- LÓGICA DE CRONÓMETRO PRECISO (TIEMPO REAL) ---
function actualizarCronometros() {
    const contenedores = document.querySelectorAll(".timer-container");

    contenedores.forEach((div) => {
        // Leemos los datos directamente del HTML (Data Attributes)
        const fechaInicioStr = div.getAttribute("data-inicio");
        const duracionMin = parseInt(div.getAttribute("data-duracion"));
        const spanTiempo = div.querySelector(".tiempo-restante");
        
        // Obtenemos el ID de la máquina desde el ID del elemento (timer-box-15 -> 15)
        const maquinaId = div.id.split("-")[2];
        const btnLiberar = document.getElementById("btn-liberar-" + maquinaId);

        if (!fechaInicioStr || !duracionMin) return;

        const fechaInicio = new Date(fechaInicioStr);
        // Calculamos fecha fin sumando minutos a la fecha inicio
        const fechaFin = new Date(fechaInicio.getTime() + duracionMin * 60000);
        const ahora = new Date();
        
        // Diferencia en milisegundos
        let diferenciaMs = fechaFin - ahora;

        if (diferenciaMs > 0) {
            // --- CASO 1: AÚN HAY TIEMPO ---
            const minutos = Math.floor((diferenciaMs % (1000 * 60 * 60)) / (1000 * 60));
            const segundos = Math.floor((diferenciaMs % (1000 * 60)) / 1000);

            const minStr = minutos < 10 ? "0" + minutos : minutos;
            const segStr = segundos < 10 ? "0" + segundos : segundos;

            spanTiempo.innerText = `${minStr}:${segStr} min`;
            spanTiempo.style.color = "#E53935";

            // Bloquear botón de terminar si el ciclo sigue
            if (btnLiberar) {
                btnLiberar.disabled = true;
                btnLiberar.innerText = "Ciclo en curso...";
                btnLiberar.style.opacity = "0.7";
                btnLiberar.style.cursor = "not-allowed";
                btnLiberar.style.borderColor = "#eee";
                btnLiberar.style.background = "#fff";
                btnLiberar.style.color = "#999";
                btnLiberar.classList.remove("pulsing");
            }
        } else {
            // --- CASO 2: SE ACABÓ EL TIEMPO ---
            spanTiempo.innerText = "00:00 - FINALIZADO";
            spanTiempo.style.color = "#D32F2F";
            spanTiempo.style.fontWeight = "900";
            
            // Alerta visual en el contenedor del timer
            div.style.backgroundColor = "#ffebee";
            div.style.border = "1px solid #ef5350";

            // Habilitar botón de terminar
            if (btnLiberar) {
                btnLiberar.disabled = false;
                btnLiberar.innerText = "TERMINAR CICLO";
                btnLiberar.style.opacity = "1";
                btnLiberar.style.cursor = "pointer";
                btnLiberar.style.backgroundColor = "#E53935";
                btnLiberar.style.color = "white";
                btnLiberar.style.borderColor = "#E53935";
                
                // Efecto de pulso para llamar la atención
                if (!btnLiberar.classList.contains("pulsing")) {
                    btnLiberar.classList.add("pulsing");
                }
            }
        }
    });
}

// --- FUNCIONES GLOBALES PARA MODALES (Window scope) ---

window.abrirModalAgregar = function() {
    document.getElementById("modalAgregarM").classList.add("open");
};

window.cerrarModalAgregar = function() {
    document.getElementById("modalAgregarM").classList.remove("open");
};

window.abrirOpciones = function(id, nombre) {
    document.getElementById("tituloMaquinaOpc").innerText = "Gestionar: " + nombre;
    document.getElementById("input_maquina_id_opc").value = id;
    document.getElementById("modalOpciones").classList.add("open");
};

window.cerrarModalOpciones = function() {
    document.getElementById("modalOpciones").classList.remove("open");
};

window.enviarOpcion = function(accion) {
    let confirmacion = false;
    
    if (accion === "baja_definitiva") {
        confirmacion = confirm("¿Estás seguro de eliminar esta máquina? Esta acción no se puede deshacer.");
    } else if (accion === "reportar_mantenimiento") {
        confirmacion = confirm("¿Poner en mantenimiento? No se podrá usar hasta reactivarla.");
    } else if (accion === "reactivar") {
        confirmacion = true;
    }

    if (confirmacion) {
        document.getElementById("input_accion_opc").value = accion;
        // Enviamos el formulario estándar (no AJAX)
        document.getElementById("formOpciones").submit();
    }
};