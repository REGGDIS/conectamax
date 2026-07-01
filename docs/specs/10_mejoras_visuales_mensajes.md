# Spec 10 — Mejoras visuales y mensajes

**Estado:** Borrador
**Fase:** 8 (Carta Gantt, post-integración) · **Responsable:** Raymond
**Depende de:** Spec 09 (integración Streamlit) — todos los módulos deben estar ya integrados y funcionando
**Referencia:** Plan de trabajo enviado por Roberto — "Mejoras visuales y mensajes de ConectaMax" (2026-06-30)
**Repo:** `REGGDIS/conectamax` · **Rama:** `feature/mejoras-visuales-mensajes`

---

## Objetivo

Mejorar la apariencia y los mensajes de toda la aplicación ConectaMax para que su uso sea más claro, consistente y profesional, **sin alterar la lógica funcional ya validada** (base de datos, modelo de churn, contratos de datos).

## Alcance

**Incluye:**

- Unificar títulos, subtítulos, textos de ayuda, botones, filtros, tablas, gráficos y tarjetas KPI en los 6 módulos: Inicio, Carga de datos, Clientes, Dashboard, Análisis, Predicción.
- Mejorar mensajes de información, éxito, advertencia y error (`st.info`, `st.success`, `st.warning`, `st.error`).
- Agregar estados vacíos y orientaciones cuando no existan datos disponibles.
- Usar componentes nativos de Streamlit; evitar CSS complejo.

**Excluye (límites duros, no negociables):**

- No modificar el esquema de la base de datos (`database/schema.sql`, tablas, vista `comportamiento_cliente`).
- No cambiar el modelo de churn: variables, features, umbrales de riesgo (§29.5), métricas.
- No alterar firmas de funciones, contratos de datos (`config/settings.py`) ni lógica de negocio, salvo cambio mínimo indispensable para mostrar un mensaje (p. ej. envolver una llamada existente en un `try/except` para mostrar un error legible).
- No agregar autenticación, roles, despliegue, tiempo real ni funcionalidades de negocio nuevas.

## Principio rector

Es un cambio de **presentación**, no de **comportamiento**. Toda funcionalidad que hoy pasa las pruebas debe seguir pasando exactamente igual después de este trabajo. Si un cambio visual requiere tocar lógica, se detiene y se pregunta antes de continuar (regla del proyecto: "si existen dudas, preguntar antes de implementar").

## Requisitos funcionales

| ID | Requisito | Módulo |
|---|---|---|
| RF10.1 | Título, explicación breve, controles y resultados en orden consistente en cada pantalla. | Todos |
| RF10.2 | Mensajes de error/advertencia/éxito explican qué ocurrió, por qué, y qué debe hacer el usuario (no "Error" a secas). | Todos |
| RF10.3 | Estados vacíos (sin datos, sin coincidencias) indican la causa y el siguiente paso. | Todos |
| RF10.4 | Acciones sensibles (reemplazar, borrar, registrar) muestran advertencia o confirmación antes de ejecutarse. | Clientes, Predicción |
| RF10.5 | Inicio describe el propósito de ConectaMax, resume módulos disponibles y orienta por dónde empezar. | Inicio |
| RF10.6 | Carga de datos explica el formato CSV esperado antes de cargar, y diferencia archivo vacío / extensión incorrecta / columnas faltantes / datos inválidos. | Carga de datos |
| RF10.7 | Carga de datos muestra nombre de archivo, filas y columnas tras una carga correcta, con indicador de procesamiento durante validación/limpieza. | Carga de datos |
| RF10.8 | Clientes agrupa buscador/filtros/orden con claridad, muestra cantidad de resultados y mensaje orientador si no hay coincidencias. | Clientes |
| RF10.9 | Dashboard uniforma tarjetas KPI y títulos de gráficos, con nombres legibles en ejes/leyendas y colores coherentes por categoría/estado. | Dashboard |
| RF10.10 | Análisis separa claramente datos originales, limpieza, calidad de datos y variables derivadas, con lenguaje directo y advertencias si no hay datos. | Análisis |
| RF10.11 | Predicción mantiene visible que usa SQLite (no el CSV cargado manualmente), explica probabilidad/niveles de riesgo, y diferencia registrar historial vs. reemplazar predicciones anteriores. | Predicción |
| RF10.12 | Predicción muestra mensajes claros cuando falte la base de datos, el modelo o los datos. | Predicción |

## Requisitos no funcionales

- Simplicidad académica: sin librerías nuevas de UI, solo `st.*` nativo y lo ya aprobado (Streamlit, Plotly).
- Backward compatibility: cero regresiones funcionales — las 141 pruebas actuales deben seguir en verde.
- Consistencia terminológica: mismos nombres de estado (bajo/medio/alto, CSV vs. SQLite) en todos los módulos.

## Criterios de aceptación

- [ ] Todos los módulos conservan su funcionamiento actual (141 pruebas siguen pasando).
- [ ] Apariencia coherente entre las 6 pantallas.
- [ ] No quedan mensajes genéricos tipo "Error" sin explicación ni próximo paso.
- [ ] Los estados sin datos orientan al usuario sobre qué hacer.
- [ ] Las acciones sensibles muestran advertencia o confirmación.
- [ ] Los textos distinguen correctamente CSV vs. SQLite donde corresponde.
- [ ] La app arranca sin errores en terminal tras los cambios.
- [ ] El PR incluye resumen de cambios y resultado de pruebas.

## Plan de implementación incremental

Regla del proyecto: evitar trabajar en varios módulos a la vez. Se implementa **un módulo por commit/sesión**, en este orden (de menor a mayor riesgo/complejidad), corriendo `pytest` después de cada uno:

1. **Base común** — definir en un solo lugar (p. ej. `scripts/ui_helpers.py` o convención de uso directo de `st.info/success/warning/error`) el patrón de mensajes: qué pasó, por qué, qué hacer. Sin esto, los módulos 2–7 se implementan sin criterio unificado.
2. **Inicio** — módulo piloto, menor riesgo (no toca datos ni BD).
3. **Carga de datos**
4. **Clientes**
5. **Dashboard**
6. **Análisis**
7. **Predicción** — mayor riesgo (toca acciones sensibles: registrar/reemplazar predicciones).
8. **Cierre** — revisión de consistencia cruzada entre los 6 módulos, pruebas manuales de navegación/filtros/descargas, PR.

## Dependencias

- Spec 09 — Integración Streamlit (todos los módulos deben estar ya integrados).
- Archivos: `app.py`, `views/*.py`, `services/*.py` (de Roberto), `scripts/predictor.py`, `scripts/registrar_predicciones.py` (de Raymond).

## Notas técnicas

- Trabajar en rama `feature/mejoras-visuales-mensajes` sobre `main` (post PR #6 y #7).
- No versionar `data/*.db`, `models/`, entorno virtual (ya cubierto por `.gitignore` existente).
- Ejecutar pruebas automatizadas antes de cada PR de revisión; probar manualmente navegación, filtros, descargas y registro de predicciones.
