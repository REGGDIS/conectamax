# Spec 01 — Base de datos SQLite (contrato de datos)

**Validación SDD:** objetivo ✅ · alcance ✅ · RF (esquema §15) ✅ · RNF ✅ · entradas/salidas ✅ · criterios ✅ · dependencias ✅

**Estado:** Propuesta para acuerdo Raymond ↔ Roberto
**Decisión de arquitectura:** Modelo **relacional completo** (Plan v3.2 §15), con una vista analítica que reproduce el contrato plano que Roberto ya tiene en `config/settings.py`.
**Fase:** 2 (Carta Gantt) · **Responsable:** Raymond
**Archivo de BD (ruta congelada, según `settings.py`):** `data/conectamax.db`
**Repo:** `REGGDIS/conectamax`

> **Principio rector:** el modelo relacional NO debe romper la app de Roberto. Su app lee un DataFrame plano con columnas definidas en `settings.py`. Por eso la pieza central de integración es la vista **`comportamiento_cliente`**, que devuelve **exactamente** esas columnas (más `abandono`). La app y el modelo consumen esa vista; las 8 tablas normalizadas viven debajo.

---

## 0. Reconciliación con lo que Roberto ya construyó

Contrato real vigente (`config/settings.py`):

- `ID_COLUMN = "id_cliente"` (formato `CXM0001`, TEXT)
- `TARGET_COLUMN = "abandono"` (0 = permanece, 1 = abandona)
- Columnas del CSV: `id_cliente, nombre, ciudad, antiguedad_meses, tipo_contrato, plan, monto_mensual, reclamos_ultimos_6_meses, pagos_atrasados, dias_sin_uso, satisfaccion, abandono` (+ opcionales `edad, cantidad_servicios`)
- Dominios reales en los datos:
  - **ciudades:** Santiago, Valparaiso, Concepcion, La Serena, Temuco, Antofagasta, Rancagua, Iquique, Valdivia, Puerto Montt, Arica
  - **planes:** Basico, Movil Max, Fibra Plus, Hogar Total, Empresas
  - **tipo_contrato:** Mensual, Anual, Bienal

**Decisiones de reconciliación (firmes):**

1. La variable objetivo se llama **`abandono`** (no `churn_real`). La regla anti-fuga §29.6 se cumple igual: `abandono` es el estado real (en `clientes`); la predicción del modelo vive aparte en `predicciones`.
2. Ruta de BD = **`data/conectamax.db`** (la de `settings.py`), no `database/`.
3. La vista `comportamiento_cliente` devuelve **los mismos nombres de columna** del contrato de Roberto → su app no cambia.
4. Convenciones SQL: snake_case sin tildes; fechas TEXT ISO `YYYY-MM-DD`; booleanos INTEGER 0/1.

---

## 1. Tablas operacionales (OLTP) — modelo relacional

### 1. `sucursales`  (dimensión; Plan: 5 sucursales)
| Columna | Tipo | Notas |
|---|---|---|
| id_sucursal | INTEGER PK | |
| nombre | TEXT | Casa Matriz Santiago, Sucursal Norte, Centro, Sur, Austral |
| ciudad_sede | TEXT | |
| region | TEXT | Metropolitana, Antofagasta, Valparaíso, Biobío, Los Lagos |

> Las 11 ciudades de los datos se asignan a la sucursal/región más cercana (mapa en Spec 02).

### 2. `servicios`  (catálogo de planes)
| Columna | Tipo | Notas |
|---|---|---|
| id_servicio | INTEGER PK | |
| codigo | TEXT | SRV-BAS, SRV-MMX, SRV-FIB, SRV-HOG, SRV-EMP |
| nombre | TEXT | Basico · Movil Max · Fibra Plus · Hogar Total · Empresas |
| tipo | TEXT | movil · internet · tv · paquete · empresarial |
| precio_mensual | REAL | base del catálogo |

### 3. `clientes`
| Columna | Tipo | Notas |
|---|---|---|
| id_cliente | TEXT PK | `CXM0001` |
| nombre | TEXT | |
| edad | INTEGER | |
| genero | TEXT | F · M · otro |
| ciudad | TEXT | dominio real (11 ciudades) |
| id_sucursal | INTEGER FK → sucursales | |
| segmento | TEXT | Jóvenes Digitales, Familias Conectadas, Profesionales Urbanos, Adultos Mayores, Clientes en Riesgo |
| tipo_cliente | TEXT | residencial · pyme |
| antiguedad_meses | INTEGER | |
| ingreso_mensual | REAL | |
| satisfaccion | INTEGER | 1–5 |
| dias_sin_uso | INTEGER | señal de churn (la usa Roberto) |
| estado | TEXT | activo · inactivo |
| fecha_alta | TEXT | YYYY-MM-DD |
| **abandono** | INTEGER 0/1 | **variable objetivo (real)** |

### 4. `contratos`  (cliente ↔ servicio)
| Columna | Tipo | Notas |
|---|---|---|
| id_contrato | INTEGER PK | |
| id_cliente | TEXT FK → clientes | |
| id_servicio | INTEGER FK → servicios | define el `plan` |
| tipo_contrato | TEXT | Mensual · Anual · Bienal |
| fecha_inicio | TEXT | |
| fecha_fin | TEXT | NULL si vigente |
| estado | TEXT | activo · finalizado |
| monto_mensual | REAL | cargo real del contrato |

> De aquí se derivan tres columnas del contrato de Roberto: `plan` (servicio del contrato principal), `monto_mensual` (Σ contratos activos) y `cantidad_servicios` (conteo de contratos activos).

### 5. `facturas`
| Columna | Tipo | Notas |
|---|---|---|
| id_factura | INTEGER PK | |
| id_cliente | TEXT FK → clientes | |
| periodo | TEXT | YYYY-MM |
| monto_facturado | REAL | |
| fecha_emision | TEXT | |
| fecha_vencimiento | TEXT | |
| estado | TEXT | pagada · pendiente · vencida |

### 6. `pagos`
| Columna | Tipo | Notas |
|---|---|---|
| id_pago | INTEGER PK | |
| id_factura | INTEGER FK → facturas | |
| fecha_pago | TEXT | |
| monto_pagado | REAL | |
| estado | TEXT | a_tiempo · atrasado |
| dias_atraso | INTEGER | 0 si a tiempo |

> `pagos_atrasados` (contrato de Roberto) = conteo de pagos con estado `atrasado` en los últimos 6 meses por cliente.

### 7. `reclamos`
| Columna | Tipo | Notas |
|---|---|---|
| id_reclamo | INTEGER PK | |
| id_cliente | TEXT FK → clientes | |
| id_sucursal | INTEGER FK → sucursales | NULL permitido |
| fecha | TEXT | |
| tipo | TEXT | facturacion · tecnico · servicio · comercial |
| canal | TEXT | telefono · app · sucursal · web |
| estado | TEXT | abierto · resuelto |

> `reclamos_ultimos_6_meses` = conteo de reclamos en los últimos 6 meses por cliente.

### 8. `interacciones`
| Columna | Tipo | Notas |
|---|---|---|
| id_interaccion | INTEGER PK | |
| id_cliente | TEXT FK → clientes | |
| fecha | TEXT | |
| canal | TEXT | soporte · llamada · app · sucursal |
| motivo | TEXT | |
| duracion_min | INTEGER | NULL permitido |

---

## 2. Vista analítica (puente de integración)

### 9. `comportamiento_cliente`  — VISTA SQL
Reproduce **exactamente** el contrato de `settings.py` (+ columnas de apoyo al final). Es lo que consumen la app de Roberto y el modelo. **No contiene probabilidad ni nivel de riesgo** (§29.6).

| Columna | Origen |
|---|---|
| id_cliente | clientes |
| nombre | clientes |
| ciudad | clientes |
| antiguedad_meses | clientes |
| tipo_contrato | contrato principal |
| plan | servicios (vía contrato principal) |
| monto_mensual | Σ contratos activos |
| reclamos_ultimos_6_meses | COUNT reclamos 6m |
| pagos_atrasados | COUNT pagos atrasados 6m |
| dias_sin_uso | clientes |
| satisfaccion | clientes |
| **abandono** | clientes (**target**) |
| edad | clientes (opcional) |
| cantidad_servicios | COUNT contratos activos (opcional) |
| region | sucursales (apoyo H6) |
| segmento | clientes (apoyo segmentación) |

> Orden y nombres de las 14 primeras columnas = `COLUMNAS_OBLIGATORIAS` + `COLUMNAS_OPCIONALES` de `settings.py`. Así la app de Roberto puede apuntar a esta vista en la Fase 7 sin tocar su validación.

---

## 3. Resultados del modelo (separados — §29.6)

### 10. `predicciones`
| Columna | Tipo | Notas |
|---|---|---|
| id_prediccion | INTEGER PK | |
| id_cliente | TEXT FK → clientes | |
| probabilidad_churn | REAL | 0.0–1.0 |
| nivel_riesgo | TEXT | bajo (<30%) · medio (30–<60%) · alto (≥60%) — §29.5 |
| modelo | TEXT | arbol_decision · regresion_logistica |
| version_modelo | TEXT | p. ej. v1 |
| fecha_prediccion | TEXT | YYYY-MM-DD HH:MM:SS |

> Existe ya `clientes_prueba` (infra de Roberto): es solo para pruebas de conexión, **no** es parte del esquema definitivo.

---

## 4. Diagrama de relaciones

```text
            sucursales 1───∞ clientes 1───∞ contratos ∞───1 servicios
                 ▲              │  │  │
                 │              │  │  └──∞ facturas 1───∞ pagos
                 └──── ∞ reclamos │
                                  └────∞ interacciones

   comportamiento_cliente  =  VISTA sobre (clientes ⨝ contratos ⨝ servicios
                                ⨝ agregados de reclamos/pagos/sucursales)
   predicciones  ∞───1  clientes        (salida del modelo, separada)
```

---

## 5. Estrategia de generación (resumen; detalle en Spec 02)

Para mantener coherencia, **generar primero el perfil plano** de cada cliente (drivers + `abandono` ponderado con ruido) y **luego expandir** a las tablas normalizadas: crear tantas filas de `reclamos`/`pagos atrasados` como indique el conteo, y los `contratos` que reproduzcan `plan`, `monto_mensual` y `cantidad_servicios`. Resultado: ≥ 2.000 clientes cuyos agregados en `comportamiento_cliente` son realistas y consistentes.

---

## 6. Decisiones cerradas y pendientes

**Cerradas:** target = `abandono` · BD = `data/conectamax.db` · vista reproduce el contrato de Roberto · modelo relacional completo.

**Pendientes de confirmar con Roberto:**
1. ¿`comportamiento_cliente` como **vista** (recomendado, siempre fresca) o tabla materializada?
2. Pesos de los drivers del `abandono` sintético (Spec 02).
3. Ubicación del modelo persistido: propuesta `models/modelo_churn.pkl` (Roberto aún no tiene carpeta `models/`).
4. Momento de cambiar la fuente de datos de la app: de CSV/`session_state` a la vista `comportamiento_cliente` (Fase 7).
