
function buscarVentas() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows       = document.querySelectorAll('#tablaVentas tr');
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    document.getElementById('registrosMostrados').textContent = visibleCount;
}

function exportarExcel() {
    const searchTerm = document.getElementById('searchInput').value;
    let url = urlExportarHistorialVentas;
    if (searchTerm) url += '?search=' + encodeURIComponent(searchTerm);
    window.location.href = url;
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('searchInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') buscarVentas();
    });
});