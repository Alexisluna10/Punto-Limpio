window.prendasAgregadas = [];
window.contadorFilas = 0;

window.servicioSeleccionado = {
  tipo: window.TIPO_SERVICIO,
  nombre: window.TIPO_SERVICIO_NOMBRE,
  precio: parseFloat(window.SERVICIO_PRECIO) || 0,
};

window.agregarPrenda = function () {
  const select = document.getElementById("select-prenda");
  const option = select.options[select.selectedIndex];
  const cantidad =
    parseInt(document.getElementById("input-cantidad").value) || 1;

  if (!option.value) {
    alert("⚠️ Por favor selecciona una prenda");
    return;
  }

  const prenda = {
    id: window.contadorFilas++,
    prendaId: option.value,
    nombre: option.dataset.nombre,
    precio: parseFloat(option.dataset.precio),
    peso: parseFloat(option.dataset.peso),
    cantidad: cantidad,
    pesoTotal: parseFloat(option.dataset.peso) * cantidad,
    subtotal: parseFloat(option.dataset.precio) * cantidad,
  };

  window.prendasAgregadas.push(prenda);
  renderizarTabla();
  calcularTotales();

  select.selectedIndex = 0;
  document.getElementById("input-cantidad").value = 1;
};

window.quitarPrenda = function (id) {
  window.prendasAgregadas = window.prendasAgregadas.filter((p) => p.id !== id);
  renderizarTabla();
  calcularTotales();
};

function renderizarTabla() {
  const tbody = document.getElementById("tabla-prendas-body");
  tbody.innerHTML = "";

  if (window.prendasAgregadas.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="texto-vacio">
          <div class="empty-table-state">
            <span class="empty-table-icon">📦</span>
            <p>No hay prendas agregadas</p>
            <small>Agrega prendas usando el formulario de arriba</small>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  let totalCantidad = 0;
  let totalPeso = 0;
  let totalPrecio = 0;

  window.prendasAgregadas.forEach((prenda, index) => {
    totalCantidad += prenda.cantidad;
    totalPeso += prenda.pesoTotal;
    totalPrecio += prenda.subtotal;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${prenda.nombre}</td>
      <td>${prenda.cantidad}</td>
      <td>${prenda.pesoTotal.toFixed(3)} KG</td>
      <td>$${prenda.subtotal.toFixed(2)}</td>
      <td>
        <button class="btn-eliminar-prenda" onclick="quitarPrenda(${prenda.id})">
          🗑️ Eliminar
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  const trTotal = document.createElement("tr");
  trTotal.innerHTML = `
    <td></td>
    <td><strong>TOTALES</strong></td>
    <td><strong>${totalCantidad}</strong></td>
    <td><strong>${totalPeso.toFixed(3)} KG</strong></td>
    <td><strong>$${totalPrecio.toFixed(2)}</strong></td>
    <td></td>
  `;
  tbody.appendChild(trTotal);
}

function calcularTotales() {
  let totalPrendas = 0;
  let totalPeso = 0;

  window.prendasAgregadas.forEach((prenda) => {
    totalPrendas += prenda.subtotal;
    totalPeso += prenda.pesoTotal;
  });

  const granTotal = totalPrendas + window.servicioSeleccionado.precio;

  document.getElementById("info-peso-total").textContent =
    totalPeso.toFixed(3) + " KG";
  document.getElementById("info-costo-prendas").textContent =
    "$" + totalPrendas.toFixed(2);
  document.getElementById("info-total").textContent =
    "$" + granTotal.toFixed(2);
  document.getElementById("gran-total").textContent = granTotal.toFixed(2);
}

window.continuarPago = function () {
  if (window.prendasAgregadas.length === 0) {
    alert("⚠️ Por favor agrega al menos una prenda");
    return;
  }

  const total = parseFloat(document.getElementById("gran-total").textContent);
  const pesoTotal = window.prendasAgregadas.reduce(
    (sum, p) => sum + p.pesoTotal,
    0
  );

  const prendasData = window.prendasAgregadas.map((p) => ({
    prenda_id: p.prendaId,
    nombre: p.nombre,
    cantidad: p.cantidad,
    peso: p.peso,
    peso_total: p.pesoTotal,
    precio: p.precio,
    subtotal: p.subtotal,
  }));

  fetch(window.SERVCOSTO_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": window.CSRF_TOKEN,
    },
    body: JSON.stringify({
      prendas: prendasData,
      peso_total: pesoTotal,
      total: total,
      tipo_servicio: window.servicioSeleccionado.tipo,
      metodo_pago: "efectivo",
    }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("info-folio").textContent = data.folio;
        alert("✅ Servicio registrado exitosamente\nFolio: " + data.folio);
        window.location.href = window.TERMINADO_URL;
      } else {
        alert("❌ Error: " + data.message);
      }
    })
    .catch(() => alert("❌ Error al procesar el servicio"));
};

document.addEventListener("DOMContentLoaded", calcularTotales);
