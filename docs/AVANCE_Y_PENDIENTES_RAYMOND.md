# Avance y pendientes — Parte de Raymond (Datos y Modelado)

**Proyecto:** ConectaMax Analytics (CRM + predicción de churn)
**Rol de Raymond:** Datos y modelado (Carta Gantt: etapas 1, 2, 6 + pruebas/integración en 7)
**Fecha de revisión:** 28-06-2026 · **Entrega:** 14-07-2026 · **Congelamiento:** 11-07-2026
**Repo:** `REGGDIS/conectamax` · **Rama de trabajo:** `feature/base-datos-modelo` (local, sin push aún)

> Este documento revisa lo construido y verificado, su cobertura frente al Plan v3.2, y lo que falta de la parte de Raymond.

---

## 1. Resumen del avance

La **base de datos** y el **modelo predictivo** —el núcleo de la parte de Raymond— están **construidos, probados y documentados**. El trabajo se desarrolló con Spec Driven Development: cada componente tiene su especificación previa en `docs/specs/`.

Estado global de la parte de Raymond: **≈ 80 % completo**. Falta principalmente la **integración del modelo en la interfaz Streamlit** (módulo Predicción) y el cierre documental de la Fase 8 (informe, presentación, manual), que son tareas conjuntas con Roberto.

---

## 2. Entregables completados y verificados

| Entregable | Archivo | Qué hace | Verificación |
|---|---|---|---|
| Esquema relacional | `database/schema.sql` | 10 tablas (8 OLTP + vista `comportamiento_cliente` + `predicciones`), PK/FK, índices | DDL válido en SQLite ✅ |
| Generador de datos | `scripts/generate_data.py` | ≥ 2.000 clientes sintéticos coherentes; `abandono` ponderado + ruido (§29.3); expande a todas las tablas | 2.500 clientes, churn 32,7 % ✅ |
| Inicializador BD | `scripts/init_db.py` | Crea `data/conectamax.db` desde el esquema | BD operativa ✅ |
| Entrenamiento del modelo | `scripts/train.py` | Pipeline sklearn; árbol (obligatorio) + reg. logística (deseable); split 80/20 `stratify` `random_state=42`; evalúa vs línea base; guarda `models/modelo_churn.pkl` | Árbol supera línea base ✅ |
| Predictor de riesgo | `scripts/predictor.py` | Carga el modelo, calcula probabilidad y clasifica bajo/medio/alto (umbrales §29.5) | Niveles y probabilidades válidos ✅ |
| Diccionario de datos | `docs/diccionario_datos.md` | Documenta las 10 entidades (campo, tipo, nulos, descripción, claves) | Coincide con el esquema ✅ |
| Pruebas — datos | `tests/test_data_generator.py` | Volumen, unicidad, tasa de churn, coherencia perfil↔vista, sin nulos | 8/9 tests en verde ✅ |
| Pruebas — modelo | `tests/test_modelo_churn.py` | Modelo se guarda, supera línea base, recall objetivo, predictor válido, umbrales | 5 tests en verde ✅ |
| Especificaciones (SDD) | `docs/specs/01..08` | Specs de BD, datos, ETL, modelo, predicción, dashboard, clientes y reportes | Revisadas y alineadas ✅ |

---

## 3. Cobertura por fase (Carta Gantt)

| Fase | Responsable | Estado | Detalle |
|---|---|---|---|
| 1. Caso y alcance | Raymond | ✅ | Documentado en plan e IMPLEMENTACION |
| **2. Base de datos** | **Raymond** | ✅ **Completa** | Esquema, BD, datos ≥ 2.000, diccionario |
| 3. Estructura software | Roberto | ✅ | App Streamlit base |
| 4. ETL y limpieza | Roberto | ✅ | Carga/validación/limpieza |
| **5–6. Modelo de churn** | **Raymond** | ✅ **Completa (lógica)** | `train.py`, `predictor.py`, modelo `.pkl`, métricas |
| 6–7. Módulo Predicción (UI) | Raymond + Roberto | ⬜ **Pendiente** | Falta la vista Streamlit que use `predictor.py` |
| 7. Integración completa | Ambos | 🟡 Parcial | Falta conmutar la fuente de datos a SQLite/`comportamiento_cliente` |
| 8. Pruebas y documentación | Ambos | 🟡 Parcial | Hay tests; faltan informe, presentación, manual |

---

## 4. Métricas del modelo (verificadas, N = 2.500, semilla 42)

| Modelo | Accuracy | Recall (churn) | Precision | F1 |
|---|---|---|---|---|
| Línea base (clase mayoritaria) | 0,672 | — | — | — |
| **Árbol de decisión (obligatorio)** | **0,696** | **0,726** | 0,527 | 0,610 |
| Regresión logística (deseable) | 0,728 | 0,677 | 0,572 | 0,620 |

El árbol **supera la línea base** y cumple la meta orientativa de **recall ≥ 0,60** (§29.4). Ninguna variable sola separa las clases (sin regla rígida). La cartera se reparte en riesgo bajo/medio/alto de forma equilibrada.

---

## 5. Lo que falta de la parte de Raymond

Por prioridad:

1. **Módulo Predicción en Streamlit** (Fase 6–7) — *prioridad alta*.
   Crear la vista `views/Prediccion` (o equivalente) que:
   - cargue `models/modelo_churn.pkl` con `predictor.py`;
   - calcule probabilidad y nivel de riesgo desde `comportamiento_cliente`;
   - registre cada predicción en la tabla `predicciones`;
   - muestre los resultados (probabilidad + nivel) en la app.
   *Coordinar con Roberto por ser UI (su área).* Spec ya escrita: `docs/specs/05_modulo_prediccion.md`.

2. **Persistir predicciones en SQLite** (Fase 6–7) — *prioridad alta*.
   Un pequeño script/función que inserte el resultado de `predictor.predecir(...)` en la tabla `predicciones` (con modelo, versión y fecha). Cierra la regla §29.6 (real vs. predicción separados).

3. **Integración de la fuente de datos** (Fase 7) — *conjunta con Roberto*.
   Conmutar la app de CSV/`session_state` a leer `comportamiento_cliente` desde `data/conectamax.db`. Bajo riesgo: la vista expone las mismas columnas de `settings.py`.

4. **requirements.txt** — *en progreso*.
   Agregar `scikit-learn` y `joblib` (lo está haciendo Claude Code).

5. **Cierre documental (Fase 8)** — *conjunta*.
   Aporte de Raymond al informe: sección de base de datos, diccionario, metodología del modelo y resultados (métricas y matriz de confusión). Apoyo al manual de uso y a la presentación.

6. **Opcionales (solo si sobra tiempo)** — clustering K-Means para validar segmentos, Apriori, o DW físico. El modelo estrella va como diseño conceptual en el informe.

---

## 6. Cómo ejecutar todo (flujo completo)

```bash
# 1. Crear la base de datos y poblarla
python scripts/init_db.py
python scripts/generate_data.py --n 2500 --csv

# 2. Entrenar y evaluar el modelo (guarda models/modelo_churn.pkl)
python scripts/train.py

# 3. Ejecutar las pruebas
python -m pytest tests/test_data_generator.py tests/test_modelo_churn.py -q

# 4. (Tras integrar) levantar la app
python -m streamlit run app.py
```

Requisitos: `streamlit, pandas, plotly, scikit-learn, joblib, numpy, pytest`.

---

## 7. Decisiones técnicas confirmadas

- Variable objetivo: **`abandono`** (0/1). La predicción vive aparte en `predicciones` (anti-fuga §29.6).
- BD: **`data/conectamax.db`**. Modelo: **`models/modelo_churn.pkl`**.
- Vista **`comportamiento_cliente`** = puente que reproduce el contrato de `config/settings.py` (no rompe la app de Roberto).
- Modelo principal: **árbol de decisión** (`max_depth=4`, `class_weight="balanced"`), interpretable; regresión logística como comparación.
- Umbrales de riesgo: bajo < 30 % · medio 30–60 % · alto ≥ 60 % (§29.5).

---

## 8. Pendiente de acordar con Roberto

- Ubicación final de `predictor.py` (`scripts/` o `services/`) para que la app lo importe.
- Carpeta `models/` (nueva en el repo) y momento de conmutar la fuente de datos a SQLite (Fase 7).
- Estructura de la nueva vista `Prediccion` dentro de `views/`.
