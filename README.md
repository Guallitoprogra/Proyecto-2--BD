# Proyecto 2 - Inventario y ventas de tienda

Aplicacion web para gestionar productos, clientes, ventas e inventario de una tienda. El proyecto usa frontend, backend Flask, PostgreSQL y Docker Compose.

## Estado del proyecto

Proyecto preparado para entrega final:

- Docker Compose levanta base de datos, backend y frontend.
- Base de datos relacional con llaves primarias, foraneas, restricciones `NOT NULL`, indices y una vista.
- Datos de prueba generados al iniciar PostgreSQL con al menos 25 registros por tabla.
- CRUD completo de productos y clientes desde la interfaz.
- Registro de ventas con transaccion explicita: `BEGIN`, `COMMIT` y `ROLLBACK`.
- Reportes visibles en la UI con `JOIN`, `GROUP BY`, `HAVING`, subqueries, `CTE` y `VIEW`.
- Autenticacion con login/logout y sesion.
- Exportacion CSV del reporte de ventas.

## Requisitos

- Docker Desktop
- Git

## Como levantar el proyecto

1. Copiar variables de entorno si fuera necesario:

```bash
cp .env.example .env
```

2. Levantar todo el proyecto:

```bash
docker compose up --build
```

3. Abrir la aplicacion:

- Frontend: http://localhost:8080
- Backend health check: http://localhost:5000/api/health

4. Iniciar sesion en la aplicacion:

- Usuario: `admin`
- Password: `admin123`

Las credenciales obligatorias para calificacion ya estan configuradas:

- Usuario: `proy2`
- Password: `secret`
- Base de datos: `tienda_db`

## Estructura

```text
Proyecto-2--BD/
  backend/        API Flask con SQL explicito
  db/             DDL, indices, vista y datos de prueba
  docs/           Diseno de base de datos y normalizacion
  frontend/       Interfaz HTML/CSS/JS
  docker-compose.yml
  .env.example
```

## Funcionalidades

- Productos: crear, listar, editar y desactivar.
- Clientes: crear, listar, editar y eliminar cuando no tienen ventas asociadas.
- Ventas: registra una venta y descuenta stock dentro de una transaccion.
- Autenticacion: login/logout con sesion de usuario.
- Reportes:
  - Resumen de ventas desde `vw_resumen_ventas`.
  - Productos mas vendidos con agregaciones.
  - Clientes frecuentes con subquery.
  - Stock critico con `WITH`.
  - Productos sin ventas con `NOT EXISTS`.

## Documentacion

Ver [docs/diseno_base_datos.md](docs/diseno_base_datos.md) para el modelo relacional, diagrama ER en Mermaid y justificacion de normalizacion.

## Checklist de rubrica

- Diseno BD: diagrama ER, modelo relacional, normalizacion, DDL, datos e indices.
- SQL: joins, subqueries, agregaciones, CTE, view y transaccion explicita visibles desde la app.
- Aplicacion web: CRUD de 2 entidades, reportes, errores visibles y README funcional.
- Avanzado: autenticacion con sesion y exportacion CSV.
