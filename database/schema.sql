-- ConectaMax Analytics - Esquema relacional definitivo (Spec 01)
-- SQLite. Ejecutar con: sqlite3 data/conectamax.db < schema.sql
PRAGMA foreign_keys = ON;

-- ----- 1. sucursales (dimension) -----
CREATE TABLE IF NOT EXISTS sucursales (
    id_sucursal  INTEGER PRIMARY KEY,
    nombre       TEXT NOT NULL,
    ciudad_sede  TEXT,
    region       TEXT
);

-- ----- 2. servicios (catalogo de planes) -----
CREATE TABLE IF NOT EXISTS servicios (
    id_servicio    INTEGER PRIMARY KEY,
    codigo         TEXT UNIQUE NOT NULL,
    nombre         TEXT NOT NULL,
    tipo           TEXT,
    precio_mensual REAL
);

-- ----- 3. clientes -----
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente       TEXT PRIMARY KEY,
    nombre           TEXT,
    edad             INTEGER,
    genero           TEXT,
    ciudad           TEXT,
    id_sucursal      INTEGER,
    segmento         TEXT,
    tipo_cliente     TEXT,
    antiguedad_meses INTEGER,
    ingreso_mensual  REAL,
    satisfaccion     INTEGER,
    dias_sin_uso     INTEGER,
    estado           TEXT,
    fecha_alta       TEXT,
    abandono         INTEGER,
    FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
);

-- ----- 4. contratos -----
CREATE TABLE IF NOT EXISTS contratos (
    id_contrato   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente    TEXT NOT NULL,
    id_servicio   INTEGER NOT NULL,
    tipo_contrato TEXT,
    fecha_inicio  TEXT,
    fecha_fin     TEXT,
    estado        TEXT,
    monto_mensual REAL,
    es_principal  INTEGER DEFAULT 0,
    FOREIGN KEY (id_cliente)  REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

-- ----- 5. facturas -----
CREATE TABLE IF NOT EXISTS facturas (
    id_factura        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente        TEXT NOT NULL,
    periodo           TEXT,
    monto_facturado   REAL,
    fecha_emision     TEXT,
    fecha_vencimiento TEXT,
    estado            TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

-- ----- 6. pagos -----
CREATE TABLE IF NOT EXISTS pagos (
    id_pago      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_factura   INTEGER NOT NULL,
    fecha_pago   TEXT,
    monto_pagado REAL,
    estado       TEXT,
    dias_atraso  INTEGER,
    FOREIGN KEY (id_factura) REFERENCES facturas(id_factura)
);

-- ----- 7. reclamos -----
CREATE TABLE IF NOT EXISTS reclamos (
    id_reclamo  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente  TEXT NOT NULL,
    id_sucursal INTEGER,
    fecha       TEXT,
    tipo        TEXT,
    canal       TEXT,
    estado      TEXT,
    FOREIGN KEY (id_cliente)  REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
);

-- ----- 8. interacciones -----
CREATE TABLE IF NOT EXISTS interacciones (
    id_interaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente     TEXT NOT NULL,
    fecha          TEXT,
    canal          TEXT,
    motivo         TEXT,
    duracion_min   INTEGER,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

-- ----- 10. predicciones (salida del modelo, separada) -----
CREATE TABLE IF NOT EXISTS predicciones (
    id_prediccion      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente         TEXT NOT NULL,
    probabilidad_churn REAL,
    nivel_riesgo       TEXT,
    modelo             TEXT,
    version_modelo     TEXT,
    fecha_prediccion   TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

-- ----- indices -----
CREATE INDEX IF NOT EXISTS idx_contratos_cliente    ON contratos(id_cliente);
CREATE INDEX IF NOT EXISTS idx_facturas_cliente     ON facturas(id_cliente);
CREATE INDEX IF NOT EXISTS idx_pagos_factura        ON pagos(id_factura);
CREATE INDEX IF NOT EXISTS idx_reclamos_cliente     ON reclamos(id_cliente);
CREATE INDEX IF NOT EXISTS idx_interacciones_cliente ON interacciones(id_cliente);
CREATE INDEX IF NOT EXISTS idx_predicciones_cliente ON predicciones(id_cliente);

-- ----- 9. vista analitica comportamiento_cliente -----
-- Reproduce el contrato plano de config/settings.py (mismas columnas y orden) + apoyo.
DROP VIEW IF EXISTS comportamiento_cliente;
CREATE VIEW comportamiento_cliente AS
SELECT
    c.id_cliente,
    c.nombre,
    c.ciudad,
    c.antiguedad_meses,
    ct.tipo_contrato,
    ct.plan,
    COALESCE(ct.monto_mensual, 0)            AS monto_mensual,
    COALESCE(r.reclamos_ultimos_6_meses, 0)  AS reclamos_ultimos_6_meses,
    COALESCE(p.pagos_atrasados, 0)           AS pagos_atrasados,
    c.dias_sin_uso,
    c.satisfaccion,
    c.abandono,
    c.edad,
    COALESCE(ct.cantidad_servicios, 0)       AS cantidad_servicios,
    s.region,
    c.segmento
FROM clientes c
LEFT JOIN sucursales s ON s.id_sucursal = c.id_sucursal
LEFT JOIN (
    SELECT
        co.id_cliente,
        MAX(CASE WHEN co.es_principal = 1 THEN co.monto_mensual END) AS monto_mensual,
        COUNT(*)              AS cantidad_servicios,
        MAX(CASE WHEN co.es_principal = 1 THEN co.tipo_contrato END) AS tipo_contrato,
        MAX(CASE WHEN co.es_principal = 1 THEN sv.nombre END)        AS plan
    FROM contratos co
    JOIN servicios sv ON sv.id_servicio = co.id_servicio
    WHERE co.estado = 'activo'
    GROUP BY co.id_cliente
) ct ON ct.id_cliente = c.id_cliente
LEFT JOIN (
    SELECT id_cliente, COUNT(*) AS reclamos_ultimos_6_meses
    FROM reclamos
    GROUP BY id_cliente
) r ON r.id_cliente = c.id_cliente
LEFT JOIN (
    SELECT f.id_cliente, COUNT(*) AS pagos_atrasados
    FROM facturas f
    JOIN pagos pg ON pg.id_factura = f.id_factura
    WHERE pg.estado = 'atrasado'
    GROUP BY f.id_cliente
) p ON p.id_cliente = c.id_cliente;
