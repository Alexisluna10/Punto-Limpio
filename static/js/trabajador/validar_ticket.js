let pedidoActualId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Detectar "Enter" en el input
    const inputFolio = document.getElementById('inputFolio');
    if (inputFolio) {
        inputFolio.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') buscarFolio();
        });
        inputFolio.focus();
    }
});

// --- FUNCIONES GLOBALES (Asignadas a window) ---

window.buscarFolio = function() {
    const folio = document.getElementById('inputFolio').value.trim();
    const msgError = document.getElementById('mensajeError');
    const btnBuscar = document.querySelector('button[onclick="buscarFolio()"]');
    
    if (!folio) {
        msgError.innerText = "Por favor escribe un folio.";
        msgError.style.display = 'block';
        return;
    }

    // UI Loading
    msgError.style.display = 'none';
    btnBuscar.disabled = true;
    btnBuscar.innerHTML = "⌛ BUSCANDO...";

    // USAMOS LA URL INYECTADA
    fetch(`${window.DjangoData.urls.buscarFolio}?folio=${encodeURIComponent(folio)}`)
        .then(res => {
            if(res.status === 404) throw new Error("Pedido no encontrado.");
            if(!res.ok) throw new Error("Error en el servidor.");
            return res.json();
        })
        .then(data => {
            if (data.success) {
                mostrarModal(data.pedido);
            } else {
                throw new Error(data.message);
            }
        })
        .catch(err => {
            msgError.innerText = err.message;
            msgError.style.display = 'block';
            if (navigator.vibrate) navigator.vibrate(200);
        })
        .finally(() => {
            btnBuscar.disabled = false;
            btnBuscar.innerHTML = "<span>🔍</span> BUSCAR FOLIO";
        });
};

window.cerrarModal = function() {
    document.getElementById('modalDetalleEntrega').style.display = 'none';
    const input = document.getElementById('inputFolio');
    input.value = '';
    input.focus();
};

window.confirmarEntrega = function() {
    if(!pedidoActualId) return;

    const btn = document.getElementById('btnEntregar');
    const textoOriginal = btn.innerText; // Guardamos texto actual (ej: COBRAR...)
    
    btn.disabled = true;
    btn.innerText = "Procesando...";

    // USAMOS URL Y TOKEN INYECTADOS
    fetch(window.DjangoData.urls.entregarPedido, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.DjangoData.csrfToken
        },
        body: JSON.stringify({ pedido_id: pedidoActualId })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            // Sonido de éxito (opcional)
            const audio = new Audio("https://actions.google.com/sounds/v1/cartoon/clank_car_crash.ogg");
            // audio.play().catch(e => console.log("Audio bloqueado por navegador"));
            
            alert(data.message);
            cerrarModal();
        } else {
            alert("⚠️ Error: " + data.message);
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error de conexión");
        btn.disabled = false;
        btn.innerText = textoOriginal;
    });
};

// --- FUNCIONES INTERNAS (Helpers) ---

function mostrarModal(pedido) {
    pedidoActualId = pedido.id;
    
    // 1. Datos Básicos
    document.getElementById('modalFolio').innerText = "#" + pedido.folio;
    document.getElementById('modalCliente').innerText = pedido.cliente;
    document.getElementById('modalTotal').innerText = "$" + pedido.total.toFixed(2);
    
    // 2. Badge de Pago
    const badgePago = document.getElementById('modalPago');
    if(pedido.estado_pago_raw === 'pagado') {
        badgePago.className = 'badge badge-pagado';
        badgePago.innerText = 'PAGADO';
    } else {
        badgePago.className = 'badge badge-pendiente';
        badgePago.innerText = 'PENDIENTE DE PAGO';
    }

    // 3. Items
    const lista = document.getElementById('modalItems');
    lista.innerHTML = '';
    if (pedido.items && pedido.items.length > 0) {
        pedido.items.forEach(item => {
            const li = document.createElement('li');
            li.innerText = item;
            lista.appendChild(li);
        });
    } else {
        lista.innerHTML = '<li style="color: #999;">Sin detalles registrados</li>';
    }

    // 4. LÓGICA DE VALIDACIÓN (SEMÁFORO)
    const btnEntregar = document.getElementById('btnEntregar');
    
    // Reset estilos base
    btnEntregar.className = "btn-submit"; 
    btnEntregar.style.opacity = "1";
    btnEntregar.disabled = false;

    if (pedido.estado_raw === 'entregado') {
        // CASO: YA ENTREGADO
        configurarAlerta('gris', 'ESTE PEDIDO YA FUE ENTREGADO');
        btnEntregar.disabled = true;
        btnEntregar.innerText = "ENTREGADO";
        btnEntregar.style.background = "#9e9e9e";

    } else if (pedido.estado_raw === 'cancelado') {
        // CASO: CANCELADO
        configurarAlerta('rojo', 'PEDIDO CANCELADO');
        btnEntregar.disabled = true;
        btnEntregar.innerText = "CANCELADO";
        btnEntregar.style.background = "#d32f2f";

    } else if (pedido.estado_raw !== 'listo') {
        // CASO: NO ESTÁ LISTO (Pendiente o En Proceso)
        configurarAlerta('naranja', `NO SE PUEDE ENTREGAR (Estatus: ${pedido.estado})`);
        btnEntregar.disabled = true;
        btnEntregar.innerText = "🚫 AÚN NO ESTÁ LISTO";
        btnEntregar.style.background = "#ff9800";
        btnEntregar.style.color = "white";

    } else {
        // CASO: ESTÁ LISTO (Verificamos pago)
        if (pedido.estado_pago_raw === 'pendiente') {
            // LISTO + DEBE PAGAR
            configurarAlerta('verde', '¡LISTO! SE REQUIERE COBRO');
            btnEntregar.innerText = `💰 COBRAR $${pedido.total.toFixed(2)} Y ENTREGAR`;
            btnEntregar.style.background = "#4CAF50"; 
        } else {
            // LISTO + YA PAGÓ
            configurarAlerta('azul', '¡LISTO PARA ENTREGAR!');
            btnEntregar.innerText = "✅ CONFIRMAR ENTREGA";
            btnEntregar.style.background = "#008CC9"; 
        }
    }

    document.getElementById('modalDetalleEntrega').style.display = 'flex';
}

function configurarAlerta(tipo, texto) {
    const alerta = document.getElementById('alertaEstado');
    alerta.innerText = texto;
    
    // Reset de bordes y colores inline anteriores para asegurar limpieza
    alerta.style.border = "1px solid transparent";

    if (tipo === 'rojo') {
        alerta.style.background = '#ffebee'; alerta.style.color = '#c62828'; alerta.style.borderColor = '#ffcdd2';
    } else if (tipo === 'naranja') {
        alerta.style.background = '#fff3e0'; alerta.style.color = '#ef6c00'; alerta.style.borderColor = '#ffe0b2';
    } else if (tipo === 'gris') {
        alerta.style.background = '#f5f5f5'; alerta.style.color = '#616161'; alerta.style.borderColor = '#e0e0e0';
    } else if (tipo === 'verde') {
        alerta.style.background = '#e8f5e9'; alerta.style.color = '#2e7d32'; alerta.style.borderColor = '#c8e6c9';
    } else { // Azul
        alerta.style.background = '#e3f2fd'; alerta.style.color = '#0277bd'; alerta.style.borderColor = '#b3e5fc';
    }
}