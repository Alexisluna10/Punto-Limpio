document.addEventListener('DOMContentLoaded', function() {
    initDatos();
    initListeners();
});

// Variables Globales del Módulo
let catalogoPrendas = [];
let itemsAgregados = [];
let clienteSeleccionadoId = null;
let timeoutBusqueda = null;

function initDatos() {
    // 1. Carga Segura de Datos desde el JSON Script del HTML
    try {
        const scriptData = document.getElementById('prendas-data');
        if (scriptData) {
            catalogoPrendas = JSON.parse(scriptData.textContent);
        }
    } catch (e) {
        console.warn("No se cargaron prendas:", e);
        catalogoPrendas = [];
    }

    // 2. Llenar Select de Prendas
    const select = document.getElementById('select_prenda_especial');
    if (select) {
        if (catalogoPrendas.length > 0) {
            catalogoPrendas.forEach(p => {
                let option = document.createElement('option');
                option.value = p.id;
                option.text = `${p.nombre} - $${p.precio.toFixed(2)}`;
                option.setAttribute('data-precio', p.precio);
                select.appendChild(option);
            });
        } else {
            let option = document.createElement('option');
            option.text = "No hay prendas registradas";
            select.appendChild(option);
        }
    }

    // 3. Configuración Inicial
    verificarServicio();
    const inputBuscar = document.getElementById('buscarCliente');
    if (inputBuscar) inputBuscar.focus();
}

function initListeners() {
    // Listener para buscador de clientes
    const inputBuscar = document.getElementById('buscarCliente');
    if (inputBuscar) {
        inputBuscar.addEventListener('input', function() {
            const query = this.value.trim();
            const resultadosDiv = document.getElementById('resultadosClientes');

            if (timeoutBusqueda) clearTimeout(timeoutBusqueda);
            
            if (query.length < 2) {
                resultadosDiv.style.display = 'none';
                return;
            }
            
            timeoutBusqueda = setTimeout(() => {
                // USAMOS LA URL INYECTADA DESDE EL HTML
                fetch(`${window.DjangoData.urls.buscarCliente}?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        resultadosDiv.innerHTML = '';
                        if (data.clientes.length === 0) {
                            resultadosDiv.innerHTML = '<div class="autocomplete-item" style="color:#666; font-style:italic;">No se encontraron clientes</div>';
                        } else {
                            data.clientes.forEach(c => {
                                const div = document.createElement('div');
                                div.className = 'autocomplete-item';
                                div.innerHTML = `
                                    <div style="font-weight:600; color:#333;">${c.nombre_completo}</div>
                                    <div style="font-size:0.85em; color:#888;">Tel: ${c.telefono}</div>
                                `;
                                div.onclick = () => seleccionarCliente(c);
                                resultadosDiv.appendChild(div);
                            });
                        }
                        resultadosDiv.style.display = 'block';
                    })
                    .catch(err => console.error(err));
            }, 300);
        });
    }

    // Cerrar autocompletado al hacer click fuera
    document.addEventListener('click', function(e) {
        const resultadosDiv = document.getElementById('resultadosClientes');
        if (resultadosDiv && !e.target.closest('.form-group')) {
            resultadosDiv.style.display = 'none';
        }
    });
}

// --- FUNCIONES GLOBALES (Asignadas a window para que el HTML las vea) ---

window.seleccionarCliente = function(c) {
    clienteSeleccionadoId = c.id;
    document.getElementById('clienteId').value = c.id;
    document.getElementById('buscarCliente').value = '';
    document.getElementById('resultadosClientes').style.display = 'none';
    document.getElementById('clienteNombre').innerText = c.nombre_completo;
    document.getElementById('clienteSeleccionado').style.display = 'block';
    document.getElementById('buscarCliente').parentElement.parentElement.style.display = 'none';
};

window.limpiarCliente = function() {
    clienteSeleccionadoId = null;
    document.getElementById('clienteId').value = '';
    document.getElementById('clienteSeleccionado').style.display = 'none';
    document.getElementById('buscarCliente').parentElement.parentElement.style.display = 'flex';
    document.getElementById('buscarCliente').focus();
};

window.calcularTotal = function() {
    const pesoNorm = parseFloat(document.getElementById('pesoNormal').value) || 0;
    const pesoSucio = parseFloat(document.getElementById('pesoSucio').value) || 0;
    
    const precios = window.DjangoData.precios || { tintoreria: 80, a_domicilio: 50, por_encargo: 20 };
    // Precio base por kilo (Podría venir del backend también)
    const costoNorm = pesoNorm * 23.00; 
    const costoSucio = pesoSucio * 30.00;

    const tipo = document.getElementById('tipoServicioSelect').value;
    let costoServicio = 0;
    let txtServicio = "";
    
    if (tipo === 'por_encargo') { 
        costoServicio = precios.por_encargo; 
        txtServicio = `+ Encargo $${costoServicio}`; 
    } else if (tipo === 'a_domicilio') { 
        costoServicio = precios.a_domicilio; 
        txtServicio = `+ Domicilio $${costoServicio}`; 
    } else if (tipo === 'tintoreria') { 
        costoServicio = precios.tintoreria; 
        txtServicio = `+ Tintorería $${costoServicio}`; 
    }
    // Tintoreria tiene costo base 0

    let costoExtras = itemsAgregados.reduce((sum, i) => sum + i.subtotal, 0);
    const total = costoNorm + costoSucio + costoServicio + costoExtras;
    
    document.getElementById('totalEstimado').value = total.toFixed(2);

    let resumen = [];
    if(pesoNorm > 0) resumen.push(`Normal: $${costoNorm.toFixed(2)}`);
    if(pesoSucio > 0) resumen.push(`Sucia: $${costoSucio.toFixed(2)}`);
    if(costoServicio > 0) resumen.push(txtServicio);
    if(costoExtras > 0) resumen.push(`Extras: $${costoExtras.toFixed(2)}`);
    
    document.getElementById('resumenCostos').innerText = resumen.length > 0 ? resumen.join(" | ") : "Esperando datos...";
};

window.agregarPrenda = function() {
    const select = document.getElementById('select_prenda_especial');
    const id = select.value;
    
    if (!id) { alert("Selecciona una prenda"); return; }

    const nombre = select.options[select.selectedIndex].text.split(' - ')[0];
    const precio = parseFloat(select.options[select.selectedIndex].getAttribute('data-precio'));
    const cantidad = parseInt(document.getElementById('cantidad_prenda').value) || 1;

    if (cantidad < 1) return;

    const existe = itemsAgregados.find(i => i.id === id);
    if (existe) {
        existe.cantidad += cantidad;
        existe.subtotal = existe.cantidad * existe.precio;
    } else {
        itemsAgregados.push({
            id: id, nombre: nombre, precio: precio, cantidad: cantidad, subtotal: cantidad * precio
        });
    }

    renderizarTabla();
    calcularTotal();
    select.value = "";
    document.getElementById('cantidad_prenda').value = 1;
};

window.eliminarPrenda = function(index) {
    itemsAgregados.splice(index, 1);
    renderizarTabla();
    calcularTotal();
};

function renderizarTabla() {
    const tbody = document.getElementById('lista_prendas_body');
    const mensaje = document.getElementById('mensajeSinPrendas');
    tbody.innerHTML = '';

    if (itemsAgregados.length === 0) {
        mensaje.style.display = 'block';
    } else {
        mensaje.style.display = 'none';
        itemsAgregados.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding:10px;">${item.nombre}</td>
                <td style="padding:10px; text-align:center;">${item.cantidad}</td>
                <td style="padding:10px; text-align:right;">$${item.precio.toFixed(2)}</td>
                <td style="padding:10px; text-align:right;">$${item.subtotal.toFixed(2)}</td>
                <td style="padding:10px; text-align:center;">
                    <button type="button" onclick="eliminarPrenda(${index})" style="color:red; background:none; border:none; cursor:pointer;">✕</button>
                </td>
            `;
            tr.style.borderBottom = "1px solid #eee";
            tbody.appendChild(tr);
        });
    }
}

window.guardarOrden = function() {
    // --- A) Validar Cliente ---
    if (!clienteSeleccionadoId) {
        alert('⚠️ ¡Falta el Cliente! Por favor busca o registra uno.');
        document.getElementById('buscarCliente').focus();
        return; 
    }

    // --- B) Validar Contenido del Pedido ---
    const tipo = document.getElementById('tipoServicioSelect').value;
    const pesoNorm = parseFloat(document.getElementById('pesoNormal').value) || 0;
    const pesoSucio = parseFloat(document.getElementById('pesoSucio').value) || 0;
    const prendasEspeciales = itemsAgregados.length;

    if (pesoNorm === 0 && pesoSucio === 0 && prendasEspeciales === 0) {
        alert('⚠️ ¡El pedido está vacío! Ingresa el peso de la ropa o agrega prendas especiales.');
        document.getElementById('pesoNormal').focus();
        return;
    }

    // --- C) Validar Fecha de Entrega ---
    if (tipo !== 'autoservicio') {
        const fecha = document.getElementById('fechaEntrega').value;
        if (!fecha) {
            alert('⚠️ Selecciona una Fecha de Entrega.');
            document.getElementById('fechaEntrega').focus();
            return;
        }
    }
    
    // --- D) Validar Total ---
    const total = parseFloat(document.getElementById('totalEstimado').value) || 0;
    if (total <= 0) {
        alert('⚠️ El total no puede ser $0.00.');
        return;
    }

    const btnGuardar = document.querySelector('button[onclick="guardarOrden()"]');
    btnGuardar.disabled = true;
    btnGuardar.innerText = "Guardando...";

    const payload = {
        cliente_id: clienteSeleccionadoId,
        tipo_servicio: tipo,
        peso_normal: pesoNorm,
        peso_sucio: pesoSucio,
        items_especiales: itemsAgregados,
        fecha_entrega: document.getElementById('fechaEntrega').value,
        metodo_pago: document.getElementById('metodoPago').value,
        observaciones: document.getElementById('observaciones').value,
        total: total
    };

    // USAMOS LA URL Y TOKEN INYECTADOS
    fetch(window.DjangoData.urls.nuevoServicio, {
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
            if (data.ticket_url) {
                window.open(data.ticket_url, '_blank');
            }
            
            document.getElementById("formContainer").style.display = "none";
            document.getElementById("folioGenerado").textContent = "Folio: " + data.folio;
            document.getElementById("pantallaExito").style.display = "flex";
        } else {
            alert('Error: ' + data.message);
            btnGuardar.disabled = false;
            btnGuardar.innerText = "Generar Orden";
        }
    })
    .catch(err => {
        console.error(err);
        alert('Error de conexión.');
        btnGuardar.disabled = false;
        btnGuardar.innerText = "Generar Orden";
    });
};

window.verificarServicio = function() {
    const tipo = document.getElementById('tipoServicioSelect').value;
    const divFecha = document.getElementById('divFechaEntrega');
    if (tipo === 'autoservicio') divFecha.style.display = 'none';
    else divFecha.style.display = 'block';
    calcularTotal();
};

// --- MODAL NUEVO CLIENTE ---
window.abrirModalCliente = function() { document.getElementById('modalNuevoCliente').style.display = 'flex'; };
window.cerrarModalCliente = function() { document.getElementById('modalNuevoCliente').style.display = 'none'; };

window.guardarClienteRapido = function() {
    const nombre = document.getElementById('newNombre').value;
    const telefono = document.getElementById('newTelefono').value;
    
    if (!nombre || !telefono) return alert("Nombre y Teléfono requeridos");

    fetch(window.DjangoData.urls.registrarCliente, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.DjangoData.csrfToken
        },
        body: JSON.stringify({
            nombre: nombre,
            apellido: document.getElementById('newApellido').value,
            telefono: telefono,
            email: document.getElementById('newEmail').value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            seleccionarCliente(data.cliente);
            cerrarModalCliente();
        } else {
            const errDiv = document.getElementById('errorMsgCliente');
            errDiv.innerText = data.message;
            errDiv.style.display = 'block';
        }
    });
};