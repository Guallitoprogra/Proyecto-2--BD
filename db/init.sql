DROP VIEW IF EXISTS vw_resumen_ventas;
DROP TABLE IF EXISTS detalle_venta;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS empleados;
DROP TABLE IF EXISTS proveedores;
DROP TABLE IF EXISTS categorias;

CREATE TABLE categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL
);

CREATE TABLE proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    telefono VARCHAR(25) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    ciudad VARCHAR(80) NOT NULL
);

CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    nit VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(25) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE empleados (
    id_empleado SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    puesto VARCHAR(80) NOT NULL,
    fecha_contratacion DATE NOT NULL
);

CREATE TABLE productos (
    id_producto SERIAL PRIMARY KEY,
    id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
    id_proveedor INTEGER NOT NULL REFERENCES proveedores(id_proveedor),
    nombre VARCHAR(120) NOT NULL,
    sku VARCHAR(40) NOT NULL UNIQUE,
    precio NUMERIC(10,2) NOT NULL CHECK (precio > 0),
    costo NUMERIC(10,2) NOT NULL CHECK (costo > 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE ventas (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
    id_empleado INTEGER NOT NULL REFERENCES empleados(id_empleado),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    estado VARCHAR(20) NOT NULL DEFAULT 'PAGADA'
);

CREATE TABLE detalle_venta (
    id_detalle SERIAL PRIMARY KEY,
    id_venta INTEGER NOT NULL REFERENCES ventas(id_venta) ON DELETE CASCADE,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario > 0),
    subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0)
);

CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_detalle_producto ON detalle_venta(id_producto);

CREATE VIEW vw_resumen_ventas AS
SELECT
    v.id_venta,
    v.fecha,
    c.nombre AS cliente,
    e.nombre AS empleado,
    v.total,
    COUNT(d.id_detalle) AS productos_distintos,
    SUM(d.cantidad) AS unidades_vendidas
FROM ventas v
JOIN clientes c ON c.id_cliente = v.id_cliente
JOIN empleados e ON e.id_empleado = v.id_empleado
JOIN detalle_venta d ON d.id_venta = v.id_venta
GROUP BY v.id_venta, v.fecha, c.nombre, e.nombre, v.total;

INSERT INTO categorias (nombre, descripcion)
SELECT 'Categoria ' || n, 'Linea de productos para area ' || n
FROM generate_series(1, 25) AS n;

INSERT INTO proveedores (nombre, telefono, email, ciudad)
SELECT
    'Proveedor ' || n,
    '5555-' || LPAD(n::text, 4, '0'),
    'proveedor' || n || '@tienda.test',
    CASE WHEN n % 4 = 0 THEN 'Guatemala'
         WHEN n % 4 = 1 THEN 'Mixco'
         WHEN n % 4 = 2 THEN 'Villa Nueva'
         ELSE 'Antigua Guatemala' END
FROM generate_series(1, 25) AS n;

INSERT INTO clientes (nombre, nit, telefono, email)
SELECT
    'Cliente ' || n,
    'CF-' || LPAD(n::text, 5, '0'),
    '4000-' || LPAD(n::text, 4, '0'),
    'cliente' || n || '@correo.test'
FROM generate_series(1, 25) AS n;

INSERT INTO empleados (nombre, puesto, fecha_contratacion)
SELECT
    'Empleado ' || n,
    CASE WHEN n % 3 = 0 THEN 'Cajero'
         WHEN n % 3 = 1 THEN 'Vendedor'
         ELSE 'Supervisor' END,
    DATE '2025-01-01' + (n * INTERVAL '7 days')
FROM generate_series(1, 25) AS n;

INSERT INTO productos (id_categoria, id_proveedor, nombre, sku, precio, costo, stock, activo)
SELECT
    ((n - 1) % 25) + 1,
    ((n - 1) % 25) + 1,
    CASE WHEN n % 5 = 0 THEN 'Audifonos modelo ' || n
         WHEN n % 5 = 1 THEN 'Teclado mecanico ' || n
         WHEN n % 5 = 2 THEN 'Mouse inalambrico ' || n
         WHEN n % 5 = 3 THEN 'Monitor LED ' || n
         ELSE 'Memoria USB ' || n END,
    'SKU-' || LPAD(n::text, 4, '0'),
    (35 + n * 4.75)::NUMERIC(10,2),
    (20 + n * 2.30)::NUMERIC(10,2),
    30 + (n % 20),
    TRUE
FROM generate_series(1, 30) AS n;

INSERT INTO ventas (id_cliente, id_empleado, fecha, total, estado)
SELECT
    ((n - 1) % 25) + 1,
    ((n + 4) % 25) + 1,
    TIMESTAMP '2026-03-01 09:00:00' + (n * INTERVAL '1 day'),
    0,
    'PAGADA'
FROM generate_series(1, 25) AS n;

INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal)
SELECT
    v.id_venta,
    ((v.id_venta + x.n - 2) % 30) + 1 AS id_producto,
    x.n AS cantidad,
    p.precio,
    x.n * p.precio
FROM ventas v
CROSS JOIN generate_series(1, 3) AS x(n)
JOIN productos p ON p.id_producto = ((v.id_venta + x.n - 2) % 30) + 1;

UPDATE ventas v
SET total = resumen.total
FROM (
    SELECT id_venta, SUM(subtotal) AS total
    FROM detalle_venta
    GROUP BY id_venta
) resumen
WHERE resumen.id_venta = v.id_venta;

UPDATE productos p
SET stock = stock - vendido.unidades
FROM (
    SELECT id_producto, SUM(cantidad) AS unidades
    FROM detalle_venta
    GROUP BY id_producto
) vendido
WHERE vendido.id_producto = p.id_producto;
