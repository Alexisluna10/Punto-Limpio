
const coloresPie = [
    '#2d3748', '#4a5568', '#718096', '#a0aec0', '#cbd5e0', '#e2e8f0',
    '#1a202c', '#2c5282', '#2b6cb0', '#3182ce'
];

const coloresBar = [
    '#28a745', '#20c997', '#17a2b8', '#007bff', '#6610f2', '#6f42c1'
];

const coloresGastos = ['#dc3545', '#fd7e14', '#ffc107', '#28a745'];

function formatCurrency(value) {
    return '$' + value.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function cambiarTab(tab) {
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById('tab-' + tab).classList.add('active');
    event.target.classList.add('active');

    const url = new URL(window.location);
    url.searchParams.set('tab', tab);
    window.history.pushState({}, '', url);

    tabActiva = tab;

    setTimeout(() => { inicializarGraficas(); }, 100);
}

function inicializarGraficas() {
    Chart.helpers.each(Chart.instances, function (instance) {
        instance.destroy();
    });

    const chartPrendasEl = document.getElementById('chartPrendas');
    if (chartPrendasEl && prendasData.length > 0) {
        new Chart(chartPrendasEl, {
            type: 'pie',
            data: {
                labels: prendasData.map(p => p.nombre + ' ' + p.porcentaje + '%'),
                datasets: [{ data: prendasData.map(p => p.cantidad), backgroundColor: coloresPie.slice(0, prendasData.length) }]
            },
            options: { responsive: true, plugins: { legend: { position: 'right', labels: { font: { size: 11 } } } } }
        });
    } else if (chartPrendasEl) {
        chartPrendasEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartGananciasPrendasEl = document.getElementById('chartGananciasPrendas');
    if (chartGananciasPrendasEl && prendasData.length > 0) {
        new Chart(chartGananciasPrendasEl, {
            type: 'bar',
            data: {
                labels: prendasData.map(p => p.nombre),
                datasets: [{ label: 'Ganancias', data: prendasData.map(p => p.ganancia), backgroundColor: '#28a745' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => formatCurrency(ctx.raw) } } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartGananciasPrendasEl) {
        chartGananciasPrendasEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartServiciosEl = document.getElementById('chartServicios');
    if (chartServiciosEl && serviciosData.length > 0) {
        new Chart(chartServiciosEl, {
            type: 'pie',
            data: {
                labels: serviciosData.map(s => s.nombre + ' ' + s.porcentaje + '%'),
                datasets: [{ data: serviciosData.map(s => s.cantidad), backgroundColor: coloresPie.slice(0, serviciosData.length) }]
            },
            options: { responsive: true, plugins: { legend: { position: 'right', labels: { font: { size: 11 } } } } }
        });
    } else if (chartServiciosEl) {
        chartServiciosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartGananciasServiciosEl = document.getElementById('chartGananciasServicios');
    if (chartGananciasServiciosEl && serviciosData.length > 0) {
        new Chart(chartGananciasServiciosEl, {
            type: 'bar',
            data: {
                labels: serviciosData.map(s => s.nombre),
                datasets: [{ label: 'Ganancias', data: serviciosData.map(s => s.ganancia), backgroundColor: '#17a2b8' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => formatCurrency(ctx.raw) } } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartGananciasServiciosEl) {
        chartGananciasServiciosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartMetodosPagoEl = document.getElementById('chartMetodosPago');
    if (chartMetodosPagoEl && metodosPagoData.some(m => m.total > 0)) {
        new Chart(chartMetodosPagoEl, {
            type: 'doughnut',
            data: {
                labels: metodosPagoData.map(m => m.nombre + ' ' + m.porcentaje + '%'),
                datasets: [{ data: metodosPagoData.map(m => m.total), backgroundColor: ['#28a745', '#007bff', '#ffc107'] }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { font: { size: 11 } } },
                    tooltip: { callbacks: { label: ctx => formatCurrency(ctx.raw) } }
                }
            }
        });
    } else if (chartMetodosPagoEl) {
        chartMetodosPagoEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartResumenPrendasEl = document.getElementById('chartResumenPrendas');
    if (chartResumenPrendasEl && prendasData.length > 0) {
        new Chart(chartResumenPrendasEl, {
            type: 'bar',
            data: {
                labels: prendasData.map(p => p.nombre),
                datasets: [{ label: 'Ganancias', data: prendasData.map(p => p.ganancia), backgroundColor: '#28a745' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartResumenPrendasEl) {
        chartResumenPrendasEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartResumenServiciosEl = document.getElementById('chartResumenServicios');
    if (chartResumenServiciosEl && serviciosData.length > 0) {
        new Chart(chartResumenServiciosEl, {
            type: 'bar',
            data: {
                labels: serviciosData.map(s => s.nombre),
                datasets: [{ label: 'Ganancias', data: serviciosData.map(s => s.ganancia), backgroundColor: '#17a2b8' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartResumenServiciosEl) {
        chartResumenServiciosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartGastosSueldosEl = document.getElementById('chartGastosSueldos');
    if (chartGastosSueldosEl && sueldosData.length > 0) {
        new Chart(chartGastosSueldosEl, {
            type: 'bar',
            data: {
                labels: sueldosData.map(s => s.nombre),
                datasets: [{ label: 'Sueldo Semanal', data: sueldosData.map(s => s.sueldo_semanal), backgroundColor: '#dc3545' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartGastosSueldosEl) {
        chartGastosSueldosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartGastosServiciosEl = document.getElementById('chartGastosServicios');
    if (chartGastosServiciosEl && gastosData.servicios && gastosData.servicios.length > 0) {
        new Chart(chartGastosServiciosEl, {
            type: 'pie',
            data: {
                labels: gastosData.servicios.map(s => s.tipo),
                datasets: [{ data: gastosData.servicios.map(s => s.monto), backgroundColor: coloresGastos }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { font: { size: 11 } } },
                    tooltip: { callbacks: { label: ctx => formatCurrency(ctx.raw) } }
                }
            }
        });
    } else if (chartGastosServiciosEl) {
        chartGastosServiciosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }

    const chartDistribucionGastosEl = document.getElementById('chartDistribucionGastos');
    if (chartDistribucionGastosEl) {
        if (totalRentaMes > 0 || totalServiciosMes > 0 || totalSueldosMes > 0) {
            new Chart(chartDistribucionGastosEl, {
                type: 'doughnut',
                data: {
                    labels: ['Renta', 'Servicios', 'Sueldos'],
                    datasets: [{ data: [totalRentaMes, totalServiciosMes, totalSueldosMes], backgroundColor: ['#dc3545', '#fd7e14', '#ffc107'] }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right', labels: { font: { size: 11 } } },
                        tooltip: { callbacks: { label: ctx => formatCurrency(ctx.raw) } }
                    }
                }
            });
        } else {
            chartDistribucionGastosEl.parentElement.innerHTML = '<p class="sin-datos">Sin gastos registrados</p>';
        }
    }

    const chartSueldosEmpleadosEl = document.getElementById('chartSueldosEmpleados');
    if (chartSueldosEmpleadosEl && sueldosData.length > 0) {
        new Chart(chartSueldosEmpleadosEl, {
            type: 'bar',
            data: {
                labels: sueldosData.map(s => s.nombre),
                datasets: [{ label: 'Sueldo Semanal', data: sueldosData.map(s => s.sueldo_semanal), backgroundColor: '#ffc107' }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: value => formatCurrency(value) } } }
            }
        });
    } else if (chartSueldosEmpleadosEl) {
        chartSueldosEmpleadosEl.parentElement.innerHTML = '<p class="sin-datos">Sin datos para mostrar</p>';
    }
}

function exportarExcel() {
    const urlParams  = new URLSearchParams(window.location.search);
    const filtro     = urlParams.get('filtro')     || 'hoy';
    const fechaDesde = urlParams.get('fecha_desde') || '';
    const fechaHasta = urlParams.get('fecha_hasta') || '';
    const tab        = urlParams.get('tab')         || tabActiva || 'resumen';

    let url = urlExportarExcel + '?filtro=' + filtro + '&tab=' + tab;
    if (filtro === 'personalizado' && fechaDesde && fechaHasta) {
        url += '&fecha_desde=' + fechaDesde + '&fecha_hasta=' + fechaHasta;
    }
    window.location.href = url;
}

function imprimirReporte() {
    const urlParams  = new URLSearchParams(window.location.search);
    const filtro     = urlParams.get('filtro')     || 'hoy';
    const fechaDesde = urlParams.get('fecha_desde') || '';
    const fechaHasta = urlParams.get('fecha_hasta') || '';
    const tab        = urlParams.get('tab')         || tabActiva || 'resumen';

    let url = urlImprimirReporte + '?filtro=' + filtro + '&tab=' + tab;
    if (filtro === 'personalizado' && fechaDesde && fechaHasta) {
        url += '&fecha_desde=' + fechaDesde + '&fecha_hasta=' + fechaHasta;
    }
    window.open(url, '_blank');
}

function abrirModalEmail() {
    document.getElementById('modalEmail').style.display = 'block';
    document.getElementById('emailDestino').value = '';
    document.getElementById('mensajeEmail').style.display = 'none';
}

function cerrarModalEmail() {
    document.getElementById('modalEmail').style.display = 'none';
}

async function enviarPorEmail(event) {
    event.preventDefault();

    const emailDestino = document.getElementById('emailDestino').value;
    const btnEnviar    = event.target.querySelector('.btn-enviar');
    const mensajeDiv   = document.getElementById('mensajeEmail');

    btnEnviar.disabled = true;
    btnEnviar.textContent = 'Enviando...';
    mensajeDiv.style.display = 'none';

    const urlParams  = new URLSearchParams(window.location.search);
    const filtro     = urlParams.get('filtro')     || 'hoy';
    const fechaDesde = urlParams.get('fecha_desde') || '';
    const fechaHasta = urlParams.get('fecha_hasta') || '';
    const tab        = urlParams.get('tab')         || tabActiva || 'resumen';

    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch(urlEnviarReporteEmail, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify({ email: emailDestino, filtro, fecha_desde: fechaDesde, fecha_hasta: fechaHasta, tab })
        });

        const data = await response.json();

        if (data.success) {
            mensajeDiv.className = 'mensaje-email success';
            mensajeDiv.textContent = 'Reporte enviado exitosamente a ' + emailDestino;
            mensajeDiv.style.display = 'block';
            setTimeout(() => { cerrarModalEmail(); }, 2000);
        } else {
            mensajeDiv.className = 'mensaje-email error';
            mensajeDiv.textContent = 'Error: ' + (data.message || 'No se pudo enviar el reporte');
            mensajeDiv.style.display = 'block';
        }
    } catch (error) {
        mensajeDiv.className = 'mensaje-email error';
        mensajeDiv.textContent = 'Error de conexion. Por favor, intente nuevamente.';
        mensajeDiv.style.display = 'block';
    } finally {
        btnEnviar.disabled = false;
        btnEnviar.textContent = 'Enviar Reporte';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    inicializarGraficas();

    document.getElementById('btn-personalizado').addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById('form-personalizado').style.display = 'flex';
        document.querySelectorAll('.filtros-rapidos a').forEach(a => a.classList.remove('active'));
        this.classList.add('active');
    });

    window.onclick = function (event) {
        const modal = document.getElementById('modalEmail');
        if (event.target === modal) { cerrarModalEmail(); }
    };
});