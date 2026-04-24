# Diagrama entidad-relacion

```mermaid
erDiagram
    CATEGORIAS ||--o{ PRODUCTOS : clasifica
    PROVEEDORES ||--o{ PRODUCTOS : suministra
    CLIENTES ||--o{ VENTAS : realiza
    EMPLEADOS ||--o{ VENTAS : atiende
    VENTAS ||--o{ DETALLE_VENTA : contiene
    PRODUCTOS ||--o{ DETALLE_VENTA : aparece_en

    CATEGORIAS {
        int id_categoria PK
        varchar nombre
        text descripcion
    }

    PROVEEDORES {
        int id_proveedor PK
        varchar nombre
        varchar telefono
        varchar email
        varchar ciudad
    }

    CLIENTES {
        int id_cliente PK
        varchar nombre
        varchar nit
        varchar telefono
        varchar email
    }

    EMPLEADOS {
        int id_empleado PK
        varchar nombre
        varchar puesto
        date fecha_contratacion
    }

    PRODUCTOS {
        int id_producto PK
        int id_categoria FK
        int id_proveedor FK
        varchar nombre
        varchar sku
        numeric precio
        numeric costo
        int stock
        boolean activo
    }

    VENTAS {
        int id_venta PK
        int id_cliente FK
        int id_empleado FK
        timestamp fecha
        numeric total
        varchar estado
    }

    DETALLE_VENTA {
        int id_detalle PK
        int id_venta FK
        int id_producto FK
        int cantidad
        numeric precio_unitario
        numeric subtotal
    }
```

## Explicacion rapida de relaciones

- Una categoria puede tener muchos productos, pero cada producto pertenece a una categoria.
- Un proveedor puede suministrar muchos productos, pero cada producto tiene un proveedor principal.
- Un cliente puede realizar muchas ventas, pero cada venta pertenece a un cliente.
- Un empleado puede atender muchas ventas, pero cada venta es atendida por un empleado.
- Una venta puede tener varios productos mediante `detalle_venta`.
- Un producto puede aparecer en muchas ventas mediante `detalle_venta`.
