
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function buscarItem() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const tables     = document.querySelectorAll('.tabla-precios tbody');

    tables.forEach(tbody => {
        tbody.querySelectorAll('tr[data-nombre]').forEach(row => {
            const nombre = row.dataset.nombre;
            row.classList.toggle('hidden-row', !nombre.includes(searchTerm));
        });
    });
}

function habilitarGuardar(input) {
    const btn      = input.closest('tr').querySelector('.btn-guardar');
    const original = parseFloat(input.dataset.original);
    const actual   = parseFloat(input.value);
    btn.disabled   = (original === actual);
}

function mostrarMensaje(row, mensaje, esError = false) {
    const mensajeSpan     = row.querySelector('.mensaje-estado');
    mensajeSpan.textContent = mensaje;
    mensajeSpan.className   = 'mensaje-estado ' + (esError ? 'mensaje-error' : 'mensaje-exito');
    setTimeout(() => { mensajeSpan.textContent = ''; }, 3000);
}

async function guardarPrecioPrenda(btn, id) {
    const row   = btn.closest('tr');
    const input = row.querySelector('.input-precio');
    const precio = parseFloat(input.value);

    try {
        const response = await fetch(urlActualizarPrecioPrenda, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ id, precio })
        });
        const data = await response.json();

        if (data.success) {
            input.dataset.original = precio;
            btn.disabled = true;
            mostrarMensaje(row, 'Guardado');
        } else {
            mostrarMensaje(row, data.mensaje, true);
        }
    } catch {
        mostrarMensaje(row, 'Error de conexion', true);
    }
}

async function guardarPrecioServicio(btn, id) {
    const row   = btn.closest('tr');
    const input = row.querySelector('.input-precio');
    const precio = parseFloat(input.value);

    try {
        const response = await fetch(urlActualizarPrecioServicio, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ id, precio })
        });
        const data = await response.json();

        if (data.success) {
            input.dataset.original = precio;
            btn.disabled = true;
            mostrarMensaje(row, 'Guardado');
        } else {
            mostrarMensaje(row, data.mensaje, true);
        }
    } catch {
        mostrarMensaje(row, 'Error de conexion', true);
    }
}

function abrirModalPrenda() {
    document.getElementById('modal-prenda').classList.add('activo');
    document.getElementById('nombre-prenda').value = '';
    document.getElementById('precio-prenda').value = '';
}

function abrirModalServicio() {
    document.getElementById('modal-servicio').classList.add('activo');
    document.getElementById('nombre-servicio').value  = '';
    document.getElementById('precio-servicio').value  = '';
    document.getElementById('tipo-servicio').value    = 'autoservicio';
}

function cerrarModal(id) {
    document.getElementById(id).classList.remove('activo');
}

async function agregarPrenda() {
    const nombre = document.getElementById('nombre-prenda').value.trim();
    const precio = parseFloat(document.getElementById('precio-prenda').value);

    if (!nombre || isNaN(precio)) { alert('Por favor complete todos los campos'); return; }

    try {
        const response = await fetch(urlAgregarPrenda, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ nombre, precio })
        });
        const data = await response.json();
        if (data.success) { cerrarModal('modal-prenda'); location.reload(); }
        else { alert(data.mensaje); }
    } catch { alert('Error de conexion'); }
}

async function agregarServicio() {
    const nombre = document.getElementById('nombre-servicio').value.trim();
    const precio = parseFloat(document.getElementById('precio-servicio').value);
    const tipo   = document.getElementById('tipo-servicio').value;

    if (!nombre || isNaN(precio)) { alert('Por favor complete todos los campos'); return; }

    try {
        const response = await fetch(urlAgregarServicio, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ nombre, precio, tipo })
        });
        const data = await response.json();
        if (data.success) { cerrarModal('modal-servicio'); location.reload(); }
        else { alert(data.mensaje); }
    } catch { alert('Error de conexion'); }
}

async function eliminarPrenda(id, nombre) {
    if (!confirm('Esta seguro de eliminar la prenda "' + nombre + '"?')) return;

    try {
        const response = await fetch(urlEliminarPrenda, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ id })
        });
        const data = await response.json();
        if (data.success) { location.reload(); }
        else { alert(data.mensaje); }
    } catch { alert('Error de conexion'); }
}

async function eliminarServicio(id, nombre) {
    if (!confirm('Esta seguro de eliminar el servicio "' + nombre + '"?')) return;

    try {
        const response = await fetch(urlEliminarServicio, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ id })
        });
        const data = await response.json();
        if (data.success) { location.reload(); }
        else { alert(data.mensaje); }
    } catch { alert('Error de conexion'); }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function (e) {
            if (e.target === this) this.classList.remove('activo');
        });
    });
});