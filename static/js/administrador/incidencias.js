
let dudaActualId = null;

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

function abrirModal(dudaId, cliente, comentario, respuesta, estado) {
    dudaActualId = dudaId;

    document.getElementById('modalCliente').textContent = `- ${cliente}`;
    document.getElementById('modalComentarioTexto').textContent = comentario;
    document.getElementById('modalDudaId').value = dudaId;

    if (respuesta && respuesta.trim()) {
        document.getElementById('respuestaAnterior').style.display = 'block';
        document.getElementById('respuestaTexto').textContent = respuesta;
    } else {
        document.getElementById('respuestaAnterior').style.display = 'none';
    }

    document.getElementById('modalRespuesta').value = '';

    const resolverBtn = document.querySelector('.btn-resolver');
    if (estado === 'resuelto') {
        document.getElementById('modalRespuesta').disabled = true;
        resolverBtn.disabled = true;
        resolverBtn.textContent = 'Ya Resuelto';
    } else {
        document.getElementById('modalRespuesta').disabled = false;
        resolverBtn.disabled = false;
        resolverBtn.textContent = 'Resolver';
    }

    document.getElementById('modalOverlay').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.getElementById('modalRespuesta').value = '';
    dudaActualId = null;
}

function resolverDuda() {
    const respuesta = document.getElementById('modalRespuesta').value;
    const dudaId    = document.getElementById('modalDudaId').value;

    if (!respuesta.trim()) {
        alert('Por favor escribe una respuesta antes de resolver.');
        return;
    }

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    const formData  = new FormData();
    formData.append('tipo',                  'duda');
    formData.append('duda_id',               dudaId);
    formData.append('respuesta',             respuesta);
    formData.append('accion',                'resolver');
    formData.append('csrfmiddlewaretoken',   csrftoken);

    const btn = document.querySelector('.btn-resolver');
    btn.disabled     = true;
    btn.textContent  = 'Resolviendo...';

    fetch(urlAdminIncidencias, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);

            const fila  = document.querySelector(`tr[data-id="${dudaId}"]`);
            if (fila) {
                const badge = fila.querySelector('.badge');
                if (badge) {
                    badge.classList.remove('badge-pendiente', 'badge-en_proceso');
                    badge.classList.add('badge-resuelto');
                    badge.textContent = 'Resuelto';
                }
                fila.classList.add('fila-resuelta');
            }
            cerrarModal();
        } else {
            alert('Error: ' + data.message);
            btn.disabled    = false;
            btn.textContent = 'Resolver';
        }
    })
    .catch(error => {
        alert('Error al resolver la duda/queja. Por favor intenta de nuevo.');
        console.error('Error:', error);
        btn.disabled    = false;
        btn.textContent = 'Resolver';
    });
}

function abrirModalIncidencia(incidenciaId, trabajador, asunto, descripcion, prioridad, respuesta, estado, evidenciaUrl) {
    document.getElementById('modalIncidenciaTrabajador').textContent = `- ${trabajador}`;
    document.getElementById('modalIncidenciaAsunto').textContent      = asunto;
    document.getElementById('modalIncidenciaDescripcion').textContent = descripcion;
    document.getElementById('modalIncidenciaId').value                = incidenciaId;

    const prioridadBadge = document.getElementById('modalIncidenciaPrioridad');
    prioridadBadge.className = 'badge badge-prioridad-' + prioridad;
    const prioridadTextos = { baja: 'Baja', media: 'Media', alta: 'Alta', urgente: 'Urgente' };
    prioridadBadge.textContent = prioridadTextos[prioridad] || prioridad;

    const evidenciaContainer = document.getElementById('modalIncidenciaEvidenciaContainer');
    const evidenciaLink      = document.getElementById('modalIncidenciaEvidenciaLink');
    const imagenPreview      = document.getElementById('modalIncidenciaImagenPreview');
    const imagen             = document.getElementById('modalIncidenciaImagen');

    if (evidenciaUrl && evidenciaUrl.trim() !== '') {
        evidenciaContainer.style.display = 'block';
        evidenciaLink.href = evidenciaUrl;

        const extensionesImagen = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];
        const esImagen = extensionesImagen.some(ext => evidenciaUrl.toLowerCase().endsWith(ext));

        if (esImagen) {
            imagenPreview.style.display = 'block';
            imagen.src = evidenciaUrl;
        } else {
            imagenPreview.style.display = 'none';
        }
    } else {
        evidenciaContainer.style.display = 'none';
        imagenPreview.style.display      = 'none';
    }

    if (respuesta && respuesta.trim()) {
        document.getElementById('incidenciaRespuestaAnterior').style.display = 'block';
        document.getElementById('incidenciaRespuestaTexto').textContent        = respuesta;
    } else {
        document.getElementById('incidenciaRespuestaAnterior').style.display = 'none';
    }

    document.getElementById('modalIncidenciaRespuesta').value = '';

    const resolverBtn = document.querySelector('#modalIncidenciaOverlay .btn-resolver');
    if (estado === 'resuelto') {
        document.getElementById('modalIncidenciaRespuesta').disabled = true;
        resolverBtn.disabled    = true;
        resolverBtn.textContent = 'Ya Resuelto';
    } else {
        document.getElementById('modalIncidenciaRespuesta').disabled = false;
        resolverBtn.disabled    = false;
        resolverBtn.textContent = 'Resolver';
    }

    document.getElementById('modalIncidenciaOverlay').classList.add('active');
}

function cerrarModalIncidencia() {
    document.getElementById('modalIncidenciaOverlay').classList.remove('active');
    document.getElementById('modalIncidenciaRespuesta').value = '';
}

function resolverIncidencia() {
    const respuesta    = document.getElementById('modalIncidenciaRespuesta').value;
    const incidenciaId = document.getElementById('modalIncidenciaId').value;

    if (!respuesta.trim()) {
        alert('Por favor escribe una respuesta antes de resolver.');
        return;
    }

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    const formData  = new FormData();
    formData.append('incidencia_id',         incidenciaId);
    formData.append('respuesta',             respuesta);
    formData.append('accion',                'resolver');
    formData.append('tipo',                  'incidencia');
    formData.append('csrfmiddlewaretoken',   csrftoken);

    const btn = document.querySelector('#modalIncidenciaOverlay .btn-resolver');
    btn.disabled    = true;
    btn.textContent = 'Resolviendo...';

    fetch(urlAdminIncidencias, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);

            const fila = document.querySelector(`tr[data-id="${incidenciaId}"][data-tipo="incidencia"]`);
            if (fila) {
                const badge = fila.querySelector('.badge:not(.badge-prioridad-baja):not(.badge-prioridad-media):not(.badge-prioridad-alta):not(.badge-prioridad-urgente)');
                if (badge) {
                    badge.classList.remove('badge-pendiente', 'badge-en_proceso');
                    badge.classList.add('badge-resuelto');
                    badge.textContent = 'Resuelto';
                }
                fila.classList.add('fila-resuelta');
            }
            cerrarModalIncidencia();
        } else {
            alert('Error: ' + data.message);
            btn.disabled    = false;
            btn.textContent = 'Resolver';
        }
    })
    .catch(error => {
        alert('Error al resolver la incidencia. Por favor intenta de nuevo.');
        console.error('Error:', error);
        btn.disabled    = false;
        btn.textContent = 'Resolver';
    });
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('modalOverlay').addEventListener('click', function (e) {
        if (e.target === this) cerrarModal();
    });

    document.getElementById('modalIncidenciaOverlay').addEventListener('click', function (e) {
        if (e.target === this) cerrarModalIncidencia();
    });
});