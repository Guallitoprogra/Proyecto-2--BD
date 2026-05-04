import csv
import hashlib
import io
import os
from decimal import Decimal
from functools import wraps

import psycopg
from flask import Flask, Response, jsonify, request, session
from flask_cors import CORS


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
CORS(app, supports_credentials=True)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://proy2:secret@localhost:5432/tienda_db",
)


def get_connection():
    return psycopg.connect(DATABASE_URL)


def to_json(row):
    data = dict(row)
    for key, value in data.items():
        if isinstance(value, Decimal):
            data[key] = float(value)
    return data


def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql, params or [])
            return [to_json(row) for row in cur.fetchall()]


def fetch_one(sql, params=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql, params or [])
            row = cur.fetchone()
            return to_json(row) if row else None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("usuario"):
            return jsonify({"error": "Debes iniciar sesion"}), 401
        return view(*args, **kwargs)

    return wrapped_view


def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@app.errorhandler(psycopg.Error)
def handle_db_error(error):
    return jsonify({"error": "Error de base de datos", "detalle": str(error)}), 400


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    usuario = data.get("usuario", "").strip()
    password = data.get("password", "")
    if not usuario or not password:
        return jsonify({"error": "Usuario y password son obligatorios"}), 400

    user = fetch_one(
        """
        SELECT id_usuario, usuario, nombre, password_hash
        FROM usuarios
        WHERE usuario = %s AND activo = TRUE;
        """,
        [usuario],
    )
    if not user or user["password_hash"] != password_hash(password):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    session["usuario"] = {
        "id_usuario": user["id_usuario"],
        "usuario": user["usuario"],
        "nombre": user["nombre"],
    }
    return jsonify({"usuario": session["usuario"]})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def auth_me():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"usuario": None}), 401
    return jsonify({"usuario": usuario})


@app.get("/api/catalogos")
@login_required
def catalogos():
    return jsonify(
        {
            "categorias": fetch_all(
                "SELECT id_categoria, nombre FROM categorias ORDER BY nombre"
            ),
            "proveedores": fetch_all(
                "SELECT id_proveedor, nombre FROM proveedores ORDER BY nombre"
            ),
        }
    )


@app.get("/api/productos")
@login_required
def listar_productos():
    sql = """
        SELECT
            p.id_producto, p.nombre, p.sku, p.precio, p.costo, p.stock, p.activo,
            c.id_categoria, c.nombre AS categoria,
            pr.id_proveedor, pr.nombre AS proveedor
        FROM productos p
        JOIN categorias c ON c.id_categoria = p.id_categoria
        JOIN proveedores pr ON pr.id_proveedor = p.id_proveedor
        ORDER BY p.id_producto;
    """
    return jsonify(fetch_all(sql))


@app.post("/api/productos")
@login_required
def crear_producto():
    data = request.get_json(force=True)
    required = ["nombre", "sku", "precio", "costo", "stock", "id_categoria", "id_proveedor"]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        return jsonify({"error": "Campos obligatorios faltantes", "campos": missing}), 400

    sql = """
        INSERT INTO productos
            (nombre, sku, precio, costo, stock, id_categoria, id_proveedor, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id_producto, nombre, sku, precio, costo, stock;
    """
    product = fetch_one(
        sql,
        [
            data["nombre"],
            data["sku"],
            data["precio"],
            data["costo"],
            data["stock"],
            data["id_categoria"],
            data["id_proveedor"],
        ],
    )
    return jsonify(product), 201


@app.put("/api/productos/<int:product_id>")
@login_required
def actualizar_producto(product_id):
    data = request.get_json(force=True)
    sql = """
        UPDATE productos
        SET nombre = %s,
            sku = %s,
            precio = %s,
            costo = %s,
            stock = %s,
            id_categoria = %s,
            id_proveedor = %s,
            activo = %s
        WHERE id_producto = %s
        RETURNING id_producto, nombre, sku, precio, costo, stock, activo;
    """
    product = fetch_one(
        sql,
        [
            data.get("nombre"),
            data.get("sku"),
            data.get("precio"),
            data.get("costo"),
            data.get("stock"),
            data.get("id_categoria"),
            data.get("id_proveedor"),
            data.get("activo", True),
            product_id,
        ],
    )
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(product)


@app.delete("/api/productos/<int:product_id>")
@login_required
def eliminar_producto(product_id):
    deleted = fetch_one(
        """
        UPDATE productos
        SET activo = FALSE
        WHERE id_producto = %s
        RETURNING id_producto, nombre, activo;
        """,
        [product_id],
    )
    if not deleted:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(deleted)


@app.get("/api/clientes")
@login_required
def listar_clientes():
    return jsonify(
        fetch_all(
            """
            SELECT id_cliente, nombre, nit, telefono, email
            FROM clientes
            ORDER BY id_cliente;
            """
        )
    )


@app.post("/api/clientes")
@login_required
def crear_cliente():
    data = request.get_json(force=True)
    required = ["nombre", "nit", "telefono", "email"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Campos obligatorios faltantes", "campos": missing}), 400

    return (
        jsonify(
            fetch_one(
                """
                INSERT INTO clientes (nombre, nit, telefono, email)
                VALUES (%s, %s, %s, %s)
                RETURNING id_cliente, nombre, nit, telefono, email;
                """,
                [data["nombre"], data["nit"], data["telefono"], data["email"]],
            )
        ),
        201,
    )


@app.put("/api/clientes/<int:client_id>")
@login_required
def actualizar_cliente(client_id):
    data = request.get_json(force=True)
    client = fetch_one(
        """
        UPDATE clientes
        SET nombre = %s, nit = %s, telefono = %s, email = %s
        WHERE id_cliente = %s
        RETURNING id_cliente, nombre, nit, telefono, email;
        """,
        [
            data.get("nombre"),
            data.get("nit"),
            data.get("telefono"),
            data.get("email"),
            client_id,
        ],
    )
    if not client:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(client)


@app.delete("/api/clientes/<int:client_id>")
@login_required
def eliminar_cliente(client_id):
    try:
        deleted = fetch_one(
            """
            DELETE FROM clientes
            WHERE id_cliente = %s
            RETURNING id_cliente, nombre;
            """,
            [client_id],
        )
    except psycopg.errors.ForeignKeyViolation:
        return jsonify({"error": "No se puede eliminar un cliente con ventas registradas"}), 400

    if not deleted:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(deleted)


@app.post("/api/ventas")
@login_required
def crear_venta():
    data = request.get_json(force=True)
    detalles = data.get("detalles", [])
    if not detalles:
        return jsonify({"error": "La venta necesita al menos un producto"}), 400

    with get_connection() as conn:
        try:
            conn.execute("BEGIN;")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO ventas (id_cliente, id_empleado, total, estado)
                    VALUES (%s, %s, 0, 'PAGADA')
                    RETURNING id_venta;
                    """,
                    [data["id_cliente"], data["id_empleado"]],
                )
                id_venta = cur.fetchone()["id_venta"]
                total = Decimal("0")

                for item in detalles:
                    cur.execute(
                        """
                        SELECT id_producto, precio, stock
                        FROM productos
                        WHERE id_producto = %s AND activo = TRUE
                        FOR UPDATE;
                        """,
                        [item["id_producto"]],
                    )
                    product = cur.fetchone()
                    cantidad = int(item["cantidad"])
                    if not product:
                        raise ValueError("Producto no encontrado o inactivo")
                    if product["stock"] < cantidad:
                        raise ValueError("Stock insuficiente para completar la venta")

                    subtotal = product["precio"] * cantidad
                    total += subtotal
                    cur.execute(
                        """
                        INSERT INTO detalle_venta
                            (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        [id_venta, item["id_producto"], cantidad, product["precio"], subtotal],
                    )
                    cur.execute(
                        """
                        UPDATE productos
                        SET stock = stock - %s
                        WHERE id_producto = %s;
                        """,
                        [cantidad, item["id_producto"]],
                    )

                cur.execute(
                    """
                    UPDATE ventas
                    SET total = %s
                    WHERE id_venta = %s
                    RETURNING id_venta, total, fecha;
                    """,
                    [total, id_venta],
                )
                venta = to_json(cur.fetchone())
            conn.execute("COMMIT;")
            return jsonify(venta), 201
        except Exception as error:
            conn.execute("ROLLBACK;")
            return jsonify({"error": "Venta cancelada", "detalle": str(error)}), 400


@app.get("/api/reportes/resumen-ventas")
@login_required
def resumen_ventas():
    return jsonify(
        fetch_all(
            """
            SELECT id_venta, fecha, cliente, empleado, total, productos_distintos, unidades_vendidas
            FROM vw_resumen_ventas
            ORDER BY fecha DESC
            LIMIT 15;
            """
        )
    )


@app.get("/api/reportes/productos-mas-vendidos")
@login_required
def productos_mas_vendidos():
    return jsonify(
        fetch_all(
            """
            SELECT
                p.nombre,
                c.nombre AS categoria,
                SUM(d.cantidad) AS unidades,
                SUM(d.subtotal) AS ingreso
            FROM detalle_venta d
            JOIN productos p ON p.id_producto = d.id_producto
            JOIN categorias c ON c.id_categoria = p.id_categoria
            GROUP BY p.nombre, c.nombre
            HAVING SUM(d.cantidad) >= 3
            ORDER BY unidades DESC, ingreso DESC
            LIMIT 10;
            """
        )
    )


@app.get("/api/reportes/clientes-frecuentes")
@login_required
def clientes_frecuentes():
    return jsonify(
        fetch_all(
            """
            SELECT c.nombre, c.nit, COUNT(v.id_venta) AS compras, SUM(v.total) AS total_comprado
            FROM clientes c
            JOIN ventas v ON v.id_cliente = c.id_cliente
            WHERE c.id_cliente IN (
                SELECT id_cliente
                FROM ventas
                GROUP BY id_cliente
                HAVING COUNT(*) >= 1
            )
            GROUP BY c.nombre, c.nit
            ORDER BY total_comprado DESC
            LIMIT 10;
            """
        )
    )


@app.get("/api/reportes/stock-critico")
@login_required
def stock_critico():
    return jsonify(
        fetch_all(
            """
            WITH promedio_stock AS (
                SELECT AVG(stock) AS promedio
                FROM productos
                WHERE activo = TRUE
            )
            SELECT p.nombre, p.sku, p.stock, c.nombre AS categoria
            FROM productos p
            JOIN categorias c ON c.id_categoria = p.id_categoria
            CROSS JOIN promedio_stock ps
            WHERE p.activo = TRUE AND p.stock < ps.promedio
            ORDER BY p.stock ASC
            LIMIT 10;
            """
        )
    )


@app.get("/api/reportes/productos-sin-ventas")
@login_required
def productos_sin_ventas():
    return jsonify(
        fetch_all(
            """
            SELECT p.nombre, p.sku, p.stock
            FROM productos p
            WHERE NOT EXISTS (
                SELECT 1
                FROM detalle_venta d
                WHERE d.id_producto = p.id_producto
            )
            ORDER BY p.nombre;
            """
        )
    )


@app.get("/api/reportes/resumen-ventas.csv")
@login_required
def exportar_resumen_csv():
    rows = fetch_all(
        """
        SELECT id_venta, fecha, cliente, empleado, total, productos_distintos, unidades_vendidas
        FROM vw_resumen_ventas
        ORDER BY fecha DESC;
        """
    )
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id_venta",
            "fecha",
            "cliente",
            "empleado",
            "total",
            "productos_distintos",
            "unidades_vendidas",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=resumen_ventas.csv"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_ENV") == "development")
