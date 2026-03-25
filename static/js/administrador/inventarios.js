
function abrirModalNuevo() {
    document.getElementById('modalNuevo').classList.add('active');
}

function cerrarModalNuevo() {
    document.getElementById('modalNuevo').classList.remove('active');
}

function cargarDatosEditar(btn) {
    var url       = btn.getAttribute('data-url');
    var codigo    = btn.getAttribute('data-codigo');
    var nombre    = btn.getAttribute('data-nombre');
    var categoria = btn.getAttribute('data-categoria');
    var unidad    = btn.getAttribute('data-unidad');
    var stock     = btn.getAttribute('data-stock');
    var capacidad = btn.getAttribute('data-capacidad');
    var precio    = btn.getAttribute('data-precio');

    document.getElementById('formEditar').action       = url;
    document.getElementById('edit_codigo').value       = codigo;
    document.getElementById('edit_nombre').value       = nombre;
    document.getElementById('edit_categoria').value    = categoria;
    document.getElementById('edit_unidad').value       = unidad;
    document.getElementById('edit_stock').value        = stock.replace(',', '.');
    document.getElementById('edit_capacidad').value    = capacidad.replace(',', '.');
    document.getElementById('edit_precio').value       = precio.replace(',', '.');
    document.getElementById('modalEditar').classList.add('active');
}

function cerrarModalEditar() {
    document.getElementById('modalEditar').classList.remove('active');
}

document.addEventListener('DOMContentLoaded', function () {

    window.onclick = function (event) {
        if (event.target === document.getElementById('modalNuevo'))  cerrarModalNuevo();
        if (event.target === document.getElementById('modalEditar')) cerrarModalEditar();
    };
});