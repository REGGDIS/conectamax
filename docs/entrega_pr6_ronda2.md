# Entrega PR #6 — ronda 2

## Comentario para GitHub (versión corta)

Listo @Roberto, resueltos los tres bloqueantes y de paso los tres no bloqueantes 👇

**Bloqueantes**
1. `--reset` ahora limpia solo datos operacionales y **conserva** `predicciones`. Borrar el historial es explícito: `--reset-predicciones`. Uso `defer_foreign_keys` + transacción explícita; si quedarían huérfanas, el commit falla con mensaje claro. Probado: conserva con mismo N, falla con N menor sin tocar el historial, y borra con el flag.
2. Vista `comportamiento_cliente`: ventana de 6 meses acotada a `[fecha_ref − 6m, fecha_ref]` (reclamos y pagos). Test confirma que no cuenta registros futuros.
3. El generador valida antes del commit que cada cliente tenga **exactamente** un contrato principal activo (rollback si no). Cubierto por `test_exactamente_un_principal_por_cliente`.

**No bloqueantes**
- Segmento `Clientes en Riesgo` → `Clientes Premium`.
- `train.py` con lista explícita `FEATURES` (12 vars) + validación de columnas.
- `prediccion.py`: caché invalidada por `mtime` de BD y modelo.

Suite: 38 tests en verde. Flujo `generate → train → registrar` corrido; el árbol supera la línea base (acc 0.696 vs 0.672). Detalle completo en `docs/respuesta_pr6_ronda2.md`. ¡Cuando puedas corres el flujo y me dices!

---

## Commit

```
fix(datos): separar --reset de borrado de predicciones, acotar ventana 6m y validar contrato principal

- --reset conserva predicciones; --reset-predicciones borra el historial (defer_foreign_keys + txn explicita)
- vista comportamiento_cliente: limite superior = fecha de referencia (reclamos y pagos)
- generador valida exactamente un contrato principal activo por cliente (+ test)
- no bloqueantes: segmento renombrado, FEATURES explicitas en train, cache invalidada por mtime
- specs 01/02/04/05 actualizadas (SDD)
```

Branch sugerido: `fix/revision-pr6-ronda2`

---

## Checklist antes del push

- [ ] `python -m pytest -q` en verde (38 passed).
- [ ] `python scripts/generate_data.py --reset` regenera sin borrar predicciones.
- [ ] `python scripts/train.py` imprime las 12 features y supera la línea base.
- [ ] `python scripts/registrar_predicciones.py` registra sin error.
- [ ] Revisar el diff: solo `scripts/`, `database/schema.sql`, `views/prediccion.py`, `tests/`, `docs/specs/`.
- [ ] No subir `data/conectamax.db` ni `models/*.pkl` (que estén en `.gitignore`).
- [ ] `git add -A && git commit` con el mensaje de arriba.
- [ ] `git push` y dejar el comentario en el PR #6.
