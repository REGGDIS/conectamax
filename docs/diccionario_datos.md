# Diccionario de datos — ConectaMax Analytics

**Base de datos:** `data/conectamax.db` (SQLite) · **Esquema:** `database/schema.sql`
**Modelo:** relacional (OLTP) con vista analítica `comportamiento_cliente` para el modelo de churn.
**Convenciones:** identificadores en snake_case sin tildes · fechas TEXT ISO `YYYY-MM-DD` · booleanos INTEGER 0/1.
**Entregable:** Plan v3.2 §15 (diccionario de datos).

> Notación: **PK** = clave primaria · **FK** = clave foránea · *AI* = autoincremental.

---

## 1. `sucursales`
Catálogo de las 5 sucursales comerciales (dimensión geográfica; apoya la hipótesis H6).

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_sucursal | INTEGER | No | Identificador de la sucursal. | PK |
| nombre | TEXT | No | Nombre comercial (p. ej. "Casa Matriz Santiago"). | |
| ciudad_sede | TEXT | Sí | Ciudad donde está la sucursal. | |
| region | TEXT | Sí | Región administrativa de la sucursal. | |

## 2. `servicios`
Catálogo de planes/servicios ofrecidos, con su precio base mensual.

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_servicio | INTEGER | No | Identificador del servicio. | PK |
| codigo | TEXT | No | Código del catálogo (SRV-BAS, SRV-MMX, SRV-FIB, SRV-HOG, SRV-EMP). Único. | |
| nombre | TEXT | No | Nombre del plan (Basico, Movil Max, Fibra Plus, Hogar Total, Empresas). | |
| tipo | TEXT | Sí | Categoría: movil, internet, tv, paquete, empresarial. | |
| precio_mensual | REAL | Sí | Precio mensual base del plan (CLP). | |

## 3. `clientes`
Datos maestros del cliente y su estado real de abandono (variable objetivo histórica).

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_cliente | TEXT | No | Identificador único del cliente (formato `CXM0001`). | PK |
| nombre | TEXT | Sí | Nombre del cliente. | |
| edad | INTEGER | Sí | Edad en años (18–85). | |
| genero | TEXT | Sí | F, M u otro. | |
| ciudad | TEXT | Sí | Ciudad de residencia (11 ciudades). | |
| id_sucursal | INTEGER | Sí | Sucursal asociada. | FK → sucursales(id_sucursal) |
| segmento | TEXT | Sí | Segmento de negocio (Jóvenes Digitales, Familias Conectadas, Profesionales Urbanos, Adultos Mayores, Clientes en Riesgo). | |
| tipo_cliente | TEXT | Sí | residencial o pyme. | |
| antiguedad_meses | INTEGER | Sí | Meses de permanencia como cliente. | |
| ingreso_mensual | REAL | Sí | Ingreso mensual estimado (CLP). | |
| satisfaccion | INTEGER | Sí | Nivel de satisfacción 1–5. Predictor (H2). | |
| dias_sin_uso | INTEGER | Sí | Días sin actividad reciente. Predictor. | |
| estado | TEXT | Sí | activo o inactivo. | |
| fecha_alta | TEXT | Sí | Fecha de alta del cliente (YYYY-MM-DD). | |
| **abandono** | INTEGER | Sí | **Variable objetivo real:** 1 = abandonó, 0 = permanece. | |

## 4. `contratos`
Servicios contratados por cada cliente (relación cliente ↔ servicio). Un cliente puede tener varios.

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_contrato | INTEGER | No | Identificador del contrato (AI). | PK |
| id_cliente | TEXT | No | Cliente titular. | FK → clientes(id_cliente) |
| id_servicio | INTEGER | No | Servicio contratado (define el `plan`). | FK → servicios(id_servicio) |
| tipo_contrato | TEXT | Sí | Mensual, Anual o Bienal. | |
| fecha_inicio | TEXT | Sí | Inicio del contrato (YYYY-MM-DD). | |
| fecha_fin | TEXT | Sí | Fin del contrato; NULL si vigente. | |
| estado | TEXT | Sí | activo o finalizado. | |
| monto_mensual | REAL | Sí | Cargo mensual del contrato (CLP). | |
| es_principal | INTEGER | Sí | 1 si es el contrato/plan principal del cliente, 0 si es adicional. | |

## 5. `facturas`
Documentos de cobro emitidos a cada cliente por período.

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_factura | INTEGER | No | Identificador de la factura (AI). | PK |
| id_cliente | TEXT | No | Cliente facturado. | FK → clientes(id_cliente) |
| periodo | TEXT | Sí | Período de la factura (YYYY-MM). | |
| monto_facturado | REAL | Sí | Monto total facturado (CLP). | |
| fecha_emision | TEXT | Sí | Fecha de emisión (YYYY-MM-DD). | |
| fecha_vencimiento | TEXT | Sí | Fecha de vencimiento (YYYY-MM-DD). | |
| estado | TEXT | Sí | pagada, pendiente o vencida. | |

## 6. `pagos`
Pagos asociados a cada factura. Permiten derivar la morosidad.

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_pago | INTEGER | No | Identificador del pago (AI). | PK |
| id_factura | INTEGER | No | Factura pagada. | FK → facturas(id_factura) |
| fecha_pago | TEXT | Sí | Fecha del pago (YYYY-MM-DD). | |
| monto_pagado | REAL | Sí | Monto abonado (CLP). | |
| estado | TEXT | Sí | a_tiempo o atrasado. | |
| dias_atraso | INTEGER | Sí | Días de atraso del pago (0 si a tiempo). | |

## 7. `reclamos`
Historial de reclamos del cliente. Sustenta la hipótesis H1.

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_reclamo | INTEGER | No | Identificador del reclamo (AI). | PK |
| id_cliente | TEXT | No | Cliente que reclama. | FK → clientes(id_cliente) |
| id_sucursal | INTEGER | Sí | Sucursal asociada (si aplica). | FK → sucursales(id_sucursal) |
| fecha | TEXT | Sí | Fecha del reclamo (YYYY-MM-DD). | |
| tipo | TEXT | Sí | facturacion, tecnico, servicio o comercial. | |
| canal | TEXT | Sí | telefono, app, sucursal o web. | |
| estado | TEXT | Sí | abierto o resuelto. | |

## 8. `interacciones`
Contactos del cliente con la empresa (soporte, llamadas, app, sucursal).

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_interaccion | INTEGER | No | Identificador de la interacción (AI). | PK |
| id_cliente | TEXT | No | Cliente que interactúa. | FK → clientes(id_cliente) |
| fecha | TEXT | Sí | Fecha de la interacción (YYYY-MM-DD). | |
| canal | TEXT | Sí | soporte, llamada, app o sucursal. | |
| motivo | TEXT | Sí | Motivo del contacto (consulta, soporte, reclamo, venta). | |
| duracion_min | INTEGER | Sí | Duración en minutos. | |

## 9. `comportamiento_cliente`  (VISTA)
Vista analítica que **alimenta el modelo** y la app. Agrega las tablas anteriores y reproduce, en orden, las columnas del contrato de `config/settings.py` (+ apoyo). **No** contiene probabilidad ni nivel de riesgo (regla anti-fuga §29.6).

| Campo | Tipo | Origen / cálculo |
|---|---|---|
| id_cliente | TEXT | clientes |
| nombre | TEXT | clientes |
| ciudad | TEXT | clientes |
| antiguedad_meses | INTEGER | clientes |
| tipo_contrato | TEXT | contrato principal (es_principal = 1) |
| plan | TEXT | servicio del contrato principal |
| monto_mensual | REAL | monto del contrato principal |
| reclamos_ultimos_6_meses | INTEGER | COUNT de reclamos del cliente |
| pagos_atrasados | INTEGER | COUNT de pagos con estado `atrasado` |
| dias_sin_uso | INTEGER | clientes |
| satisfaccion | INTEGER | clientes |
| **abandono** | INTEGER | clientes (variable objetivo) |
| edad | INTEGER | clientes (opcional) |
| cantidad_servicios | INTEGER | COUNT de contratos activos del cliente |
| region | TEXT | sucursales (apoyo H6) |
| segmento | TEXT | clientes (apoyo segmentación) |

> Las primeras 14 columnas coinciden, en nombre y orden, con `COLUMNAS_OBLIGATORIAS` + `COLUMNAS_OPCIONALES` de `config/settings.py`.

## 10. `predicciones`
Resultados producidos por el modelo. Se almacenan **separados** del estado real (§29.6).

| Campo | Tipo | Nulo | Descripción | Clave |
|---|---|---|---|---|
| id_prediccion | INTEGER | No | Identificador de la predicción (AI). | PK |
| id_cliente | TEXT | No | Cliente evaluado. | FK → clientes(id_cliente) |
| probabilidad_churn | REAL | Sí | Probabilidad estimada de abandono (0.0–1.0). | |
| nivel_riesgo | TEXT | Sí | bajo (< 30 %), medio (30–< 60 %), alto (≥ 60 %) — umbrales §29.5. | |
| modelo | TEXT | Sí | arbol_decision o regresion_logistica. | |
| version_modelo | TEXT | Sí | Versión del modelo (p. ej. v1). | |
| fecha_prediccion | TEXT | Sí | Fecha y hora de la predicción. | |

---

## Relaciones (resumen)

```text
sucursales 1───∞ clientes 1───∞ contratos ∞───1 servicios
                 │  │  │
                 │  │  └──∞ facturas 1───∞ pagos
                 │  └─────∞ interacciones
                 └────────∞ reclamos ∞───1 sucursales

comportamiento_cliente = VISTA (clientes ⨝ contratos ⨝ servicios ⨝ agregados)
predicciones ∞───1 clientes      (salida del modelo, separada)
```

## Notas de integridad
- `PRAGMA foreign_keys = ON` activo: se respetan las claves foráneas.
- Índices en las FK de mayor uso (contratos, facturas, pagos, reclamos, interacciones, predicciones) para acelerar las consultas del dashboard.
- La tabla `clientes_prueba` de la infraestructura previa de Roberto **no** forma parte de este esquema definitivo.
