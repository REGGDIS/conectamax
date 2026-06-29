# Spec 09 — Integración del modelo en Streamlit (Fase 7)

**Estado:** Borrador implementado (vista + servicio) · wire-up pendiente con Roberto
**Fase:** 7 (Carta Gantt) · **Responsable:** Raymond + Roberto
**Depende de:** Spec 01 (vista + tabla `predicciones`), Spec 04 (modelo), Spec 05 (predictor)
**Referencia plan:** Plan v3.2 §18, §29.5, §29.6 · RF7, RF8

---

## Objetivo

Conectar el modelo de churn ya entrenado con la aplicación Streamlit de Roberto, **sin romper nada de lo existente**: agregar el módulo **Predicción** que muestra probabilidad y nivel de riesgo por cliente, y registrar los resultados en la tabla `predicciones`.

## Principio rector

La app de Roberto consume un DataFrame con las columnas de `config/settings.py`. El modelo consume **la misma forma de datos** a través de la vista `comportamiento_cliente`. Por eso la integración es de **bajo riesgo**: no se tocan validaciones, nombres ni módulos existentes; solo se **añade** una vista y, opcionalmente, se conmuta la fuente de datos a SQLite.

## Alcance

**Incluye:**

- Vista `views/prediccion.py` (borrador entregado): KPIs de riesgo, gráfico Plotly, tabla filtrable y botón para registrar predicciones.
- Servicio `scripts/registrar_predicciones.py` (probado): genera predicciones desde la vista analítica y las inserta en `predicciones`.
- Conmutación de la fuente de datos de la app: de CSV/`session_state` a la vista `comportamiento_cliente` en SQLite (opcional pero recomendada).

**Excluye:**

- Reentrenamiento desde la UI.
- Campañas automáticas de retención.
- API REST / despliegue.

## Requisitos funcionales

| ID | Requisito |
|---|---|
| RF7.7 | La vista carga `models/modelo_churn.pkl` al abrirse; si no existe, muestra aviso para ejecutar `train.py`. |
| RF7.8 | Calcula y muestra `probabilidad_churn` (0.0–1.0) por cliente desde `comportamiento_cliente`. |
| RF8.1 | Clasifica en bajo/medio/alto según umbrales §29.5. |
| RF8.5 | Registra cada predicción en `predicciones` (modelo, versión, fecha) al pulsar el botón. |
| RF8.6 | Permite filtrar la tabla por nivel de riesgo. |
| RF7.9 | *(Recomendado)* La app lee la vista `comportamiento_cliente` desde `data/conectamax.db`. |

## Requisitos no funcionales

- **Anti-fuga (§29.6):** `probabilidad_churn` y `nivel_riesgo` NO entran a la vista analítica ni al modelo; viven solo en `predicciones`.
- Aviso claro si falta el modelo o la BD.
- Sin dependencias nuevas más allá de las ya aprobadas (streamlit, plotly, pandas, scikit-learn, joblib).

## Flujo de integración

```text
comportamiento_cliente (SQLite)
        │
        ▼
predictor.predecir()  ──►  probabilidad + nivel (umbrales §29.5)
        │
        ├──►  Vista Streamlit "Predicción"  (KPIs, gráfico, tabla)
        │
        └──►  registrar_predicciones.guardar()  ──►  tabla `predicciones`
                                                      (modelo, version, fecha)
```

## Contrato de wire-up con Roberto

1. **Navegación:** enganchar `views/prediccion.py::render()` donde hoy figura "Predicción" como pendiente en `app.py`.
2. **Ubicación de imports:** la vista importa `predictor.py` y `registrar_predicciones.py` desde `scripts/` (añade `scripts/` al `sys.path`). Si se prefiere, mover ambos a `services/` y ajustar el import.
3. **Carpeta `models/`:** nueva en el repo; el `.pkl` se genera con `train.py` y va ignorado por git.
4. **Fuente de datos (opcional, Fase 7):** cuando se conmute la app a SQLite, leer `SELECT * FROM comportamiento_cliente` en lugar del CSV; las columnas son idénticas a `settings.py`, así que el módulo Clientes y el Dashboard siguen funcionando igual.
5. **Ficha de cliente:** opcionalmente, mostrar en la ficha (módulo Clientes) la última predicción del cliente leyendo de `predicciones`.

## Entradas / Salidas

| Entrada | Origen |
|---|---|
| Modelo entrenado | `models/modelo_churn.pkl` |
| Datos analíticos | vista `comportamiento_cliente` (SQLite) |

| Salida | Destino |
|---|---|
| Probabilidad + nivel | UI Streamlit |
| Registro de predicciones | tabla `predicciones` (SQLite) |
| CSV de predicciones | descarga desde la UI |

## Pruebas (verificadas)

`tests/test_registrar_predicciones.py` (3 pruebas en verde):

- Se registran tantas predicciones como clientes.
- Probabilidades en [0,1] y niveles válidos.
- La vista analítica no contiene columnas de predicción (anti-fuga §29.6).

## Criterios de aceptación

- Abrir la app → módulo Predicción muestra KPIs, gráfico y tabla sin errores.
- El botón de registro inserta filas en `predicciones` con modelo/versión/fecha.
- Nada de lo previo de Roberto (Clientes, Carga, Dashboard, Análisis) se rompe.
