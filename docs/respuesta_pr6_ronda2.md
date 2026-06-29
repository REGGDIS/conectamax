# Respuesta a la revisión — PR #6 (ronda 2)

Hola Roberto, gracias por la revisión. Apliqué los tres ajustes bloqueantes y, de paso, las tres observaciones no bloqueantes. Resumo punto por punto.

## Bloqueantes

**1. `--reset` ya no borra el historial de `predicciones`.**
`--reset` ahora limpia **solo** los datos operacionales/sintéticos (catálogo + `clientes` y sus tablas hijas) y conserva `predicciones`. El borrado del historial pasó a ser una acción separada y explícita: `--reset-predicciones`. Como `predicciones` referencia `clientes` por FK, durante el reset uso `PRAGMA defer_foreign_keys = ON` dentro de una transacción explícita (`BEGIN`/`COMMIT`), de modo que la integridad referencial se valida en el commit. Si se regenera con un `N` que dejaría predicciones huérfanas, el commit falla con un mensaje claro pidiendo `--reset-predicciones`.

Verificado de punta a punta:
- `--reset` con el mismo N → conserva las 2.500 predicciones.
- `--reset` con N menor (huérfanas) → falla sin tocar el historial, con mensaje explicativo.
- `--reset --reset-predicciones` → borra el historial.

**2. Ventana de "últimos 6 meses" acotada por arriba.**
Los agregados `reclamos_ultimos_6_meses` y `pagos_atrasados` de la vista `comportamiento_cliente` ahora se restringen al intervalo `[fecha_referencia − 6 meses, fecha_referencia]` (antes solo tenían cota inferior). Agregué `AND fecha <= fecha_referencia` en ambos subselects. Test nuevo confirma que un registro posterior a la fecha de referencia no se cuenta.

**3. Validación de "exactamente un contrato principal activo por cliente".**
Como SQLite no permite exigir "al menos uno" con un `CHECK` entre tablas, el generador valida antes del commit que cada cliente tenga exactamente un contrato con `es_principal = 1 AND estado = 'activo'`, y hace `ROLLBACK` si no se cumple. El índice único parcial se mantiene como salvaguarda de unicidad. Cubierto por `test_exactamente_un_principal_por_cliente`.

## No bloqueantes

- **Segmento "Clientes en Riesgo":** renombrado a `Clientes Premium` para que el nombre no sugiera el target (ya estaba excluido de las features del modelo).
- **Variables predictoras:** `train.py` ahora declara una lista explícita `FEATURES` (12 variables) en vez de derivarlas por descarte, con validación de columnas requeridas.
- **Invalidación de caché:** `views/prediccion.py` usa el `mtime` de la BD y del modelo como clave de `@st.cache_data`; si cambia cualquiera, las predicciones se recalculan.

## Verificación

- Suite completa: **38 pruebas en verde** (los *skips* son specs aún pendientes, sin relación con estos cambios).
- Flujo completo ejecutado: `generate_data → train → registrar_predicciones`. El árbol supera la línea base (accuracy 0.696 vs 0.672; recall churn 0.726).

## Nota técnica

Por el `defer_foreign_keys`, `poblar()` pasó a manejar la transacción de forma explícita (`isolation_level = None` + `BEGIN`/`COMMIT`/`ROLLBACK`), porque `executescript()` hace un commit implícito que apagaba el pragma antes de los `DELETE`.

Las especificaciones afectadas (`docs/specs/01, 02, 04, 05`) quedaron actualizadas con estos acuerdos. Cuando puedas, corre el flujo completo y me avisas si queda algo.
