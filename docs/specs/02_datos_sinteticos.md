# Spec 02 — Generador de datos sintéticos (≥ 2.000 clientes)

**Validación SDD:** objetivo ✅ · alcance ✅ · RF ✅ · RNF ✅ · entradas/salidas ✅ · criterios ✅ · dependencias ✅

**Estado:** Propuesta para acuerdo Raymond ↔ Roberto
**Fase:** 3 (Carta Gantt) · **Responsable:** Raymond
**Depende de:** Spec 01 (esquema) · **Base:** Plan v3.2 §29.3 (generación de Churn)
**Archivo:** `scripts/generate_data.py` → puebla `data/conectamax.db`
**Reproducibilidad:** `random_state = 42` / `np.random.default_rng(42)`

> **Objetivo:** generar ≥ 2.000 clientes coherentes con el contrato de Roberto (`config/settings.py`) y con relaciones plausibles, donde `abandono` surge de **varios drivers ponderados + ruido controlado** (nunca de una regla rígida, §29.3). El resultado debe poder leerse desde la vista `comportamiento_cliente` y entrenar un modelo con señal real pero no perfecta.

---

## 1. Volumen y dominios (reales, del CSV de Roberto)

- **N = 2.500 clientes** (margen sobre el mínimo de 2.000).
- **id_cliente:** `CXM0001`… formato `CXM` + 4 dígitos.
- **ciudades (11)** con peso por tamaño y su mapeo a sucursal/región:

| Ciudad | Sucursal | Región | Peso |
|---|---|---|---|
| Santiago | Casa Matriz Santiago | Metropolitana | 0.30 |
| Valparaiso | Sucursal Centro | Valparaíso | 0.10 |
| Concepcion | Sucursal Sur | Biobío | 0.10 |
| Antofagasta | Sucursal Norte | Antofagasta | 0.08 |
| Puerto Montt | Sucursal Austral | Los Lagos | 0.07 |
| La Serena | Sucursal Centro | Coquimbo | 0.07 |
| Temuco | Sucursal Sur | La Araucanía | 0.07 |
| Rancagua | Casa Matriz Santiago | O'Higgins | 0.06 |
| Iquique | Sucursal Norte | Tarapacá | 0.06 |
| Valdivia | Sucursal Austral | Los Ríos | 0.05 |
| Arica | Sucursal Norte | Arica y Parinacota | 0.04 |

- **planes (5)** y precio base mensual (CLP), coherentes con el CSV:

| plan | tipo | precio_base |
|---|---|---|
| Basico | movil | 17.990 |
| Movil Max | movil | 24.990 |
| Fibra Plus | internet | 33.990 |
| Hogar Total | paquete | 46.990 |
| Empresas | empresarial | 68.990 |

- **tipo_contrato:** Mensual (0.55), Anual (0.32), Bienal (0.13).
- **segmento (5):** Jóvenes Digitales, Familias Conectadas, Profesionales Urbanos, Adultos Mayores, Clientes en Riesgo.

---

## 2. Variables por cliente (rangos)

| Variable | Distribución / rango | Notas |
|---|---|---|
| edad | 18–85, sesgo a 25–55 | entero |
| genero | F / M / otro | — |
| antiguedad_meses | 1–72 | clientes nuevos más frecuentes |
| satisfaccion | 1–5 | depende inversamente de reclamos/morosidad |
| reclamos_ultimos_6_meses | 0–6 (Poisson λ≈1) | driver de churn |
| pagos_atrasados | 0–6 (Poisson λ≈0.8) | driver de churn |
| dias_sin_uso | 0–30 | driver de churn |
| cantidad_servicios | 1–5 | más servicios ⇒ menos churn (bundle) |
| monto_mensual | precio_base(plan) × factor por nº servicios | CLP |
| ingreso_mensual | 300.000–3.000.000 | apoyo a segmento |

> Coherencia interna: `satisfaccion` se calcula DESPUÉS de reclamos/morosidad (más reclamos ⇒ menor satisfacción), para que las variables no sean independientes.

---

## 3. Generación de `abandono` (núcleo — §29.3)

**Regla:** NO asignar `abandono` con una condición única. Se construye un **score latente** lineal sobre drivers normalizados, se pasa por una **sigmoide** para obtener probabilidad, se añade **ruido** y se muestrea Bernoulli.

```text
z = b0
  + w1 * norm(reclamos_ultimos_6_meses)     # +  fricción
  + w2 * norm(pagos_atrasados)              # +  morosidad
  + w3 * (3 - satisfaccion)/2               # +  baja satisfacción  (1→+1, 5→-1)
  + w4 * norm(dias_sin_uso)                 # +  desuso
  - w5 * norm(antiguedad_meses)             # -  fidelidad
  - w6 * norm(cantidad_servicios)           # -  bundle
  + w7 * (tipo_contrato == "Mensual")       # +  contrato corto
  + ruido ~ Normal(0, sigma)

p_churn = sigmoide(z)
abandono = 1 si Bernoulli(p_churn), si no 0
```

**Pesos finales (calibrados y verificados en `generate_data.py`):**

| Peso | Driver | Valor |
|---|---|---|
| b0 | intercepto | −0.95 |
| w1 | reclamos | 2.4 |
| w2 | pagos atrasados | 1.9 |
| w3 | baja satisfacción | 2.0 |
| w4 | días sin uso | 1.5 |
| w5 | antigüedad | 1.6 |
| w6 | nº servicios | 1.1 |
| w7 | contrato mensual | 0.9 |
| sigma | ruido | 0.40 |

> Estos pesos hacen que el churn dependa de **varios** factores con peso comparable: ningún driver lo determina solo, y el ruido evita una regla perfecta.

**Resultados verificados (N = 2.500, semilla 42):**
- Tasa de abandono: **32,7 %** (rango objetivo 20–35 %). Línea base: 67,2 %.
- Coherencia perfil ↔ vista `comportamiento_cliente`: 0 filas incoherentes; 0 nulos en obligatorias.
- Árbol de decisión (balanced): Accuracy **69,4 %** (supera línea base), Recall churn **68,9 %**, F1 59,6 %.
- Regresión logística (balanced): Accuracy 73,4 %, Recall 68,3 %, F1 62,7 %.
- Ninguna variable sola separa las clases (sin regla rígida).

---

## 4. Controles de calidad (antes de cargar)

- **Balance de clases:** tasa de `abandono` objetivo **20 %–35 %**. Si cae fuera, ajustar `b0`.
- **Verificar señal:** correlación esperada — reclamos↑, morosidad↑, días sin uso↑, satisfacción↓ y antigüedad↓ asociados a mayor churn.
- **Sin reglas perfectas:** ninguna variable sola debe separar las clases (revisar que no haya un umbral que prediga churn con ~100 % exactitud).
- **Sin nulos** en columnas obligatorias; rangos válidos (satisfaccion 1–5, edad 18–100, no negativos).
- **`id_cliente` único.**

---

## 5. Expansión al modelo relacional (Spec 01)

El perfil plano se genera primero; luego se expande a las tablas normalizadas para mantener consistencia con los agregados:

1. **clientes** ← atributos del perfil (incl. `abandono`, `satisfaccion`, `dias_sin_uso`, `id_sucursal` por mapeo de ciudad, `segmento`).
2. **servicios** ← catálogo fijo (5 planes).
3. **contratos** ← `cantidad_servicios` filas por cliente; el contrato principal define `plan`; `monto_mensual` = Σ cargos; `tipo_contrato` del perfil.
4. **facturas** ← ~6 períodos recientes por cliente.
5. **pagos** ← un pago por factura; marcar `pagos_atrasados` como `atrasado` con `dias_atraso` > 0.
6. **reclamos** ← `reclamos_ultimos_6_meses` filas por cliente, con fecha en los últimos 6 meses.
7. **interacciones** ← 0–N por cliente (correlacionadas con reclamos).

> Así, los agregados de la vista `comportamiento_cliente` (conteos de reclamos/pagos, Σ monto, nº servicios) **reproducen exactamente** el perfil plano original. Verificable con un test que compare perfil vs. agregado.

---

## 6. Salida y pruebas

- **Salida:** registros insertados en `data/conectamax.db` (todas las tablas) + opción de exportar `data/clientes_generados.csv` (formato del contrato de Roberto, para que su app lo pueda cargar tal cual).
- **Pruebas (`tests/test_generate_data.py`):**
  - N ≥ 2.000 y `id_cliente` único.
  - Tasa de `abandono` en 20–35 %.
  - Columnas y dominios = `settings.py`.
  - Coherencia perfil ↔ agregados de `comportamiento_cliente`.
  - Reproducibilidad con semilla fija.

---

## 7. Decisiones pendientes de confirmar con Roberto
1. ¿N = 2.500 o ceñirse a 2.000?
2. ¿Pesos de los drivers (sección 3) y tasa objetivo de churn (20–35 %)?
3. ¿Exportar también `clientes_generados.csv` para mantener compatibilidad con la carga actual por CSV?
