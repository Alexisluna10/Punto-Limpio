window.enviarReporte = function(event) {
    event.preventDefault();
    
    const form = document.getElementById('formIncidencia');
    // FormData captura automáticamente todos los inputs, incluido el archivo y el CSRF Token
    const formData = new FormData(form);
    const btnEnviar = document.getElementById('btnEnviar');
    
    // UI Loading
    btnEnviar.disabled = true;
    btnEnviar.textContent = 'Enviando...';
    
    // USAMOS LA URL INYECTADA
    fetch(window.DjangoData.urls.incidencias, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            // Nota: Al usar FormData, NO se debe poner 'Content-Type': 'application/json'
            // El navegador se encarga de eso automáticamente para manejar el archivo adjunto.
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarModalExito();
        } else {
            alert('Error: ' + data.message);
            resetBoton(btnEnviar);
        }
    })
    .catch(error => {
        alert('Error al enviar la incidencia. Por favor intenta de nuevo.');
        console.error('Error:', error);
        resetBoton(btnEnviar);
    });
};

window.cerrarModal = function() {
    const modal = document.getElementById('modalIncidencia');
    modal.classList.remove('open');
    setTimeout(() => {
        modal.style.display = 'none';
        // Recargar para ver la nueva incidencia en la lista
        window.location.reload();
    }, 300);
};

// --- FUNCIONES INTERNAS ---

function mostrarModalExito() {
    const modal = document.getElementById('modalIncidencia');
    modal.style.display = 'flex';
    // Pequeño delay para permitir que la transición CSS se vea suave
    setTimeout(() => {
        modal.classList.add('open');
    }, 10);
}

function resetBoton(btn) {
    btn.disabled = false;
    btn.textContent = 'Enviar Reporte';
}