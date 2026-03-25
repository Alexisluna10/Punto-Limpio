
function calcularTotales() {
    const efectivo      = parseFloat(document.getElementById('efectivo_contado').value)  || 0;
    const tarjeta       = parseFloat(document.getElementById('tarjeta_terminal').value)  || 0;
    const transferencia = parseFloat(document.getElementById('transferencia_banco').value) || 0;

    const totalFisico = efectivo + tarjeta + transferencia;
    const diferencia  = totalFisico - ventasTotal;

    document.getElementById('total_fisico').textContent    = '$' + totalFisico.toFixed(2);
    document.getElementById('diferencia_valor').textContent = diferencia.toFixed(2);

    const diferenciaDisplay = document.getElementById('diferencia_display');
    diferenciaDisplay.classList.remove('positiva', 'negativa', 'cero');

    if (diferencia > 0) {
        diferenciaDisplay.classList.add('positiva');
    } else if (diferencia < 0) {
        diferenciaDisplay.classList.add('negativa');
    } else {
        diferenciaDisplay.classList.add('cero');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('corteCajaForm').addEventListener('submit', function (e) {
        const efectivo      = parseFloat(document.getElementById('efectivo_contado').value)  || 0;
        const tarjeta       = parseFloat(document.getElementById('tarjeta_terminal').value)  || 0;
        const transferencia = parseFloat(document.getElementById('transferencia_banco').value) || 0;

        if (efectivo < 0 || tarjeta < 0 || transferencia < 0) {
            e.preventDefault();
            alert('Los valores no pueden ser negativos');
            return false;
        }

        return confirm('Esta seguro de guardar este corte de caja?');
    });
});