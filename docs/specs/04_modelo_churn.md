# Spec 04 — Modelo predictivo de churn

**Estado:** Pendiente de implementación
**Fase:** 5 (Carta Gantt) · **Responsable:** Raymond
**Depende de:** Spec 01, Spec 02, Spec 03 (dataset preparado / vista analítica)
**Referencia plan:** Plan v3.2 §29 · RF7 (parcial)

---

## Objetivo

Entrenar, evaluar y persistir un modelo de clasificación que estime la probabilidad de abandono (`abandono = 1`) a partir de variables de comportamiento del cliente, superando una línea base simple y cumpliendo las reglas anti-fuga del plan.

## Alcance

**Incluye:**

- Entrenamiento con scikit-learn (`Pipeline` con preprocesamiento + clasificador).
- Árbol de decisión (obligatorio).
- Regresión logística (deseable, comparación de métricas).
- Split train/test 80/20, `stratify=y`, `random_state=42`.
- Evaluación: matriz de confusión, Accuracy, Recall, Precision, F1.
- Comparación contra línea base (clase mayoritaria).
- Persistencia con joblib en `models/modelo_churn.pkl`.
- Scripts: `scripts/train.py` (o `ml/train.py` según estructura acordada), `services/predictor.py` o equivalente.

**Excluye:**

- AutoML, redes neuronales, despliegue en producción.
- Usar probabilidad o nivel de riesgo como variables de entrada.
- Entrenar con el conjunto de prueba o ajustar preprocesamiento con test.

## Requisitos funcionales

| ID | Requisito |
|---|---|
| RF7.1 | El modelo se entrena desde la vista `comportamiento_cliente` (sin columnas de predicción). |
| RF7.2 | Target = columna `abandono` (INTEGER 0/1). |
| RF7.3 | Features: satisfacción, reclamos, pagos atrasados, antigüedad, días sin uso, plan/contrato codificados, etc. |
| RF7.4 | El modelo entrenado se guarda en `models/modelo_churn.pkl`. |
| RF7.5 | Se reportan métricas en consola o archivo de log comparando con línea base. |
| RF7.6 | *(Deseable)* Segundo modelo (regresión logística) con tabla comparativa. |

## Requisitos no funcionales

- Reproducibilidad total con `random_state=42`.
- Preprocesamiento encapsulado en `Pipeline` (fit solo en train).
- Tiempo de entrenamiento razonable en laptop (< 2 min con N ≈ 2.500).
- Dependencias ya presentes en `requirements.txt` (scikit-learn, joblib, pandas).

## Entradas

| Entrada | Origen | Formato |
|---|---|---|
| Dataset analítico | Vista `comportamiento_cliente` | SQLite / pandas |
| Contrato de columnas | `config/settings.py` | Exclusión de ID, nombre, target |
| Hiperparámetros mínimos | Spec / plan §29 | Documentados en código |

## Salidas

| Salida | Destino | Formato |
|---|---|---|
| Modelo entrenado | `models/modelo_churn.pkl` | joblib |
| Métricas de evaluación | stdout / `reports/` | Texto o JSON |
| *(Opcional)* Importancias / coeficientes | Informe final | Tabla |

## Criterios de aceptación

- [ ] Split 80/20 estratificado verificado en código.
- [ ] Accuracy del modelo supera la línea base (clase mayoritaria).
- [ ] Recall de la clase churn (`abandono=1`) reportado explícitamente.
- [ ] Archivo `.pkl` se carga con joblib sin error.
- [ ] Ninguna columna de `predicciones` usada como feature.
- [ ] Tests en `tests/test_churn_model.py` pasan.

## Dependencias

- Spec 01 — tabla `predicciones` (solo escritura posterior, no entrenamiento).
- Spec 02 — datos con señal de churn (tasa 20–35 %).
- Spec 05 — consumo del modelo en módulo Predicción.

## Notas técnicas

Metas orientativas del plan: Accuracy ≥ 0,80 y Recall ≥ 0,60; criterio principal = superar línea base con explicación honesta.

Features candidatas (confirmar en implementación):

- `satisfaccion`, `reclamos_ultimos_6_meses`, `pagos_atrasados`, `antiguedad_meses`, `dias_sin_uso`, `monto_mensual`, `cantidad_servicios`, `tipo_contrato`, `plan` (codificado).

Excluir: `id_cliente`, `nombre`, `abandono`, `region`, `segmento` (opcional según decisión documentada).
