
function filtrarMovimientos() {
    const filterUsuario = document.getElementById('filterUsuario').value.toLowerCase();
    const filterAccion  = document.getElementById('filterAccion').value.toLowerCase();
    const filterFecha   = document.getElementById('filterFecha').value;
    const rows          = document.querySelectorAll('#tablaMovimientos tr[data-usuario]');
    const now           = new Date();
    let visibleCount    = 0;

    rows.forEach(row => {
        const usuario  = row.getAttribute('data-usuario').toLowerCase();
        const accion   = row.getAttribute('data-accion').toLowerCase();
        const fechaStr = row.getAttribute('data-fecha');
        const fecha    = new Date(fechaStr);

        const showByUsuario = !filterUsuario || usuario.includes(filterUsuario);
        const showByAccion  = !filterAccion  || accion.includes(filterAccion);
        let showByFecha     = true;

        if (filterFecha) {
            const diffDays = Math.ceil(Math.abs(now - fecha) / (1000 * 60 * 60 * 24));
            if (filterFecha === '24h')      showByFecha = diffDays <= 1;
            else if (filterFecha === '7d')  showByFecha = diffDays <= 7;
            else if (filterFecha === '30d') showByFecha = diffDays <= 30;
        }

        if (showByUsuario && showByAccion && showByFecha) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    document.getElementById('registrosMostrados').textContent = visibleCount;
}

function exportarExcel() {
    const usuario = document.getElementById('filterUsuario').value;
    const accion  = document.getElementById('filterAccion').value;
    const fecha   = document.getElementById('filterFecha').value;

    let url = urlExportarHistorialMovimientos;
    const params = [];

    if (usuario) params.push('usuario=' + encodeURIComponent(usuario));
    if (accion)  params.push('accion='  + encodeURIComponent(accion));
    if (fecha)   params.push('fecha='   + encodeURIComponent(fecha));

    if (params.length > 0) url += '?' + params.join('&');
    window.location.href = url;
}

document.addEventListener('DOMContentLoaded', function () {
    filtrarMovimientos();
});