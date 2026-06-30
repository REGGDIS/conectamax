-- ConectaMax Analytics - Esquema relacional definitivo (Spec 01, rev. PR #6)
PRAGMA foreign_keys = ON;

-- Parametros de configuracion (p.ej. fecha de referencia para ventanas de 6 meses)
CREATE TABLE IF NOT EXISTS parametros (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    fecha_referencia TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sucursales (
    id_sucursal  INTEGER PRIMARY KEY,
    nombre       TEXT NOT NULL,
    ciudad_sede  TEXT,
    region       TEXT
);

CREATE TABLE IF NOT EXISTS servicios (
    id_servicio    INTEGER PRIMARY KEY,
    codigo         TEXT UNIQUE NOT NULL,
    nombre         TEXT NOT NULL,
    tipo           TEXT,
    precio_mensual REAL NOT NULL CHECK (precio_mensual >= 0)
);

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente       TEXT PRIMARY KEY,
    nombre           TEXT,
    edad             INTEGER CHECK (edad IS NULL OR edad BETWEEN 0 AND 120),
    genero           TEXT,
    ciudad           TEXT,
    id_sucursal      INTEGER,
    segmento         TEXT,
    tipo_cliente     TEXT,
    antiguedad_meses INTEGER CHECK (antiguedad_meses IS NULL OR antiguedad_meses >= 0),
    ingreso_mensual  REAL,
    satisfaccion     INTEGER NOT NULL CHECK (satisfaccion BETWEEN 1 AND 5),
    dias_sin_uso     INTEGER CHECK (dias_sin_uso IS NULL OR dias_sin_uso >= 0),
    estado           TEXT,
    fecha_alta       TEXT,
    abandono         INTEGER NOT NULL CHECK (abandono IN (0, 1)),
    FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
);

CREATE TABLE IF NOT EXISTS contratos (
    id_contrato   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente    TEXT NOT NULL,
    id_servicio   INTEGER NOT NULL,
    tipo_contrato TEXT,
    fecha_inicio  TEXT,
    fecha_fin     TEXT,
    estado        TEXT NOT NULL DEFAULT 'activo',
    monto_mensual REAL NOT NULL CHECK (monto_mensual >= 0),
    es_principal  INTEGER NOT NULL DEFAULT 0 CHECK (es_principal IN (0, 1)),
    FOREIGN KEY (id_cliente)  REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);
-- Un unico contrato principal activo por cliente (punto 4)
CREATE UNIQUE INDEX IF NOT EXISTS ux_contrato_principal
    ON contratos(id_cliente) WHERE es_principal = 1 AND estado = 'activo';

CREATE TABLE IF NOT EXISTS facturas (
    id_factura        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente        TEXT NOT NULL,
    periodo           TEXT,
    monto_facturado   REAL CHECK (monto_facturado IS NULL OR monto_facturado >= 0),
    fecha_emision     TEXT,
    fecha_vencimiento TEXT,
    estado            TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

CREATE TABLE IF NOT EXISTS pagos (
    id_pago      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_factura   INTEGER NOT NULL,
    fecha_pago   TEXT,
    monto_pagado REAL CHECK (monto_pagado IS NULL OR monto_pagado >= 0),
    estado       TEXT CHECK (estado IS NULL OR estado IN ('a_tiempo', 'atrasado')),
    dias_atraso  INTEGER CHECK (dias_atraso IS NULL OR dias_atraso >= 0),
    FOREIGN KEY (id_factura) REFERENCES facturas(id_factura)
);

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

CREATE TABLE IF NOT EXISTS interacciones (
    id_interaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente     TEXT NOT NULL,
    fecha          TEXT,
    canal          TEXT,
    motivo         TEXT,
    duracion_min   INTEGER CHECK (duracion_min IS NULL OR duracion_min >= 0),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

CREATE TABLE IF NOT EXISTS predicciones (
    id_prediccion      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente         TEXT NOT NULL,
    probabilidad_churn REAL NOT NULL CHECK (probabilidad_churn BETWEEN 0 AND 1),
    nivel_riesgo       TEXT NOT NULL CHECK (nivel_riesgo IN ('bajo', 'medio', 'alto')),
    modelo             TEXT NOT NULL,
    version_modelo     TEXT NOT NULL,
    fecha_prediccion   TEXT NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

CREATE INDEX IF NOT EXISTS idx_contratos_cliente    ON contratos(id_cliente);
CREATE INDEX IF NOT EXISTS idx_facturas_cliente     ON facturas(id_cliente);
CREATE INDEX IF NOT EXISTS idx_pagos_factura        ON pagos(id_factura);
CREATE INDEX IF NOT EXISTS idx_reclamos_cliente     ON reclamos(id_cliente);
CREATE INDEX IF NOT EXISTS idx_interacciones_cliente ON interacciones(id_cliente);
CREATE INDEX IF NOT EXISTS idx_predicciones_cliente ON predicciones(id_cliente);

-- Vista analitica: reproduce el contrato de settings.py.
-- monto_mensual = SUMA de contratos activos; plan/tipo_contrato del contrato principal (punto 5).
-- reclamos y pagos atrasados se cuentan en los ULTIMOS 6 MESES respecto a parametros.fecha_referencia (punto 2).
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
        SUM(co.monto_mensual) AS monto_mensual,
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
    WHERE fecha >= date((SELECT fecha_referencia FROM parametros WHERE id = 1), '-6 months')
      AND fecha <= date((SELECT fecha_referencia FROM parametros WHERE id = 1))
    GROUP BY id_cliente
) r ON r.id_cliente = c.id_cliente
LEFT JOIN (
    SELECT f.id_cliente, COUNT(*) AS pagos_atrasados
    FROM facturas f
    JOIN pagos pg ON pg.id_factura = f.id_factura
    WHERE pg.estado = 'atrasado'
      AND f.fecha_emision >= date((SELECT fecha_referencia FROM parametros WHERE id = 1), '-6 months')
      AND f.fecha_emision <= date((SELECT fecha_referencia FROM parametros WHERE id = 1))
    GROUP BY f.id_cliente
) p ON p.id_cliente = c.id_cliente;
