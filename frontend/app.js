const API = "http://localhost:5000/api";

let products = [];
let clients = [];
let catalogos = { categorias: [], proveedores: [] };

const $ = (id) => document.getElementById(id);

function toast(message, error = false) {
  const node = $("toast");
  node.textContent = message;
  node.className = `toast show${error ? " error" : ""}`;
  setTimeout(() => (node.className = "toast"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detalle || data.error || "Error inesperado");
  }
  return data;
}

function optionList(rows, idKey, labelKey) {
  return rows.map((row) => `<option value="${row[idKey]}">${row[labelKey]}</option>`).join("");
}

function money(value) {
  return `Q${Number(value).toFixed(2)}`;
}

async function loadCatalogos() {
  catalogos = await api("/catalogos");
  $("product-category").innerHTML = optionList(catalogos.categorias, "id_categoria", "nombre");
  $("product-provider").innerHTML = optionList(catalogos.proveedores, "id_proveedor", "nombre");
}

async function loadProducts() {
  products = await api("/productos");
  $("products-body").innerHTML = products
    .map(
      (p) => `
        <tr>
          <td>${p.id_producto}</td>
          <td>${p.nombre}<br><small>${p.sku}</small></td>
          <td>${p.categoria}</td>
          <td>${p.proveedor}</td>
          <td>${money(p.precio)}</td>
          <td>${p.stock}</td>
          <td class="actions">
            <button class="secondary" onclick="editProduct(${p.id_producto})">Editar</button>
            <button class="danger" onclick="deleteProduct(${p.id_producto})">Desactivar</button>
          </td>
        </tr>
      `
    )
    .join("");

  $("sale-product").innerHTML = products
    .filter((p) => p.activo && p.stock > 0)
    .map((p) => `<option value="${p.id_producto}">${p.nombre} - stock ${p.stock}</option>`)
    .join("");
}

async function loadClients() {
  clients = await api("/clientes");
  $("clients-body").innerHTML = clients
    .map(
      (c) => `
        <tr>
          <td>${c.id_cliente}</td>
          <td>${c.nombre}</td>
          <td>${c.nit}</td>
          <td>${c.telefono}</td>
          <td>${c.email}</td>
          <td class="actions">
            <button class="secondary" onclick="editClient(${c.id_cliente})">Editar</button>
            <button class="danger" onclick="deleteClient(${c.id_cliente})">Eliminar</button>
          </td>
        </tr>
      `
    )
    .join("");
  $("sale-client").innerHTML = optionList(clients, "id_cliente", "nombre");
}

function renderMiniList(id, rows, primary, secondary, amount) {
  const node = $(id);
  if (!rows.length) {
    node.innerHTML = '<p class="empty">Sin datos para mostrar.</p>';
    return;
  }
  node.innerHTML = `
    <div class="mini-list">
      ${rows
        .map(
          (row) => `
          <div class="mini-item">
            <div>
              <strong>${primary(row)}</strong>
              <span>${secondary(row)}</span>
            </div>
            <b>${amount(row)}</b>
          </div>
        `
        )
        .join("")}
    </div>
  `;
}

async function loadReports() {
  const [sales, top, frequent, stock, noSales] = await Promise.all([
    api("/reportes/resumen-ventas"),
    api("/reportes/productos-mas-vendidos"),
    api("/reportes/clientes-frecuentes"),
    api("/reportes/stock-critico"),
    api("/reportes/productos-sin-ventas"),
  ]);

  renderMiniList(
    "report-sales",
    sales,
    (r) => `Venta #${r.id_venta} - ${r.cliente}`,
    (r) => `${r.empleado} | ${r.unidades_vendidas} unidades`,
    (r) => money(r.total)
  );
  renderMiniList(
    "report-top",
    top,
    (r) => r.nombre,
    (r) => r.categoria,
    (r) => `${r.unidades} uds`
  );
  renderMiniList(
    "report-clients",
    frequent,
    (r) => r.nombre,
    (r) => `${r.compras} compras | ${r.nit}`,
    (r) => money(r.total_comprado)
  );
  renderMiniList(
    "report-stock",
    stock,
    (r) => r.nombre,
    (r) => `${r.sku} | ${r.categoria}`,
    (r) => `${r.stock} uds`
  );
  renderMiniList(
    "report-no-sales",
    noSales,
    (r) => r.nombre,
    (r) => r.sku,
    (r) => `${r.stock} uds`
  );
}

function clearProduct() {
  $("product-id").value = "";
  $("product-form").reset();
}

function editProduct(id) {
  const p = products.find((item) => item.id_producto === id);
  $("product-id").value = p.id_producto;
  $("product-name").value = p.nombre;
  $("product-sku").value = p.sku;
  $("product-price").value = p.precio;
  $("product-cost").value = p.costo;
  $("product-stock").value = p.stock;
  $("product-category").value = p.id_categoria;
  $("product-provider").value = p.id_proveedor;
}

async function deleteProduct(id) {
  await api(`/productos/${id}`, { method: "DELETE" });
  toast("Producto desactivado");
  await refresh();
}

function clearClient() {
  $("client-id").value = "";
  $("client-form").reset();
}

function editClient(id) {
  const c = clients.find((item) => item.id_cliente === id);
  $("client-id").value = c.id_cliente;
  $("client-name").value = c.nombre;
  $("client-nit").value = c.nit;
  $("client-phone").value = c.telefono;
  $("client-email").value = c.email;
}

async function deleteClient(id) {
  try {
    await api(`/clientes/${id}`, { method: "DELETE" });
    toast("Cliente eliminado");
    await refresh();
  } catch (error) {
    toast(error.message, true);
  }
}

async function saveProduct(event) {
  event.preventDefault();
  const id = $("product-id").value;
  const body = {
    nombre: $("product-name").value,
    sku: $("product-sku").value,
    precio: Number($("product-price").value),
    costo: Number($("product-cost").value),
    stock: Number($("product-stock").value),
    id_categoria: Number($("product-category").value),
    id_proveedor: Number($("product-provider").value),
    activo: true,
  };
  await api(id ? `/productos/${id}` : "/productos", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(body),
  });
  clearProduct();
  toast("Producto guardado");
  await refresh();
}

async function saveClient(event) {
  event.preventDefault();
  const id = $("client-id").value;
  const body = {
    nombre: $("client-name").value,
    nit: $("client-nit").value,
    telefono: $("client-phone").value,
    email: $("client-email").value,
  };
  await api(id ? `/clientes/${id}` : "/clientes", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(body),
  });
  clearClient();
  toast("Cliente guardado");
  await refresh();
}

async function saveSale(event) {
  event.preventDefault();
  try {
    await api("/ventas", {
      method: "POST",
      body: JSON.stringify({
        id_cliente: Number($("sale-client").value),
        id_empleado: Number($("sale-employee").value),
        detalles: [
          {
            id_producto: Number($("sale-product").value),
            cantidad: Number($("sale-qty").value),
          },
        ],
      }),
    });
    toast("Venta registrada con transaccion");
    await refresh();
  } catch (error) {
    toast(error.message, true);
  }
}

async function refresh() {
  await Promise.all([loadProducts(), loadClients()]);
  await loadReports();
}

async function init() {
  try {
    await loadCatalogos();
    await refresh();
    $("product-form").addEventListener("submit", saveProduct);
    $("client-form").addEventListener("submit", saveClient);
    $("sale-form").addEventListener("submit", saveSale);
    $("clear-product").addEventListener("click", clearProduct);
    $("clear-client").addEventListener("click", clearClient);
  } catch (error) {
    toast(`No se pudo conectar con el backend: ${error.message}`, true);
  }
}

init();
