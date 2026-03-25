window.prepararGuardado = function() {
    const estado = document.getElementById('selectEstado').value;
    
    // Si eligen "En Proceso", es obligatorio asignar máquina -> Abrimos Modal
    if (estado === 'en_proceso') {
        document.getElementById('modalSeleccionMaquina').classList.add('open');
    } else {
        // Cualquier otro estado se guarda directo
        confirmarYGuardar(true); // true = sin máquina asignada
    }
};

window.cerrarModalMaquina = function() {
    document.getElementById('modalSeleccionMaquina').classList.remove('open');
    // Resetear el select para que no se quede visualmente en "en_proceso" si el usuario canceló
    const selectEstado = document.getElementById('selectEstado');
    if (selectEstado) selectEstado.value = "";
};

window.confirmarYGuardar = function(sinMaquina = false) {
    let maquinaId = null;
    let tiempo = null;

    // Si requiere máquina, validamos que haya seleccionado una
    if (!sinMaquina) {
        maquinaId = document.getElementById('maquinaSeleccionada').value;
        tiempo = document.getElementById('tiempoCiclo').value;
        
        if (!maquinaId) { 
            alert("Por favor selecciona una máquina disponible."); 
            return; 
        }
    }

    // Preparamos datos del formulario
    const payload = {
        estado: document.getElementById('selectEstado').value,
        estado_pago: document.getElementById('selectPago').value,
        metodo_pago: document.getElementById('selectMetodoPago').value,
        notas: document.getElementById('notasAdicionales').value,
        maquina_id: maquinaId,
        tiempo_asignado: tiempo
    };

    // USAMOS LA URL Y TOKEN INYECTADOS
    // Nota: 'detalleServicio' ya contiene el ID del pedido correcto (ej: /servicios/detalle/15/)
    fetch(window.DjangoData.urls.guardarDetalle, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.DjangoData.csrfToken
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // Redirigir al panel de procesos tras éxito
            window.location.href = window.DjangoData.urls.serviciosProceso;
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error al conectar con el servidor.");
    });
};