# Spec 05 — Módulo de predicción y clasificación de riesgo

**Estado:** Pendiente de implementación
**Fase:** 6–7 (Carta Gantt) · **Responsable:** Raymond (integración con Roberto)
**Depende de:** Spec 04 (modelo persistido), Spec 01 (tabla `predicciones`)
**Referencia plan:** Plan v3.2 §29.5–29.6 · RF7, RF8

---

## Objetivo

Exponer en la aplicación Streamlit la probabilidad de abandono por cliente y clasificarlo en nivel de riesgo **bajo, medio o alto**, registrando cada predicción en SQLite de forma separada del target real.

## Alcance

**Incluye:**

- Vista Streamlit `Predicción` / `Riesgo` (pendiente en repo).
- Carga del modelo `models/modelo_churn.pkl`.
- Inferencia por cliente o lote desde `comportamiento_cliente`.
- Clasificación por umbrales fijos (ajustables documentados).
- Inserción en tabla `predicciones`.
- Visualización de probabilidad y nivel en UI.

**Excluye:**

- Campañas automáticas de retención.
- Reentrenamiento online.
- API REST externa.

## Requisitos funcionales

| ID | Requisito |
|---|---|
| RF7.7 | La app carga el modelo persistido al abrir el módulo Predicción. |
| RF7.8 | Se muestra probabilidad de churn por cliente (0.0–1.0). |
| RF8.1 | Clasificación de riesgo según umbrales del plan. |
| RF8.2 | Riesgo **bajo** si probabilidad < 30 %. |
| RF8.3 | Riesgo **medio** si 30 % ≤ probabilidad < 60 %. |
| RF8.4 | Riesgo **alto** si probabilidad ≥ 60 %. |
| RF8.5 | Cada predicción se registra en `predicciones` (modelo, versión, fecha). |
| RF8.6 | Filtros por nivel de riesgo en listado de clientes (integración con módulo Clientes). |

## Requisitos no funcionales

- Tiempo de inferencia < 1 s para un cliente en hardware académico típico.
- Mensaje claro si el modelo `.pkl` no existe (indicar ejecutar entrenamiento).
- Umbrales aplicados de forma uniforme en app, informe y reportes.

## Entradas

| Entrada | Origen | Formato |
|---|---|---|
| Modelo entrenado | `models/modelo_churn.pkl` | joblib Pipeline |
| Perfil cliente | Vista `comportamiento_cliente` | SQLite / pandas |
| Umbrales | Spec 05 / plan §29.5 | Constantes en código |

## Salidas

| Salida | Destino | Formato |
|---|---|---|
| Probabilidad + riesgo | UI Streamlit | Texto / badges |
| Registro histórico | Tabla `predicciones` | SQLite |
| *(Opcional)* Export CSV riesgo | `reports/` | CSV |

## Criterios de aceptación

- [ ] Módulo Predicción accesible desde navegación principal.
- [ ] Probabilidades en rango [0, 1].
- [ ] Umbrales producen exactamente tres niveles de riesgo.
- [ ] Filas insertadas en `predicciones` con FK válida a `clientes`.
- [ ] `abandono` real no se muestra como input del modelo en UI de predicción.
- [ ] Tests de servicio de predicción pasan (`tests/test_services.py`).

## Dependencias

- Spec 04 — modelo entrenado y `predictor.py`.
- Spec 07 — listado/ficha de clientes (filtro por riesgo).
- Spec 06 — KPIs de riesgo en dashboard (integración deseable).

## Notas técnicas

Función de clasificación propuesta:

```python
def clasificar_riesgo(probabilidad: float) -> str:
    if probabilidad < 0.30:
        return "bajo"
    if probabilidad < 0.60:
        return "medio"
    return "alto"
```

Anti-fuga: la tabla `predicciones` es solo salida; nunca se hace JOIN de `probabilidad_churn` hacia el entrenamiento.
