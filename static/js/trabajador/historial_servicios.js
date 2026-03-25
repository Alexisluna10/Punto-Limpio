document.addEventListener('DOMContentLoaded', function() {
    // Vinculamos el evento al input de búsqueda
    const inputBusqueda = document.getElementById('inputBusquedaHistorial');
    
    if (inputBusqueda) {
        // Usamos 'input' en lugar de 'keyup' para detectar pegado de texto también
        inputBusqueda.addEventListener('input', function() {
            filtrarHistorial(this.value);
        });
        
        // Foco inicial opcional
        inputBusqueda.focus();
    }
});

function filtrarHistorial(texto) {
    const textoLimpio = texto.toLowerCase().trim();
    const tarjetas = document.querySelectorAll('.trab-serv-card');
    let encontrados = 0;
    
    tarjetas.forEach(card => {
        // Buscamos en todo el texto de la tarjeta
        const contenido = card.innerText.toLowerCase();
        
        if (contenido.includes(textoLimpio)) {
            card.style.display = 'block';
            encontrados++;
        } else {
            card.style.display = 'none';
        }
    });

    // Opcional: Mostrar mensaje si no hay resultados en la búsqueda
    manejarMensajeVacio(encontrados, tarjetas.length);
}

function manejarMensajeVacio(visibles, total) {
    // Buscamos si ya existe el mensaje de "No hay resultados"
    let msgNoResult = document.getElementById('msgNoResultados');
    
    if (visibles === 0 && total > 0) {
        if (!msgNoResult) {
            const grid = document.getElementById('gridHistorial');
            msgNoResult = document.createElement('div');
            msgNoResult.id = 'msgNoResultados';
            msgNoResult.style.gridColumn = '1 / -1';
            msgNoResult.style.textAlign = 'center';
            msgNoResult.style.padding = '40px';
            msgNoResult.style.color = '#666';
            msgNoResult.innerHTML = '<p>🔍 No se encontraron coincidencias.</p>';
            grid.appendChild(msgNoResult);
        } else {
            msgNoResult.style.display = 'block';
        }
    } else {
        if (msgNoResult) msgNoResult.style.display = 'none';
    }
}