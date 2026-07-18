# IMPLEMENTACION_IA.md

Documentación técnica de la ampliación del módulo de IA de SIGPDA: comparación científica de 5 modelos, validación cruzada temporal, optimización de hiperparámetros, pruebas estadísticas, persistencia de modelos y reportes de experimentación. Complementa a `README.md`.

---

## 1. Lo que ya existía (auditado antes de empezar)

- Backend FastAPI con ~20 routers, autenticación JWT, SQLAlchemy + SQLite.
- Frontend React + TypeScript (Vite, Tailwind, **Recharts** ya presente).
- `ia/predictor.py`: dataset histórico, features, modelos clásicos (Random Forest, Regresión Lineal, Árbol de Decisión) y `HybridTransformerModel` (Multi-Head Self-Attention en NumPy + ensemble RF/GBR/LR/DT + meta-learner Ridge).
- `ia/comparador_modelos.py`: comparación ARIMA / Prophet / Transformer Híbrido (3 modelos), split cronológico 80/20, métricas MAE/RMSE/MAPE/R², prueba Diebold-Mariano.
- Endpoints `/api/ia/predecir`, `/api/ia/comparar-modelos`, `/api/ia/historial`, `/api/ia/platos-disponibles`.
- Tablas `Prediccion` y `ComparacionModelos` (columnas fijas por modelo).
- **Hallazgo crítico confirmado en la auditoría**: la capa de atención (`MultiHeadSelfAttention`) usa pesos `W_Q/W_K/W_V/W_O` generados aleatoriamente y **nunca actualizados por retropropagación** — es una proyección aleatoria fija, no un Transformer entrenado end-to-end.
- Sin EDA, sin validación cruzada, sin tuning registrado, sin Holt-Winters, sin Friedman/Wilcoxon, sin SMAPE, sin persistencia de modelos, sin reportes de IA específicos, sin `pytest` instalado.

## 2. Lo que se corrigió

- **Duplicación de lógica**: la construcción de la serie diaria continua, ARIMA, Prophet y las métricas estaban implementadas únicamente dentro de `comparador_modelos.py`. Se centralizaron en módulos dedicados (`data_preparation.py`, `modelos_clasicos.py`, `metricas.py`, `pruebas_estadisticas.py`) y `comparador_modelos.py` ahora las **reutiliza** (verificado con pruebas de identidad de función: `comparador.entrenar_evaluar_arima is modelos_clasicos.entrenar_evaluar_arima`, etc.). El comportamiento numérico de `/comparar-modelos` es idéntico al original (verificado end-to-end).
- **Falso positivo de "duplicados" en el EDA**: la primera versión de la detección de duplicados usaba `(fecha, cantidad, categoria, precio)` como clave, lo que marcaba como "duplicadas" ventas legítimas distintas del mismo día con la misma cantidad (muy común con cantidades pequeñas y precio fijo de carta) — llegó a reportar 93 de 153 filas como duplicadas en datos reales. Se corrigió usando `(id_venta, id_plato)` como clave real de duplicado (el mismo plato facturado dos veces en la misma venta), bajando a un 4-7% razonable y evitando que `limpiar_y_validar` borrara ventas reales.
- **Bug de persistencia**: `ResultadoFold` tiene columnas `Date` en SQLAlchemy, pero `ia.validacion.evaluar_modelo_cv` genera fechas como strings ISO (`.isoformat()`). La primera versión de `persistencia_bd.guardar_ejecucion_comparacion` intentaba insertar esos strings directamente, y SQLite/SQLAlchemy lanzaba `TypeError: SQLite Date type only accepts Python date objects`. Se corrigió con un conversor `_a_fecha()` y se añadió una prueba de regresión específica.
- El Transformer sigue **sin ser un Transformer entrenado por backpropagación** (ver sección 9, decisión técnica deliberada).

## 3. Lo que se añadió

- **EDA** completo por plato (estadísticas descriptivas, outliers vía IQR, distribución, estacionalidad, correlaciones, calidad de datos).
- **Pipeline de preparación de datos centralizado**, con lags y medias móviles construidos exclusivamente con `shift(1)` antes de cualquier `rolling` (sin fuga de información, verificado con pruebas).
- **Holt-Winters** como tercer modelo clásico.
- **Transformer+Random Forest** y **Transformer+Gradient Boosting** como modelos híbridos independientes (cada uno con un único regresor sobre las features "atendidas"), distintos del `HybridTransformerModel` original (ensemble de 4 modelos), que se conserva intacto solo por compatibilidad con `/predecir`.
- **SMAPE** añadido a las métricas (con manejo explícito de ceros, sin división por cero).
- **Validación cruzada temporal walk-forward** (`TimeSeriesSplit`, hasta 5 folds), con reducción automática y advertencia si no hay datos suficientes.
- **Optimización de hiperparámetros** sin Optuna: `RandomizedSearchCV` + `TimeSeriesSplit` para los regresores sklearn de los modelos híbridos, y una búsqueda aleatoria temporal propia (split train/val cronológico, sin k-fold aleatorio) para ARIMA/Prophet/Holt-Winters.
- **Pruebas de Friedman** (comparación simultánea de los 5 modelos) y **Wilcoxon** (ganador vs. cada competidor, con corrección Holm-Bonferroni), además del Diebold-Mariano ya existente.
- **Registro de modelos** (`ia/model_registry.py`): guardar/cargar/predecir sin reentrenar, con escritura atómica (archivo temporal + `os.replace`), detección de si el dataset cambió desde el entrenamiento (hash ligero) y protección contra path traversal (la ruta se deriva exclusivamente de `int(id_plato)`).
- **5 tablas normalizadas** en la base de datos para el historial de comparaciones de 5 modelos.
- **Endpoint unificado** `POST /ia/entrenar-comparar` que orquesta todo lo anterior.
- **Reportes de IA en PDF, Word y Excel** de una ejecución ya persistida.
- Componentes React nuevos (`EdaPanel`, `EntrenamientoCompleto`, `ModeloGuardadoPanel`) integrados en `IA.tsx` sin reescribirla.
- 161 pruebas automatizadas nuevas (`pytest`, antes no había ninguna).

## 4. Archivos nuevos

**Backend / IA:**
`ia/data_preparation.py`, `ia/eda.py`, `ia/modelos_clasicos.py`, `ia/modelos_hibridos.py`, `ia/comparacion_completa.py`, `ia/validacion.py`, `ia/tuning.py`, `ia/metricas.py`, `ia/pruebas_estadisticas.py`, `ia/orquestador.py`, `ia/model_registry.py`, `ia/persistencia_bd.py`, `ia/reportes_ia.py`

**Frontend:**
`frontend/src/types/ia.ts`, `frontend/src/components/ia/EdaPanel.tsx`, `frontend/src/components/ia/EntrenamientoCompleto.tsx`, `frontend/src/components/ia/ModeloGuardadoPanel.tsx`

**Pruebas:**
`conftest.py` (raíz), `tests/__init__.py`, `tests/test_data_preparation.py`, `tests/test_eda.py`, `tests/test_comparador_modelos.py`, `tests/test_modelos_clasicos.py`, `tests/test_modelos_hibridos.py`, `tests/test_metricas.py`, `tests/test_validacion.py`, `tests/test_tuning.py`, `tests/test_pruebas_estadisticas.py`, `tests/test_model_registry.py`, `tests/test_comparacion_completa.py`, `tests/test_database_ia.py`, `tests/test_orquestador.py`, `tests/test_reportes_ia.py`, `tests/test_endpoints_ia.py`

**Otros:**
`models/.gitkeep` (carpeta de artefactos de modelos guardados), `IMPLEMENTACION_IA.md`

## 5. Archivos modificados

- `ia/comparador_modelos.py` — se quitó la lógica duplicada (ARIMA, Prophet, serie diaria, métricas, Diebold-Mariano) reemplazándola por imports de los módulos centralizados. `comparar_modelos_prediccion()` (3 modelos) **no cambió de comportamiento**.
- `backend/routers/ia_prediccion.py` — se añadieron los endpoints nuevos (ver sección 6); los 4 originales no se tocaron.
- `backend/routers/reportes.py` — se añadieron los 3 endpoints de reportes de IA; `/api/reportes/semanal` no se tocó.
- `database/modelos.py` — se añadieron 5 tablas nuevas (`EjecucionEntrenamiento`, `ResultadoModelo`, `ResultadoFold`, `ResultadoPruebaEstadistica`, `ModeloGuardado`); no se eliminó ninguna columna ni tabla existente.
- `frontend/src/pages/IA.tsx` — se añadieron un botón y sección para EDA, un botón y sección para el entrenamiento completo (5 modelos), y el panel de modelo guardado; nada existente se quitó.
- `requirements.txt` — se añadieron `pytest` y `python-docx`.
- `README.md` — se actualizó (stack, estructura, endpoints, tablas, pruebas, limitaciones).

`ia/predictor.py` **no se modificó**: `HybridTransformerModel`, `ejecutar_prediccion_completa` y el endpoint `/predecir` siguen exactamente igual.

## 6. Endpoints añadidos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/ia/eda/{id_plato}` | EDA estructurado del histórico de un plato |
| `POST` | `/api/ia/entrenar-comparar` | Flujo completo: EDA + 5 modelos + CV + tuning + pruebas estadísticas + guardado opcional |
| `GET` | `/api/ia/modelos-guardados` | Lista de modelos guardados |
| `GET` | `/api/ia/modelos-guardados/{id_plato}` | Estado del modelo guardado (vigente/desactualizado) |
| `POST` | `/api/ia/modelos-guardados/{id_plato}/predecir` | Predice con el modelo guardado, sin reentrenar |
| `POST` | `/api/ia/modelos-guardados/{id_plato}/reentrenar` | Ejecuta la comparación de 5 modelos y guarda el ganador |
| `GET` | `/api/reportes/ia/{ejecucion_id}/pdf` | Reporte PDF |
| `GET` | `/api/reportes/ia/{ejecucion_id}/word` | Reporte Word |
| `GET` | `/api/reportes/ia/{ejecucion_id}/excel` | Reporte Excel (7 hojas) |

Los 4 endpoints originales (`/predecir`, `/comparar-modelos`, `/historial`, `/platos-disponibles`) siguen exactamente iguales.

### Contrato de `POST /api/ia/entrenar-comparar`

Request:
```json
{
  "id_plato": 1,
  "dias_adelante": 7,
  "clima": 2,
  "evento": 0,
  "n_splits": 5,
  "ejecutar_tuning": true,
  "guardar_ganador": true
}
```

Response (resumida): `ejecucion_id`, `estado`, `dataset`, `eda_resumen`, `modelo_ganador`, `metricas_por_modelo` (5 modelos, con `smape`), `validacion_cruzada` (folds por modelo), `hiperparametros` (resultado del tuning por modelo), `pruebas_estadisticas` (`friedman`, `wilcoxon[]`, `diebold_mariano[]`), `modelo_guardado`, `predicciones_futuras`, `interpretacion[]`.

## 7. Tablas añadidas

`ejecuciones_entrenamiento`, `resultados_modelo`, `resultados_fold`, `resultados_prueba_estadistica`, `modelos_guardados` — ver README.md para el detalle de columnas. Se crean automáticamente al iniciar el backend; no requieren migración manual y no afectan las tablas existentes (verificado: `ventas`/`detalle_ventas` con el mismo número de filas antes y después de correr `crear_tablas()` contra la base de datos real).

## 8. Flujo completo (`POST /ia/entrenar-comparar`)

1. `ia.comparacion_completa.comparar_cinco_modelos` — construye el dataset del plato, valida mínimo de datos (30 días), split cronológico 80/20, entrena y evalúa ARIMA/Prophet/Holt-Winters/Transformer+RF/Transformer+GBR, selecciona ganador (menor MAE, empate → RMSE → SMAPE).
2. `ia.eda.generar_eda_desde_df` — resumen del EDA sobre el mismo dataset ya usado para modelar.
3. `ia.tuning` — una búsqueda de hiperparámetros por modelo (no dentro de cada fold, por rendimiento): búsqueda temporal propia para los 3 modelos clásicos, `RandomizedSearchCV` + `TimeSeriesSplit` para los regresores de los híbridos.
4. `ia.validacion.evaluar_modelo_cv` — 5 folds walk-forward por modelo, usando los hiperparámetros hallados en el paso 3 (fijos durante la CV, para no repetir una búsqueda costosa en cada fold).
5. `ia.pruebas_estadisticas` — Friedman sobre los 5 modelos, Wilcoxon del ganador contra cada competidor (Holm-Bonferroni), Diebold-Mariano del ganador contra cada competidor.
6. Si `guardar_ganador=true`: se reentrena el modelo ganador sobre **todo** el histórico (`ajustar_*_completo`) y se guarda con `ia.model_registry.guardar_modelo` (artefacto + metadatos, escritura atómica).
7. `ia.persistencia_bd.guardar_ejecucion_comparacion` — persiste todo en las 5 tablas nuevas.
8. El router construye la respuesta pública (sin objetos internos de pandas/numpy) y la retorna.

Tiempo medido contra datos reales (plato con 90 días de historial, 5 folds, tuning activado): **~12.7 segundos**.

## 9. Decisiones técnicas

- **El Transformer NO se migró a PyTorch.** Por instrucción explícita del usuario, se implementó todo lo demás primero y se evaluó al final si la migración era "realmente necesaria". Decisión: **no**, por ahora. Razones:
  - La limitación (atención = proyección aleatoria fija, no entrenada) ya se documenta de forma explícita y visible: en el docstring de `ia/modelos_hibridos.py`, en el campo `nota_atencion` que devuelve cada modelo híbrido en su API (`get_info()`), y en el README/este documento. El sistema ya no *implica* falsamente que es un Transformer entrenado end-to-end.
  - Una migración real requeriría: diseñar un encoder entrenable, un bucle de entrenamiento con optimizador y early stopping, re-serializar los modelos guardados, y revalidar CV/tuning/reportes que ya están construidos y probados sobre la arquitectura actual — es esencialmente rehacer las Fases 3 a 9 para ese componente.
  - Es una decisión reversible: queda documentada como limitación conocida y como trabajo futuro concreto, no oculta.
- **`comparar_cinco_modelos` usa un único split 80/20** (no CV) para la selección del ganador y las predicciones futuras, igual que la función original de 3 modelos. La CV de 5 folds es una capa de **análisis adicional** (más robusta estadísticamente) que se ejecuta por separado dentro de `/entrenar-comparar`, reutilizando los hiperparámetros ya buscados — evita repetir búsquedas costosas de hiperparámetros dentro de cada fold (sección de rendimiento del encargo original).
- **No se usó Optuna** (instrucción explícita): tuning vía `RandomizedSearchCV` para los regresores sklearn y una búsqueda aleatoria propia con semilla fija para los modelos estadísticos.
- **`models/` guarda solo el modelo activo más reciente por plato** (no todo el historial): el historial completo de ejecuciones vive en la base de datos. Evita crecimiento sin control del disco en un entorno de estudiante.
- **`ia/predictor.py` no se tocó**: `HybridTransformerModel` se mantiene intacto únicamente por compatibilidad con `/predecir` y con `/comparar-modelos` (3 modelos), tal como pedía el encargo.

## 10. Cómo probar cada funcionalidad

```bash
# Backend
venv\Scripts\activate  (o `source venv/bin/activate` en Linux/macOS)
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

- **EDA**: en la pantalla de IA, seleccionar un plato → botón "Analizar datos (EDA)".
- **Comparación de 5 modelos**: botón "Ejecutar experimentación completa" (tarda decenas de segundos; hay un indicador de carga).
- **Modelo guardado**: tras ejecutar la experimentación completa (con "guardar ganador" activado, por defecto), el panel "Modelo guardado" permite predecir sin reentrenar o forzar un reentrenamiento.
- **Reportes**: tras una ejecución completa, botones "PDF" / "Word" / "Excel" en la cabecera de resultados.
- **Pruebas automatizadas**: `pytest` desde la raíz del proyecto (161 pruebas, ~60 s). `npm run build` en `frontend/` para verificar la compilación TypeScript y el build de producción.
- **Verificación manual vía API** (equivalente a lo hecho durante el desarrollo):
  ```bash
  curl -X POST http://localhost:8000/api/ia/entrenar-comparar \
    -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
    -d '{"id_plato": 1, "dias_adelante": 7}'
  ```
