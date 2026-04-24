# Guion para presentar el avance del 60%

1. El proyecto es una aplicacion web para una tienda que controla productos, clientes, ventas e inventario.
2. La infraestructura ya levanta con `docker compose up --build`: PostgreSQL, Flask y frontend con Nginx.
3. La base de datos ya tiene el modelo principal: categorias, proveedores, productos, clientes, empleados, ventas y detalle de venta.
4. El diseno esta normalizado hasta 3FN para evitar duplicar datos como nombres de clientes, categorias o proveedores.
5. La interfaz permite hacer CRUD de productos y clientes.
6. Al registrar una venta, el backend abre una transaccion, valida stock, guarda el detalle, actualiza el total y descuenta inventario.
7. Si algo falla durante la venta, se ejecuta `ROLLBACK` y no queda informacion incompleta.
8. Los reportes visibles demuestran consultas SQL avanzadas: joins, subqueries, agregaciones, CTE y vista.
9. Tambien se agrego exportacion CSV del resumen de ventas como funcionalidad avanzada inicial.

## Pendiente para completar el 100%

- Mejorar autenticacion con login/logout.
- Agregar mas filtros en reportes.
- Agregar pruebas automatizadas o evidencia de pruebas manuales.
- Pulir validaciones visuales y pantallas de detalle.
- Crear una presentacion final con capturas.
