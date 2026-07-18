Actúa como desarrollador senior full stack especializado en:

- Python
- FastAPI
- React con TypeScript
- Machine Learning
- Series temporales
- Redes neuronales
- Validación estadística
- SQLAlchemy
- SQLite
- Generación de reportes PDF, Word y Excel

Estoy trabajando en el proyecto SIGPDA, un sistema de predicción de demanda y reducción de desperdicios para restaurantes.

IMPORTANTE:

No quiero que rehagas el proyecto desde cero.
No quiero que elimines funcionalidades existentes.
No quiero que cambies arbitrariamente la arquitectura.
No quiero que implementes nuevamente algo que ya funciona.

Tu primera obligación es revisar completamente el código actual, identificar lo ya implementado y desarrollar únicamente lo que falte para cumplir los requisitos descritos más adelante.

Por ahora NO debes trabajar en:

- Render
- Vercel
- despliegue en producción
- Jira
- GitHub Actions
- Docker para producción
- artículo científico

La prioridad es dejar el sistema completamente funcional en entorno local.

==================================================
1. ESTRUCTURA ACTUAL QUE DEBES REVISAR
==================================================

Revisa como mínimo estos archivos y directorios:

Backend:

- backend/main.py
- backend/routers/ia_prediccion.py
- backend/routers/reportes.py
- backend/routers/estadisticas.py
- database/modelos.py
- database/conexion.py

Inteligencia artificial:

- ia/comparador_modelos.py
- ia/predictor.py

Frontend:

- frontend/src/pages/IA.tsx
- frontend/src/pages/Reportes.tsx
- frontend/src/pages/Estadisticas.tsx
- frontend/src/api/client.ts
- frontend/src/types/index.ts
- frontend/src/App.tsx
- frontend/src/components/Sidebar.tsx

Dependencias:

- requirements.txt
- frontend/package.json

Base de datos:

- database/sigpda.db
- database/esquema.sql

Antes de modificar código:

1. Lee el README y la documentación existente.
2. Revisa el flujo actual de predicción.
3. Identifica los modelos existentes.
4. Identifica las métricas existentes.
5. Verifica los endpoints actuales.
6. Revisa las tablas de base de datos relacionadas con predicciones y comparaciones.
7. Revisa cómo React consume el backend.
8. Revisa los reportes que ya existen.
9. Ejecuta el sistema o, como mínimo, las pruebas de importación y compilación.
10. Crea un inventario breve de:
   - funcionalidad existente;
   - funcionalidad parcialmente implementada;
   - funcionalidad faltante;
   - errores técnicos encontrados.

No comiences a programar hasta terminar esta auditoría.

==================================================
2. FUNCIONALIDAD QUE YA EXISTE Y DEBE CONSERVARSE
==================================================

El proyecto ya parece incluir, entre otras cosas:

- Backend con FastAPI.
- Frontend con React y TypeScript.
- Autenticación.
- Predicción individual.
- Modelos clásicos como Random Forest, regresión lineal y árbol de decisión.
- Comparación de ARIMA, Prophet y un modelo denominado Transformer híbrido.
- División cronológica de datos.
- Métricas MAE, RMSE, MAPE y R².
- Selección automática del modelo ganador.
- Prueba Diebold-Mariano.
- Predicciones futuras.
- Persistencia de predicciones y comparaciones.
- Pantalla de inteligencia artificial en React.
- Gráficos y tablas comparativas.
- Reportes PDF y Excel generales.

Debes confirmar cada punto revisando el código.

Si una función ya existe y funciona, reutilízala o extiéndela. No crees una segunda implementación paralela.

==================================================
3. OBJETIVO GENERAL
==================================================

Completar el módulo de inteligencia artificial para que cumpla este flujo:

1. Obtención y preparación de datos.
2. EDA o análisis exploratorio.
3. Limpieza y validación de datos.
4. Entrenamiento de tres modelos clásicos.
5. Entrenamiento de dos modelos híbridos.
6. Validación cruzada temporal con cinco folds.
7. Optimización de hiperparámetros.
8. Comparación mediante métricas de regresión.
9. Pruebas estadísticas robustas.
10. Selección automática del mejor modelo.
11. Persistencia del mejor modelo entrenado.
12. Carga del modelo guardado sin reentrenarlo.
13. Predicción futura.
14. Visualización completa en React.
15. Exportación de resultados a PDF, Word y Excel.

El problema es de regresión y pronóstico de demanda.

Por tanto, NO debes añadir como métricas principales:

- accuracy;
- precision;
- recall;
- F1-score;
- matriz de confusión;
- curva ROC.

Estas corresponden a clasificación y no son apropiadas para este problema.

==================================================
4. MODELOS REQUERIDOS
==================================================

La comparación principal debe utilizar exactamente cinco modelos:

Modelos clásicos:

1. ARIMA.
2. Prophet.
3. Holt-Winters o Exponential Smoothing.

Modelos híbridos:

4. Transformer + Random Forest.
5. Transformer + Gradient Boosting.

Antes de implementarlos, revisa cómo están construidos los modelos actuales.

No elimines la predicción individual existente con:

- random_forest;
- regresion_lineal;
- decision_tree;
- transformer_hibrido.

Puedes mantenerla por compatibilidad, pero la comparación científica principal deberá usar los cinco modelos indicados.

==================================================
5. CORRECCIÓN DEL TRANSFORMER
==================================================

Audita cuidadosamente la clase o implementación de atención existente.

Verifica si las matrices de atención, por ejemplo:

- W_Q
- W_K
- W_V
- W_O

son parámetros realmente entrenables mediante retropropagación.

Si actualmente se generan aleatoriamente y nunca se actualizan, no debes presentarlo como un Transformer neuronal entrenado.

En ese caso, reemplaza o corrige esa implementación usando PyTorch.

Requisitos para el Transformer:

- Debe ser realmente entrenable.
- Debe usar semillas reproducibles.
- Debe manejar datos secuenciales.
- Debe evitar fuga de información.
- Debe utilizar únicamente datos anteriores para predecir datos futuros.
- Debe extraer representaciones o embeddings de la serie temporal.

Luego utiliza esas representaciones para entrenar:

- RandomForestRegressor.
- GradientBoostingRegressor o HistGradientBoostingRegressor.

Los dos híbridos deben ser independientes y aparecer como modelos diferentes en todas las tablas, pruebas y reportes.

Arquitectura sugerida, adaptable al proyecto:

Serie temporal y variables exógenas
→ creación de secuencias
→ normalización
→ Transformer entrenable
→ extracción del embedding o representación latente
→ Random Forest o Gradient Boosting
→ predicción final

No uses una transformación aleatoria como sustituto del entrenamiento.

==================================================
6. ANÁLISIS EXPLORATORIO DE DATOS — EDA
==================================================

Implementa un módulo de EDA asociado al plato seleccionado.

Debe analizar los datos históricos usados para entrenar los modelos.

Debe incluir:

- número total de registros;
- fecha inicial;
- fecha final;
- cantidad de días cubiertos;
- valores faltantes;
- registros duplicados;
- media;
- mediana;
- desviación estándar;
- mínimo;
- máximo;
- cuartiles;
- rango intercuartílico;
- posibles valores atípicos;
- distribución de la demanda;
- demanda por día de la semana;
- demanda por mes, cuando haya datos suficientes;
- evolución histórica;
- correlación entre variables numéricas;
- mapa de calor de correlaciones;
- información sobre clima;
- información sobre eventos;
- advertencias cuando el dataset sea insuficiente.

El backend debe devolver datos estructurados, no imágenes estáticas.

React deberá construir los gráficos usando la biblioteca ya existente en el proyecto. Si no existe una biblioteca adecuada, usa Recharts.

No agregues una biblioteca diferente si ya existe una que pueda resolverlo correctamente.

Crea un endpoint coherente con el router actual, por ejemplo:

GET /ia/eda/{id_plato}

o

POST /ia/eda

Respeta el prefijo real configurado en backend/main.py.

El resultado debe incluir, como mínimo:

{
  "resumen": {},
  "estadisticas_descriptivas": {},
  "valores_faltantes": {},
  "duplicados": 0,
  "outliers": {},
  "serie_historica": [],
  "distribucion": [],
  "por_dia_semana": [],
  "por_mes": [],
  "correlaciones": {},
  "advertencias": []
}

==================================================
7. LIMPIEZA Y PREPARACIÓN
==================================================

Implementa una única canalización reutilizable para preparar datos.

Debe:

- ordenar cronológicamente;
- eliminar o controlar duplicados;
- manejar valores nulos de forma justificada;
- validar tipos de datos;
- evitar cantidades negativas;
- construir variables temporales;
- incorporar clima y evento cuando corresponda;
- crear lags;
- crear medias móviles exclusivamente con datos pasados;
- evitar fuga de información;
- separar train, validation y test cronológicamente;
- guardar los parámetros de escalado cuando sean necesarios.

No calcules variables de una fecha usando información futura.

Centraliza esta lógica para evitar que cada modelo prepare los datos de manera distinta.

Puedes crear módulos como:

- ia/data_preparation.py
- ia/eda.py
- ia/modelos_clasicos.py
- ia/modelos_hibridos.py
- ia/validacion.py
- ia/pruebas_estadisticas.py
- ia/model_registry.py
- ia/reportes_ia.py

Los nombres son sugeridos. Adáptalos a la arquitectura existente.

==================================================
8. VALIDACIÓN CRUZADA TEMPORAL
==================================================

Implementa validación cruzada temporal real con cinco folds.

Usa:

TimeSeriesSplit(n_splits=5)

o una implementación walk-forward equivalente, si se adapta mejor a ARIMA, Prophet y Holt-Winters.

No uses KFold aleatorio.

No mezcles fechas futuras dentro del entrenamiento de folds anteriores.

Para cada uno de los cinco modelos, reporta por fold:

- número de fold;
- fecha inicial y final de entrenamiento;
- fecha inicial y final de validación;
- cantidad de observaciones de entrenamiento;
- cantidad de observaciones de validación;
- MAE;
- RMSE;
- MAPE;
- SMAPE;
- R²;
- tiempo de entrenamiento;
- tiempo de inferencia.

También reporta por modelo:

- promedio de cada métrica;
- desviación estándar;
- mínimo;
- máximo;
- tiempo total.

Si no existen suficientes registros para cinco folds:

- no provoques un error interno;
- devuelve una advertencia comprensible;
- calcula el número máximo razonable de folds;
- informa claramente cuántos folds se pudieron ejecutar.

==================================================
9. MÉTRICAS
==================================================

Conserva:

- MAE;
- RMSE;
- MAPE;
- R².

Añade:

- SMAPE.

Consideraciones:

- Maneja correctamente valores reales iguales a cero.
- No permitas divisiones por cero.
- Documenta la fórmula empleada.
- El ganador no debe elegirse mediante R² únicamente.
- Usa MAE como criterio principal, salvo que el código existente tenga una justificación distinta.
- En caso de empate, usa RMSE y luego SMAPE como criterios secundarios.

La respuesta del backend debe devolver métricas con precisión numérica razonable, sin valores NaN ni Infinity.

==================================================
10. OPTIMIZACIÓN DE HIPERPARÁMETROS
==================================================

Implementa tuning respetando el orden temporal.

No uses validación aleatoria.

Cada modelo debe tener una búsqueda razonable y computacionalmente viable.

Ejemplo de espacios de búsqueda:

ARIMA:

- p: 0 a 3
- d: 0 a 2
- q: 0 a 3

Prophet:

- changepoint_prior_scale
- seasonality_prior_scale
- seasonality_mode
- weekly_seasonality

Holt-Winters:

- trend
- seasonal
- damped_trend
- seasonal_periods

Transformer:

- sequence_length
- d_model
- nhead
- num_layers
- dropout
- learning_rate
- batch_size
- epochs con early stopping

Random Forest:

- n_estimators
- max_depth
- min_samples_split
- min_samples_leaf
- max_features

Gradient Boosting:

- n_estimators
- learning_rate
- max_depth
- min_samples_split
- min_samples_leaf
- subsample

No es obligatorio evaluar todas las combinaciones posibles.

Puedes usar:

- búsqueda manual controlada;
- RandomizedSearchCV con TimeSeriesSplit;
- Optuna, únicamente si se incorpora correctamente;
- una estrategia propia de búsqueda temporal.

Debes registrar:

- espacio de búsqueda;
- combinaciones evaluadas;
- mejor configuración;
- métrica objetivo;
- valor obtenido;
- tiempo empleado;
- semilla aleatoria;
- fecha de ejecución.

La interfaz debe mostrar esta información de manera comprensible.

==================================================
11. PRUEBAS ESTADÍSTICAS
==================================================

Conserva y revisa la prueba Diebold-Mariano existente.

Añade:

1. Prueba de Friedman para comparar simultáneamente los cinco modelos.
2. Prueba de Wilcoxon entre el modelo ganador y cada uno de los demás modelos.
3. Diebold-Mariano entre el ganador y los competidores, siempre que sea estadísticamente aplicable.

Requisitos:

- Usa errores alineados sobre las mismas fechas.
- Verifica el tamaño mínimo de muestra.
- Controla casos de errores idénticos o varianza cero.
- No devuelvas NaN sin explicación.
- Usa alpha = 0.05.
- Incluye:
  - estadístico;
  - p-valor;
  - significativo;
  - hipótesis;
  - interpretación automática en español.

No afirmes que un modelo es estadísticamente superior si p >= 0.05.

Para comparaciones múltiples de Wilcoxon, aplica una corrección como Holm-Bonferroni y reporta tanto el p-valor original como el ajustado.

==================================================
12. PERSISTENCIA DEL MEJOR MODELO
==================================================

Implementa un registro de modelos entrenados.

El mejor modelo debe guardarse para no reentrenarlo cada vez.

Crea una carpeta como:

models/

Debe estar excluida de Git si los archivos son grandes, pero conserva la estructura mediante un .gitkeep.

Guarda:

- artefacto del modelo;
- scaler;
- encoder, si existe;
- configuración;
- hiperparámetros;
- métricas;
- fecha de entrenamiento;
- id del plato;
- nombre del plato;
- rango temporal de entrenamiento;
- cantidad de registros;
- versión del modelo;
- versión de librerías relevantes;
- hash o firma del dataset;
- ruta del artefacto.

Puedes utilizar:

- joblib para modelos de scikit-learn;
- torch.save para PyTorch;
- JSON para metadatos.

Si el ganador es híbrido, deben guardarse todos sus componentes:

- Transformer;
- modelo Random Forest o Gradient Boosting;
- scalers;
- configuración de secuencias;
- columnas;
- metadatos.

Implementa funciones claras:

- guardar_modelo();
- cargar_modelo();
- existe_modelo_vigente();
- listar_modelos_guardados();
- eliminar_modelo(), solo si es seguro;
- predecir_con_modelo_guardado().

Crea endpoints equivalentes a:

GET /ia/modelos-guardados
GET /ia/modelos-guardados/{id_plato}
POST /ia/modelos-guardados/{id_plato}/predecir
POST /ia/modelos-guardados/{id_plato}/reentrenar

Adapta las rutas al esquema existente.

El sistema debe informar:

- si está usando un modelo guardado;
- cuándo fue entrenado;
- qué modelo es;
- sus métricas;
- si los datos han cambiado desde el entrenamiento;
- si recomienda reentrenar.

No cargues archivos con rutas recibidas directamente desde el usuario. Evita path traversal.

==================================================
13. BASE DE DATOS
==================================================

Revisa las tablas existentes:

- Prediccion;
- ComparacionModelos;
- y cualquier otra relacionada.

No borres columnas ni datos existentes.

Amplía la persistencia para soportar cinco modelos.

Actualmente pueden existir columnas específicas para:

- ARIMA;
- Prophet;
- Transformer.

No continúes aumentando indefinidamente columnas específicas si eso vuelve rígido el diseño.

Preferentemente crea nuevas tablas normalizadas, por ejemplo:

EjecucionEntrenamiento:

- id;
- id_plato;
- id_usuario;
- fecha;
- estado;
- modelo_ganador;
- criterio_seleccion;
- duracion;
- numero_registros;
- fecha_inicio_datos;
- fecha_fin_datos;
- ruta_artefacto;
- metadata_json.

ResultadoModelo:

- id;
- id_ejecucion;
- modelo;
- categoria;
- mae;
- rmse;
- mape;
- smape;
- r2;
- tiempo_entrenamiento;
- tiempo_inferencia;
- hiperparametros_json;
- posicion.

ResultadoFold:

- id;
- id_resultado_modelo;
- numero_fold;
- mae;
- rmse;
- mape;
- smape;
- r2;
- fechas;
- tiempos.

ResultadoPruebaEstadistica:

- id;
- id_ejecucion;
- prueba;
- modelo_a;
- modelo_b;
- estadistico;
- p_valor;
- p_valor_ajustado;
- significativo;
- interpretacion.

ModeloGuardado:

- id;
- id_plato;
- id_ejecucion;
- modelo;
- ruta;
- fecha_entrenamiento;
- hash_datos;
- activo;
- metadata_json.

Los nombres son orientativos.

Usa SQLAlchemy siguiendo el estilo del proyecto.

Como el proyecto usa SQLite, crea una migración segura o un script idempotente para añadir tablas sin borrar la base actual.

No reemplaces database/sigpda.db por una base vacía.

==================================================
14. ENDPOINT PRINCIPAL DE EXPERIMENTACIÓN
==================================================

Amplía o crea un endpoint para ejecutar el proceso completo.

Ejemplo:

POST /ia/entrenar-comparar

Entrada:

{
  "id_plato": 1,
  "dias_adelante": 7,
  "clima": 2,
  "evento": 0,
  "n_splits": 5,
  "ejecutar_tuning": true,
  "guardar_ganador": true
}

Respuesta sugerida:

{
  "ejecucion_id": 1,
  "estado": "completado",
  "dataset": {
    "registros": 365,
    "fecha_inicio": "...",
    "fecha_fin": "...",
    "advertencias": []
  },
  "eda_resumen": {},
  "metricas_por_modelo": {
    "arima": {},
    "prophet": {},
    "holt_winters": {},
    "transformer_random_forest": {},
    "transformer_gradient_boosting": {}
  },
  "validacion_cruzada": {
    "arima": {
      "folds": [],
      "promedio": {},
      "desviacion_estandar": {}
    }
  },
  "hiperparametros": {},
  "pruebas_estadisticas": {
    "friedman": {},
    "wilcoxon": [],
    "diebold_mariano": []
  },
  "modelo_ganador": "transformer_random_forest",
  "criterio_seleccion": "menor MAE promedio",
  "modelo_guardado": {
    "guardado": true,
    "ruta_logica": "...",
    "fecha": "..."
  },
  "predicciones_futuras": [],
  "interpretacion": []
}

No devuelvas modelos serializados ni rutas internas sensibles al frontend.

Si el entrenamiento tarda mucho, implementa inicialmente una ejecución síncrona robusta con indicadores de carga en React.

No incorpores Celery, Redis o infraestructura adicional salvo que sea estrictamente necesaria.

==================================================
15. INTERFAZ EN REACT
==================================================

Mantén el diseño visual existente de SIGPDA.

No reemplaces toda la página IA.tsx sin necesidad.

Puedes refactorizarla en componentes más pequeños si actualmente es demasiado extensa.

La pantalla de IA debe organizarse mediante pestañas, pasos o secciones:

1. Configuración.
2. Análisis exploratorio.
3. Entrenamiento y optimización.
4. Validación cruzada.
5. Comparación de modelos.
6. Pruebas estadísticas.
7. Modelo guardado.
8. Predicciones.
9. Reportes.

Debe incluir:

Configuración:

- selector de plato;
- días de predicción;
- clima;
- evento;
- botón para analizar datos;
- botón para entrenar y comparar;
- botón para cargar modelo guardado;
- botón para reentrenar.

EDA:

- tarjetas resumen;
- tabla de estadísticas;
- serie temporal;
- histograma;
- boxplot;
- demanda por día de semana;
- mapa de calor;
- advertencias.

Entrenamiento:

- estado del proceso;
- modelos que se ejecutan;
- tiempo;
- hiperparámetros;
- mensajes de error específicos.

Comparación:

Tabla de cinco modelos con:

- posición;
- modelo;
- tipo;
- MAE;
- RMSE;
- MAPE;
- SMAPE;
- R²;
- tiempo;
- indicador visual del ganador.

Validación cruzada:

- tabla por folds;
- promedio;
- desviación estándar;
- gráfico comparativo;
- posibilidad de desplegar los detalles de cada fold.

Pruebas estadísticas:

- Friedman;
- Wilcoxon;
- Diebold-Mariano;
- p-valores;
- interpretación en español;
- alerta visible indicando si existe o no diferencia significativa.

Modelo guardado:

- modelo;
- fecha de entrenamiento;
- métricas;
- versión;
- rango del dataset;
- estado vigente o desactualizado;
- botón de usar;
- botón de reentrenar.

Predicciones:

- tabla de fechas futuras;
- demanda estimada;
- recomendación;
- riesgo;
- gráfico;
- indicación de si se usó el modelo guardado.

Reportes:

- descargar PDF;
- descargar Word;
- descargar Excel.

Implementa estados:

- loading;
- error;
- vacío;
- completado;
- advertencia.

No ocultes errores del backend con mensajes genéricos.

==================================================
16. REPORTES DE INTELIGENCIA ARTIFICIAL
==================================================

No reemplaces los reportes generales actuales.

Añade reportes específicos de experimentación de IA.

Deben estar disponibles en:

- PDF;
- Word;
- Excel.

El reporte debe incluir:

1. Portada o encabezado.
2. Fecha de generación.
3. Plato analizado.
4. Rango del dataset.
5. Cantidad de registros.
6. Resumen del EDA.
7. Estadísticas descriptivas.
8. Calidad de datos.
9. Configuración de los modelos.
10. Hiperparámetros evaluados.
11. Mejor hiperparámetro por modelo.
12. Resultados de los cinco folds.
13. Promedios y desviaciones.
14. Tabla comparativa de los cinco modelos.
15. Modelo ganador.
16. Prueba de Friedman.
17. Pruebas de Wilcoxon.
18. Pruebas Diebold-Mariano.
19. Gráficos.
20. Interpretación de los resultados.
21. Predicciones futuras.
22. Conclusiones automáticas técnicamente prudentes.

Para Word, agrega python-docx si no existe.

Para Excel:

- usa múltiples hojas;
- no pegues todas las tablas como imágenes;
- las métricas deben ser celdas editables;
- incluye gráficos de Excel cuando sea razonable;
- usa estilos básicos profesionales;
- ajusta anchos de columnas;
- congela encabezados;
- aplica formatos numéricos.

Hojas sugeridas:

- Resumen;
- EDA;
- Modelos;
- Validación cruzada;
- Hiperparámetros;
- Pruebas estadísticas;
- Predicciones.

Para PDF y Word sí pueden incorporarse gráficos renderizados temporalmente.

Elimina correctamente los archivos temporales.

Crea endpoints como:

GET /reportes/ia/{ejecucion_id}/pdf
GET /reportes/ia/{ejecucion_id}/word
GET /reportes/ia/{ejecucion_id}/excel

Respeta autenticación y permisos existentes.

==================================================
17. DATASET PÚBLICO
==================================================

El profesor pide usar datasets públicos en el artículo científico.

Sin embargo, no debes sustituir los datos internos del sistema ni romper el flujo actual.

Prepara la arquitectura para aceptar:

- datos históricos internos;
- carga controlada de CSV;
- o un dataset público adaptado.

No descargues automáticamente datasets externos durante la ejecución normal.

Si añades importación de CSV:

- valida extensión;
- valida tamaño;
- valida columnas;
- evita ejecución de contenido;
- muestra vista previa;
- permite mapear columnas;
- no sobrescribas información existente sin confirmación.

Para esta implementación local, prioriza los datos ya existentes en la base de datos.

==================================================
18. SEGURIDAD Y CALIDAD
==================================================

Mantén la autenticación existente.

Protege todos los endpoints de IA y reportes igual que los actuales.

Valida:

- id_plato;
- cantidad mínima de datos;
- fechas;
- días de predicción;
- clima;
- evento;
- archivos;
- rutas.

No uses eval().

No uses rutas de archivos proporcionadas libremente por el cliente.

No expongas stack traces al frontend.

Registra errores con logging.

Usa transacciones seguras en base de datos.

Cierra sesiones y archivos.

No guardes modelos parcialmente escritos. Usa escritura temporal y renombrado atómico cuando sea posible.

==================================================
19. REPRODUCIBILIDAD
==================================================

Define una semilla central para:

- Python random;
- NumPy;
- scikit-learn;
- PyTorch.

Registra la semilla en los resultados.

Activa configuraciones deterministas de PyTorch cuando sea razonable.

Documenta que algunos procesos pueden no ser completamente deterministas según hardware y versión.

Guarda versiones de:

- Python;
- NumPy;
- pandas;
- scikit-learn;
- statsmodels;
- Prophet;
- PyTorch.

==================================================
20. RENDIMIENTO
==================================================

El proyecto debe seguir funcionando en una computadora de estudiante.

No uses configuraciones excesivamente pesadas.

Incluye límites razonables:

- epochs;
- combinaciones de tuning;
- profundidad de árboles;
- cantidad de estimadores;
- tamaño de secuencia.

Usa early stopping para el Transformer.

Evita entrenar el Transformer repetidamente dentro de cada combinación si puede reutilizarse de forma metodológicamente válida.

No sacrifiques la separación temporal para reducir tiempo.

Muestra advertencias cuando un proceso pueda tardar.

==================================================
21. COMPATIBILIDAD
==================================================

Conserva los endpoints actuales siempre que sea posible:

- /predecir
- /comparar-modelos
- /historial
- /platos-disponibles

No rompas el frontend existente.

Si debes cambiar la estructura de respuesta de /comparar-modelos:

- conserva los campos anteriores;
- añade los campos nuevos;
- o crea un endpoint nuevo para la experimentación completa.

Mantén compatibilidad con registros históricos que solo tengan tres modelos.

==================================================
22. PRUEBAS
==================================================

Crea pruebas automatizadas razonables.

Backend:

- pruebas de métricas;
- SMAPE con ceros;
- preparación temporal sin fuga;
- creación de folds;
- selección del ganador;
- guardado y carga del modelo;
- EDA con datos vacíos;
- EDA con nulos;
- pruebas estadísticas con muestras pequeñas;
- endpoints principales;
- permisos y autenticación.

Modelos:

No es necesario entrenar redes grandes en las pruebas.

Usa datasets sintéticos pequeños y configuraciones rápidas.

Frontend:

Como mínimo verifica:

- compilación TypeScript;
- renderizado de la página;
- manejo de estados;
- consumo de respuestas completas;
- consumo de respuestas con advertencias;
- compatibilidad con datos anteriores.

Ejecuta:

- pytest;
- npm run build;
- cualquier lint existente.

No consideres terminada la tarea si el frontend no compila.

==================================================
23. DEPENDENCIAS
==================================================

Revisa requirements.txt antes de añadir paquetes.

Añade únicamente lo necesario.

Posibles dependencias:

- torch;
- scipy;
- joblib;
- python-docx;
- openpyxl;
- matplotlib, si ya se utiliza;
- statsmodels;
- prophet.

No dupliques librerías equivalentes.

Fija versiones compatibles cuando sea necesario, pero no cambies todas las versiones sin justificación.

Actualiza .env.example si incorporas nuevas variables.

==================================================
24. DOCUMENTACIÓN
==================================================

Actualiza README.md con:

- requisitos;
- instalación;
- migración o actualización de base de datos;
- ejecución del backend;
- ejecución del frontend;
- estructura del módulo IA;
- modelos utilizados;
- validación cruzada;
- tuning;
- pruebas estadísticas;
- guardado de modelos;
- generación de reportes;
- comandos de pruebas;
- limitaciones conocidas.

Crea también un archivo:

IMPLEMENTACION_IA.md

Debe explicar:

- lo que ya existía;
- lo que se corrigió;
- lo que se añadió;
- archivos modificados;
- archivos nuevos;
- endpoints;
- tablas;
- flujo completo;
- decisiones técnicas;
- cómo probar cada funcionalidad.

==================================================
25. PLAN DE EJECUCIÓN OBLIGATORIO
==================================================

Trabaja en este orden:

FASE 1 — Auditoría

- Revisar el proyecto.
- Ejecutar pruebas iniciales.
- Identificar funcionalidades existentes.
- Identificar errores.
- Crear plan exacto.

FASE 2 — Preparación de datos y EDA

- Crear pipeline.
- Crear estadísticas.
- Crear endpoints.
- Integrar visualización React.

FASE 3 — Modelos faltantes y corrección del Transformer

- Agregar Holt-Winters.
- Crear Transformer entrenable.
- Crear Transformer + Random Forest.
- Crear Transformer + Gradient Boosting.

FASE 4 — Validación y tuning

- Cinco folds temporales.
- Métricas por fold.
- Optimización de hiperparámetros.
- Tiempos.

FASE 5 — Pruebas estadísticas

- Friedman.
- Wilcoxon con corrección.
- Diebold-Mariano.

FASE 6 — Persistencia

- Guardado del ganador.
- Carga.
- Registro de metadatos.
- Predicción sin reentrenar.

FASE 7 — Base de datos

- Tablas normalizadas.
- Actualización segura.
- Historial.

FASE 8 — React

- Secciones.
- Tablas.
- Gráficos.
- Estados.
- Descargas.

FASE 9 — Reportes

- PDF.
- Word.
- Excel.

FASE 10 — Pruebas y documentación

- pytest.
- npm run build.
- corrección de errores.
- README.
- IMPLEMENTACION_IA.md.

Después de cada fase:

1. Ejecuta las pruebas relacionadas.
2. Informa brevemente qué cambió.
3. Corrige errores antes de continuar.

No dejes funciones con TODO, pass o mocks como resultado final.

==================================================
26. CRITERIOS DE ACEPTACIÓN
==================================================

La tarea se considera terminada únicamente cuando:

- El sistema inicia localmente.
- El login existente sigue funcionando.
- La página IA carga correctamente.
- Se puede seleccionar un plato.
- Se puede ejecutar el EDA.
- Se visualizan estadísticas y gráficos.
- Se comparan cinco modelos.
- Existen tres modelos clásicos.
- Existen dos modelos híbridos reales.
- El Transformer es entrenable.
- Se ejecuta validación temporal de cinco folds, cuando los datos lo permiten.
- Se muestran resultados por fold.
- Se ejecuta tuning.
- Se muestran los mejores hiperparámetros.
- Se calcula MAE.
- Se calcula RMSE.
- Se calcula MAPE.
- Se calcula SMAPE.
- Se calcula R².
- Se ejecuta Friedman.
- Se ejecuta Wilcoxon.
- Se ejecuta Diebold-Mariano.
- Se selecciona un ganador.
- El ganador se guarda.
- El ganador puede cargarse posteriormente.
- Se puede predecir sin volver a entrenar.
- La comparación se guarda en la base de datos.
- Se puede descargar PDF.
- Se puede descargar Word.
- Se puede descargar Excel.
- Los reportes contienen tablas, gráficos e interpretación.
- Los endpoints anteriores siguen funcionando.
- pytest finaliza correctamente.
- npm run build finaliza correctamente.
- No hay errores visibles en consola.
- La documentación está actualizada.

==================================================
27. FORMATO DE TU RESPUESTA Y FORMA DE TRABAJO
==================================================

No me entregues solo explicaciones o fragmentos aislados.

Debes modificar directamente el proyecto.

Al comenzar, responde con:

1. Resumen de la arquitectura encontrada.
2. Funciones que ya están implementadas.
3. Funciones parcialmente implementadas.
4. Funciones faltantes.
5. Problemas técnicos detectados.
6. Archivos que planeas modificar.
7. Archivos que planeas crear.
8. Plan por fases.

Luego empieza la implementación.

Durante la implementación:

- muestra los cambios importantes;
- no pegues archivos completos innecesariamente;
- indica los comandos ejecutados;
- informa los resultados de las pruebas;
- no digas que algo funciona si no lo verificaste.

Al terminar, entrega:

1. Resumen de implementación.
2. Lista exacta de archivos creados.
3. Lista exacta de archivos modificados.
4. Endpoints añadidos.
5. Tablas añadidas.
6. Dependencias añadidas.
7. Comandos para instalar.
8. Comandos para actualizar la base de datos.
9. Comandos para ejecutar backend y frontend.
10. Comandos para pruebas.
11. Credenciales de prueba únicamente si ya existen en el proyecto.
12. Limitaciones reales pendientes.
13. Resultado de pytest.
14. Resultado de npm run build.

Empieza revisando el proyecto completo. No programes basándote únicamente en esta descripción: confirma todo en el código y conserva lo que ya está implementado.