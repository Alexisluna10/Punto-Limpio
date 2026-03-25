window.servicioSeleccionado = null;

window.seleccionarOpcion = function (elemento) {
  const id = elemento.getAttribute('data-servicio-id');
  const nombre = elemento.getAttribute('data-servicio-nombre');
  const precio = parseFloat(elemento.getAttribute('data-servicio-precio'));

  document.querySelectorAll('.servicio-card-auto').forEach(card => {
    card.classList.remove('selected');
  });

  elemento.classList.add('selected');

  window.servicioSeleccionado = { id, nombre, precio };

  document.getElementById('folio-valor').textContent = 'Pendiente...';
  document.getElementById('servicio-valor').textContent = nombre;
  document.getElementById('total-pagar').textContent = precio.toFixed(2);

  const nombreLower = nombre.toLowerCase();

  if (nombreLower.includes('lavadora') || nombreLower.includes('lavado')) {
    document.getElementById('num-lavadora').textContent = 'Lavadora 0' + Math.floor(1 + Math.random() * 9);
    document.getElementById('tiempo-uso').textContent = '30 minutos';
    document.getElementById('tipo-prenda').textContent = 'Ropa general';
  } else if (nombreLower.includes('secadora') || nombreLower.includes('secado')) {
    document.getElementById('num-lavadora').textContent = 'Secadora 0' + Math.floor(1 + Math.random() * 9);
    document.getElementById('tiempo-uso').textContent = '25 minutos';
    document.getElementById('tipo-prenda').textContent = 'Ropa general';
  } else if (nombreLower.includes('combo')) {
    const numLav = Math.floor(1 + Math.random() * 9);
    const numSec = Math.floor(1 + Math.random() * 9);
    document.getElementById('num-lavadora').textContent = `Lavadora 0${numLav} + Secadora 0${numSec}`;
    document.getElementById('tiempo-uso').textContent = '55 minutos';
    document.getElementById('tipo-prenda').textContent = 'Ropa general';
  } else {
    document.getElementById('num-lavadora').textContent = 'Por asignar';
    document.getElementById('tiempo-uso').textContent = '30 min. aprox.';
    document.getElementById('tipo-prenda').textContent = 'Ropa general';
  }
};

window.pagar = function () {
  if (!window.servicioSeleccionado) {
    alert('⚠️ Por favor selecciona un servicio primero');
    return;
  }

  fetch(window.AUTOSERVICIO_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.CSRF_TOKEN
    },
    body: JSON.stringify({
      servicio_id: window.servicioSeleccionado.id || null,
      servicio_nombre: window.servicioSeleccionado.nombre,
      total: window.servicioSeleccionado.precio,
      metodo_pago: 'efectivo'
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      document.getElementById('folio-valor').textContent = data.folio;
      alert('✅ Servicio registrado exitosamente\nFolio: ' + data.folio);
      window.location.href = window.TERMINADO_URL;
    } else {
      alert('❌ Error: ' + data.message);
    }
  })
  .catch(() => alert('❌ Error al procesar el pago'));
};