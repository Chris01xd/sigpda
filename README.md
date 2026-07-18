# SIGPDA — Sistema Inteligente de Gestión y Predicción de Desperdicio Alimentario

**Tesis de Ingeniería de Sistemas — Valle Jequetepeque**

Sistema web inteligente para PyMEs gastronómicas que integra gestión operativa, analítica BI y predicción de demanda con Inteligencia Artificial, orientado a reducir el desperdicio alimentario.

---

## Objetivo

Reducir el desperdicio alimentario en restaurantes y PyMEs gastronómicas mediante un sistema integrado de gestión, analítica descriptiva y un módulo de predicción de demanda con IA.

El módulo de IA ofrece dos flujos, ambos disponibles y compatibles entre sí:

- **Comparación original (3 modelos)** — `POST /api/ia/comparar-modelos`: ARIMA, Prophet y Transformer Híbrido, con Diebold-Mariano. Se conserva sin cambios por compatibilidad.
- **Comparación científica completa (5 modelos)** — `POST /api/ia/entrenar-comparar`: ARIMA, Prophet, Holt-Winters, Transformer+Random Forest y Transformer+Gradient Boosting, con EDA, validación cruzada temporal (5 folds), optimización de hiperparámetros, pruebas de Friedman/Wilcoxon/Diebold-Mariano, persistencia del modelo ganador y reportes en PDF/Word/Excel. Ver **[IMPLEMENTACION_IA.md](IMPLEMENTACION_IA.md)** para el detalle técnico completo de este flujo.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI 0.111 + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Base de datos | PostgreSQL 15 / SQLite (desarrollo) |
| ORM | SQLAlchemy 2.0 |
| IA — modelo propuesto | Multi-Head Self-Attention (NumPy) + Ensemble (RF / GBR / LR / DT) + Ridge Meta-Learner |
| IA — comparación (3 modelos, original) | statsmodels (ARIMA), Prophet (Meta/Facebook), scikit-learn |
| IA — comparación científica (5 modelos) | + Holt-Winters (statsmodels), Transformer+RF y Transformer+GBR independientes |
| IA — validación y tuning | TimeSeriesSplit (walk-forward), RandomizedSearchCV, búsqueda temporal propia (sin Optuna) |
| Validación estadística | Diebold-Mariano, Friedman, Wilcoxon con corrección Holm-Bonferroni (scipy, statsmodels) |
| Persistencia de modelos | joblib (artefactos), escritura atómica, carpeta `models/` |
| Reportes | ReportLab / fpdf2 (PDF), python-docx (Word), openpyxl (Excel) |
| Autenticación | JWT (python-jose) + bcrypt |
| Comunicación frontend-backend | Axios |
| Visualización | Recharts |

---

## Estructura del Proyecto

```
sigpda/
│
├── backend/                        # API FastAPI
│   ├── main.py                     # Punto de entrada, middlewares, routers
│   ├── auth.py                     # JWT — validación de token
│   └── routers/
│       ├── auth.py
│       ├── usuarios.py
│       ├── roles.py
│       ├── restaurantes.py
│       ├── clientes.py
│       ├── proveedores.py
│       ├── platos.py
│       ├── insumos.py
│       ├── recetas.py
│       ├── ventas.py
│       ├── produccion.py
│       ├── desperdicio.py
│       ├── dashboard.py
│       ├── estadisticas.py
│       ├── bitacora.py
│       ├── configuracion.py
│       ├── recomendaciones.py
│       └── ia_prediccion.py        # Endpoints de IA y comparación
│
├── ia/                             # Módulo de Inteligencia Artificial
│   ├── __init__.py
│   ├── predictor.py                # Modelos ML individuales + Transformer Híbrido (compat. /predecir)
│   ├── comparador_modelos.py       # Comparación automática ARIMA/Prophet/Transformer (3 modelos, compat.)
│   ├── data_preparation.py         # Pipeline centralizado: limpieza, lags, medias móviles, split, escalado
│   ├── eda.py                      # Análisis exploratorio de datos
│   ├── modelos_clasicos.py         # ARIMA, Prophet, Holt-Winters (centralizados)
│   ├── modelos_hibridos.py         # Transformer+RandomForest, Transformer+GradientBoosting (independientes)
│   ├── comparacion_completa.py     # Orquesta los 5 modelos con un único split
│   ├── validacion.py               # Validación cruzada temporal (walk-forward, hasta 5 folds)
│   ├── tuning.py                   # Optimización de hiperparámetros (RandomizedSearchCV / búsqueda temporal)
│   ├── metricas.py                 # MAE, RMSE, MAPE, SMAPE, R²
│   ├── pruebas_estadisticas.py     # Diebold-Mariano, Friedman, Wilcoxon (Holm-Bonferroni)
│   ├── orquestador.py              # Flujo completo: EDA + 5 modelos + tuning + CV + pruebas estadísticas
│   ├── model_registry.py           # Guardar/cargar/predecir sin reentrenar (models/)
│   ├── persistencia_bd.py          # Guarda cada ejecución en las tablas normalizadas
│   └── reportes_ia.py              # Reportes de IA en PDF, Word y Excel
│
├── models/                         # Artefactos de modelos guardados (uno por plato, excluido de Git)
│
├── database/
│   ├── __init__.py
│   ├── conexion.py                 # Engine SQLAlchemy + sesión
│   └── modelos.py                  # Modelos ORM (todos en español)
│
├── frontend/                       # Aplicación React
│   ├── src/
│   │   ├── pages/
│   │   │   ├── IA.tsx              # Predicción + comparación automática
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Ventas.tsx
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── client.ts           # Axios con baseURL + interceptores
│   │   └── components/
│   └── package.json
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Instalación y Ejecución

### Requisitos previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (o SQLite para desarrollo sin configuración adicional)

### Backend (FastAPI)

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales de la base de datos

# 4. Ejecutar el servidor
uvicorn backend.main:app --reload --port 8000
```

API disponible en: **http://localhost:8000**  
Documentación interactiva: **http://localhost:8000/docs**

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Aplicación disponible en: **http://localhost:5173**

---

## Credenciales de Prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `gerente` | `gerente123` | Gerente |
| `trabajador` | `trabajador123` | Trabajador |
| `analista` | `analista123` | Analista |

---

## Módulo de IA — Arquitectura y Comparación

### Modelo Propuesto: Transformer Híbrido

Arquitectura desarrollada para la tesis, implementada en NumPy sin dependencias de PyTorch/TensorFlow:

```
Entrada (features) → StandardScaler → Multi-Head Self-Attention (NumPy)
                                              ↓
                             Concatenación [features originales ‖ features atendidas]
                                              ↓
                    Ensemble de modelos base: RF + GBR + Regresión Lineal + Árbol Decisión
                                              ↓
                                    Ridge Meta-Learner
                                              ↓
                               Demanda estimada (unidades)
```

**Features de entrada:**

| Feature | Descripción |
|---|---|
| `dia_semana` | Día de la semana (0 = lunes) |
| `mes` | Mes del año |
| `dia_mes` | Día del mes |
| `es_finde` | Indicador de fin de semana (0/1) |
| `clima` | Condición climática (1=soleado, 2=nublado, 3=lluvia) |
| `evento` | Tipo de evento (0=normal, 1=local, 2=feriado) |
| `cat_enc` | Categoría del plato codificada (LabelEncoder) |
| `ventas_7d` | Media móvil de ventas de los últimos 7 días |

---

### Comparación Automática de Modelos (aporte de tesis)

El sistema compara experimentalmente tres enfoques de predicción para demostrar la superioridad del modelo propuesto:

#### Modelos comparados

| Modelo | Descripción | Hiperparámetros |
|---|---|---|
| **ARIMA** | Modelo estadístico clásico para series de tiempo | Auto-seleccionados por mínimo AIC (prueba ADF + grilla p,d,q) |
| **Prophet** | Modelo de pronóstico de Meta/Facebook | Auto-seleccionados según longitud de la serie |
| **Transformer Híbrido** | Modelo propuesto del sistema | Auto-seleccionados según tamaño del dataset |

> El usuario **no puede modificar** los hiperparámetros en la comparación automática. El backend los selecciona automáticamente para garantizar imparcialidad.

#### Metodología de validación

- **Split temporal cronológico**: 80% entrenamiento / 20% prueba (sin mezcla aleatoria — obligatorio para series de tiempo)
- **Métricas calculadas** para cada modelo:
  - **MAE** — Error Absoluto Medio (criterio de selección principal)
  - **RMSE** — Raíz del Error Cuadrático Medio
  - **MAPE** — Error Porcentual Absoluto Medio
  - **R²** — Coeficiente de determinación
- **Selección automática**: gana el modelo con menor MAE
- **Prueba Diebold-Mariano**: valida estadísticamente si la diferencia de precisión entre el modelo ganador y los demás es significativa (p < 0.05)

#### Prueba Diebold-Mariano

Implementación de la prueba estadística de Diebold & Mariano (1995):

```
H₀: Los dos modelos tienen igual precisión predictiva  E[d_t] = 0
H₁: Los modelos difieren en precisión predictiva

d_t = L(e₁_t) - L(e₂_t)   con L = pérdida cuadrática
DM  = d̄ / sqrt(V̂(d̄))     ~  N(0, 1)  asintóticamente

Varianza estimada con corrección Newey-West (h = 1)
```

Si `p < 0.05` la diferencia es estadísticamente significativa y el modelo ganador es formalmente superior.

#### Flujo de la función principal

```python
comparar_modelos_prediccion(id_plato, dias_adelante, clima, evento)
```

1. Construir dataset histórico desde la base de datos
2. Agrupar demanda diaria por plato
3. Preparar serie temporal continua (interpolación de fechas faltantes)
4. Split temporal 80/20 cronológico
5. Entrenar y evaluar ARIMA (hiperparámetros automáticos)
6. Entrenar y evaluar Prophet (hiperparámetros automáticos)
7. Entrenar y evaluar Transformer Híbrido (hiperparámetros automáticos)
8. Calcular MAE, RMSE, MAPE, R² para cada modelo
9. Seleccionar ganador por menor MAE
10. Aplicar prueba Diebold-Mariano (ganador vs cada alternativa)
11. Generar predicciones futuras con el modelo ganador
12. Retornar JSON con resultado completo

#### Estructura del JSON de respuesta

```json
{
  "modelo_ganador": "transformer_hibrido",
  "modelo_ganador_legible": "Transformer Híbrido",
  "mae_ganador": 0.8234,
  "metricas_por_modelo": {
    "arima":              { "mae": 1.42, "rmse": 1.78, "mape": 14.3, "r2": 0.71 },
    "prophet":            { "mae": 1.19, "rmse": 1.51, "mape": 12.1, "r2": 0.79 },
    "transformer_hibrido": { "mae": 0.82, "rmse": 1.05, "mape":  8.6, "r2": 0.91 }
  },
  "diebold_mariano": {
    "arima_vs_transformer_hibrido": {
      "estadistico": 3.42,
      "p_valor": 0.0006,
      "significativo": true,
      "interpretacion": "Diferencia significativa al 5 % — Transformer Híbrido presenta mayor precisión"
    },
    "prophet_vs_transformer_hibrido": {
      "estadistico": 2.18,
      "p_valor": 0.0293,
      "significativo": true,
      "interpretacion": "Diferencia significativa al 5 % — Transformer Híbrido presenta mayor precisión"
    }
  },
  "predicciones_futuras": [
    { "fecha": "2026-06-14", "demanda_estimada": 28.5, "recomendacion": 32, "riesgo": "bajo" }
  ],
  "n_datos_entrenamiento": 240,
  "n_datos_prueba": 60,
  "explicacion": "El modelo Transformer Híbrido fue seleccionado automáticamente..."
}
```

---

## API — Endpoints de IA

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/ia/predecir` | Predicción individual con modelo elegido por el usuario |
| `POST` | `/api/ia/comparar-modelos` | Comparación automática ARIMA / Prophet / Transformer (3 modelos, original) |
| `GET`  | `/api/ia/historial` | Historial de predicciones guardadas |
| `GET`  | `/api/ia/platos-disponibles` | Lista de platos activos |
| `GET`  | `/api/ia/eda/{id_plato}` | Análisis exploratorio de datos del histórico de un plato |
| `POST` | `/api/ia/entrenar-comparar` | **Flujo completo**: EDA + 5 modelos + CV + tuning + pruebas estadísticas + guardado |
| `GET`  | `/api/ia/modelos-guardados` | Lista de modelos guardados (uno por plato) |
| `GET`  | `/api/ia/modelos-guardados/{id_plato}` | Estado del modelo guardado de un plato (vigente / desactualizado) |
| `POST` | `/api/ia/modelos-guardados/{id_plato}/predecir` | Predice con el modelo guardado, sin reentrenar |
| `POST` | `/api/ia/modelos-guardados/{id_plato}/reentrenar` | Ejecuta la comparación de 5 modelos y guarda el ganador |
| `GET`  | `/api/reportes/ia/{ejecucion_id}/pdf` | Reporte de una ejecución de 5 modelos en PDF |
| `GET`  | `/api/reportes/ia/{ejecucion_id}/word` | Reporte de una ejecución de 5 modelos en Word |
| `GET`  | `/api/reportes/ia/{ejecucion_id}/excel` | Reporte de una ejecución de 5 modelos en Excel (multi-hoja) |

Todos requieren `Authorization: Bearer <token>`. El detalle completo del flujo de 5 modelos (contratos de request/response, metodología, arquitectura de cada módulo) está en **[IMPLEMENTACION_IA.md](IMPLEMENTACION_IA.md)**.

### POST `/api/ia/comparar-modelos`

**Request:**
```json
{
  "id_plato":     1,
  "dias_adelante": 7,
  "clima":        2,
  "evento":       0
}
```

> Los hiperparámetros de ARIMA, Prophet y el Transformer se determinan automáticamente en el backend. El usuario no puede modificarlos.

**Requiere:** Token JWT (`Authorization: Bearer <token>`)

---

## Modelo de Datos — Tablas de IA

### `predicciones`

Almacena predicciones individuales generadas por el endpoint `/predecir`.

| Columna | Tipo | Descripción |
|---|---|---|
| `id_prediccion` | INT PK | Identificador |
| `id_plato` | INT FK | Plato predicho |
| `id_usuario` | INT FK | Usuario que ejecutó la predicción |
| `fecha_objetivo` | DATE | Fecha de la predicción |
| `demanda_estimada` | FLOAT | Unidades estimadas |
| `recomendacion_produccion` | INT | Unidades recomendadas a producir |
| `riesgo_desperdicio` | VARCHAR | `bajo` / `medio` / `alto` |
| `modelo_usado` | VARCHAR | Nombre del modelo |
| `mae` | FLOAT | Error Absoluto Medio |
| `r2` | FLOAT | Coeficiente de determinación |
| `confianza` | FLOAT | Nivel de confianza (0–1) |
| `fecha_generacion` | DATETIME | Timestamp de la predicción |

### `comparaciones_modelos`

Almacena el resultado completo de cada comparación automática.

| Columna | Tipo | Descripción |
|---|---|---|
| `id_comparacion` | INT PK | Identificador |
| `id_plato` | INT FK | Plato evaluado |
| `id_usuario` | INT FK | Usuario que ejecutó la comparación |
| `fecha_comparacion` | DATETIME | Timestamp |
| `modelo_ganador` | VARCHAR | Identificador del modelo ganador |
| `dias_adelante` | INT | Días pronosticados |
| `clima` / `evento` | INT | Contexto de la predicción |
| `mae_arima` / `rmse_arima` / `mape_arima` / `r2_arima` | FLOAT | Métricas ARIMA |
| `mae_prophet` / `rmse_prophet` / `mape_prophet` / `r2_prophet` | FLOAT | Métricas Prophet |
| `mae_transformer` / `rmse_transformer` / `mape_transformer` / `r2_transformer` | FLOAT | Métricas Transformer |
| `dm_estadistico` | FLOAT | Estadístico DM (ganador vs mejor alternativa) |
| `dm_p_valor` | FLOAT | p-valor de la prueba DM |
| `dm_significativo` | BOOL | True si p < 0.05 |
| `dm_interpretacion` | VARCHAR | Texto interpretable del resultado DM |

---

## Módulos del Sistema

| N° | Módulo | Descripción |
|---|---|---|
| 1 | Autenticación | Login JWT, roles, sesiones |
| 2 | Usuarios | CRUD de usuarios del sistema |
| 3 | Roles y Permisos | RBAC por módulo y acción |
| 4 | Restaurantes | Registro de PyMEs gastronómicas |
| 5 | Clientes | Registro de clientes |
| 6 | Proveedores | Gestión de proveedores |
| 7 | Platos | Catálogo de platos con precios y categorías |
| 8 | Insumos | Inventario de insumos con stock y alertas |
| 9 | Recetas | Relación plato ↔ insumos + cantidades |
| 10 | Ventas | Registro de ventas con detalles por plato |
| 11 | Producción | Control de unidades preparadas y sobrantes |
| 12 | Desperdicio | Registro y análisis de desperdicios |
| 13 | Predicción IA | Predicción individual con cuatro modelos |
| 14 | Comparación de modelos | Comparación automática ARIMA/Prophet/Transformer + DM |
| 15 | Recomendaciones | Alertas inteligentes por módulo |
| 16 | Dashboard BI | Indicadores clave de gestión |
| 17 | Estadísticas | Análisis descriptivo y tendencias |
| 18 | Reportes PDF | Generación de reportes imprimibles |
| 19 | Exportación | Excel / CSV por módulo |
| 20 | Bitácora | Registro de acciones por usuario |
| 21 | Configuración | Parámetros globales del sistema |

---

## Arquitectura de Capas

```
┌─────────────────────────────────────────────────────┐
│                  CAPA DE PRESENTACIÓN                │
│          React 18 + TypeScript + Tailwind CSS        │
│    (Dashboard, Ventas, Predicción, Comparación IA)   │
└────────────────────────┬────────────────────────────┘
                         │ HTTP/JSON (Axios)
┌────────────────────────▼────────────────────────────┐
│                   CAPA DE APLICACIÓN                 │
│                FastAPI + Uvicorn + JWT               │
│         Routers: auth, platos, ventas, ia, ...       │
└────────────────────────┬────────────────────────────┘
                         │
       ┌─────────────────┼───────────────────┐
       ▼                 ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│  CAPA DE IA  │  │ CAPA DE BASE │  │  CAPA DE       │
│              │  │   DE DATOS   │  │  REPORTES      │
│ predictor.py │  │ SQLAlchemy   │  │ ReportLab      │
│ comparador   │  │ PostgreSQL / │  │ openpyxl       │
│ ARIMA        │  │ SQLite       │  │                │
│ Prophet      │  └──────────────┘  └────────────────┘
│ Transformer  │
└──────────────┘
```

---

## Módulo de Alertas Inteligentes

Motor interno de alertas preventivas que **no depende de n8n ni de ningún servicio externo**. Cualquier PyME puede usarlo de forma completamente autónoma.

### Tipos de alerta generados automáticamente

| Tipo | Descripción | Niveles |
|---|---|---|
| `RIESGO_SOBREPRODUCCION` | Sobrante de producción ≥ 10 % en 30 días | BAJO / MEDIO / ALTO / CRITICO |
| `PRODUCTO_PROXIMO_VENCER` | Insumo vence en ≤ 7 días | BAJO / MEDIO / ALTO / CRITICO |
| `STOCK_EXCESIVO` | Stock > 3× el stock mínimo | BAJO / MEDIO / ALTO / CRITICO |
| `BAJA_DEMANDA` | Caída de ventas > 20 % vs. mes anterior | BAJO / MEDIO / ALTO / CRITICO |
| `ALTO_DESPERDICIO` | Costo de desperdicio elevado en 30 días | BAJO / MEDIO / ALTO / CRITICO |
| `RECOMENDACION_MENU` | Plato sin ventas en los últimos 30 días | BAJO |
| `ALERTA_CRITICA` | Baja demanda + alto desperdicio simultáneos | CRITICO |

### API — Endpoints de Alertas Inteligentes

| Método | Ruta | Descripción |
|---|---|---|
| `GET`  | `/api/alertas-inteligentes` | Lista alertas con filtros (tipo, nivel, estado) |
| `POST` | `/api/alertas-inteligentes/generar` | Ejecuta el motor de análisis y crea alertas nuevas |
| `PUT`  | `/api/alertas-inteligentes/{id}/marcar-leida` | Cambia estado a "leida" |
| `PUT`  | `/api/alertas-inteligentes/{id}/resolver` | Cambia estado a "resuelta" |

### POST `/api/alertas-inteligentes/generar`

```json
{ "clima": 2, "evento": 0 }
```

> `clima`: 1=soleado, 2=nublado, 3=lluvioso. `evento`: 0=sin evento, 1=evento local, 2=feriado.

**Respuesta:**
```json
{
  "total_generadas": 5,
  "por_tipo": { "RIESGO_SOBREPRODUCCION": 2, "PRODUCTO_PROXIMO_VENCER": 1, "BAJA_DEMANDA": 2 },
  "por_nivel": { "CRITICO": 1, "ALTO": 2, "MEDIO": 2 },
  "fecha": "2026-06-13T15:30:00"
}
```

### Tabla `alertas_inteligentes`

| Columna | Tipo | Descripción |
|---|---|---|
| `id_alerta` | INT PK | Identificador único |
| `tipo_alerta` | VARCHAR(50) | Tipo de alerta (ver tabla anterior) |
| `nivel_riesgo` | VARCHAR(20) | BAJO / MEDIO / ALTO / CRITICO |
| `titulo` | VARCHAR(200) | Título descriptivo |
| `descripcion` | TEXT | Detalle del problema detectado |
| `recomendacion` | TEXT | Acción operativa sugerida en lenguaje sencillo |
| `fecha_generacion` | DATETIME | Momento de creación |
| `estado` | VARCHAR(20) | pendiente / leida / resuelta |
| `id_plato` | INT FK | Plato relacionado (opcional) |
| `id_insumo` | INT FK | Insumo relacionado (opcional) |
| `valor_predicho` | FLOAT | Valor de referencia o esperado |
| `valor_actual` | FLOAT | Valor observado (sobrante, días, stock…) |
| `porcentaje_riesgo` | FLOAT | Porcentaje de riesgo calculado (0–100) |

---

## Gestión del Proyecto (Jira)

La gestión del proyecto se registra en Jira bajo las siguientes categorías de tareas:

| Tipo | Ejemplos |
|---|---|
| **Backlog** | Definición de módulos, requerimientos funcionales, modelo de datos |
| **Sprint** | Implementación de endpoints, desarrollo de componentes React, entrenamiento de modelos |
| **Pruebas** | Pruebas unitarias de métricas, validación del comparador, pruebas de endpoints |
| **Documentación** | README, docstrings de módulos IA, diagramas UML |

---

## Dependencias Principales

```
# Backend
fastapi==0.111.0          # Framework API REST
uvicorn[standard]==0.30.0 # Servidor ASGI
sqlalchemy==2.0.25        # ORM
pandas==2.2.0             # Manipulación de datos
numpy==1.26.3             # Álgebra lineal
scikit-learn==1.4.0       # Modelos ML clásicos
scipy>=1.8.0              # Estadística (Diebold-Mariano, Friedman, Wilcoxon)
statsmodels>=0.14.0       # ARIMA / SARIMAX / Holt-Winters / Friedman corr. Holm-Bonferroni
prophet>=1.1.0            # Modelo Prophet (Meta/Facebook)
python-docx>=1.1.0        # Reportes de IA en Word
pytest>=8.0.0             # Pruebas automatizadas
bcrypt==4.1.2             # Hash de contraseñas
python-jose[cryptography] # JWT

# Frontend
react@18                  # UI
typescript                # Tipado estático
vite                      # Bundler
tailwindcss               # Estilos utilitarios
recharts                  # Visualización de datos
axios                     # Cliente HTTP
lucide-react              # Iconos
```

---

## Base de datos — Tablas de la comparación de 5 modelos

Se añadieron 5 tablas normalizadas (no reemplazan `predicciones` ni `comparaciones_modelos`, que siguen usándose por los endpoints originales):

| Tabla | Descripción |
|---|---|
| `ejecuciones_entrenamiento` | Una fila por corrida de `/entrenar-comparar` (plato, modelo ganador, duración, rango de datos, metadata JSON con EDA/predicciones/tuning) |
| `resultados_modelo` | Una fila por modelo evaluado en cada ejecución (métricas, hiperparámetros, posición en el ranking) |
| `resultados_fold` | Una fila por fold de validación cruzada de cada modelo |
| `resultados_prueba_estadistica` | Friedman, Wilcoxon y Diebold-Mariano de cada ejecución |
| `modelos_guardados` | Historial de qué modelo quedó activo (guardado en disco) para cada plato |

Se crean automáticamente al iniciar el backend (`crear_tablas()`, vía `Base.metadata.create_all`) — no requiere una migración manual y no borra datos existentes.

---

## Pruebas

```bash
# Backend — 161 pruebas (pytest)
pytest

# Frontend — compilación TypeScript + build de producción
cd frontend
npm run build
```

La suite de pytest cubre: limpieza de datos sin fuga de información, EDA (datos vacíos/nulos/duplicados/outliers), los 5 modelos y sus variantes de ajuste, validación cruzada temporal, tuning de hiperparámetros, métricas (incluyendo SMAPE con ceros), pruebas estadísticas (Friedman/Wilcoxon/Diebold-Mariano), guardado/carga de modelos (con protección contra path traversal), las tablas normalizadas, los reportes de IA (PDF/Word/Excel) y los endpoints principales (incluyendo autenticación).

---

## Limitaciones conocidas

- **Capa de atención del Transformer no entrenada por retropropagación**: `MultiHeadSelfAttention` (usada por `transformer_hibrido`, `transformer_random_forest` y `transformer_gradient_boosting`) usa proyecciones `W_Q/W_K/W_V/W_O` inicializadas aleatoriamente y **fijas** — no hay backward pass. Actúa como una expansión de features no lineal, no como un Transformer entrenado end-to-end. Esto se documenta explícitamente en el campo `nota_atencion` de cada modelo híbrido y en `IMPLEMENTACION_IA.md`. Una migración a un encoder real en PyTorch (entrenable) se evaluó y se dejó como trabajo futuro: implicaría rediseñar el entrenamiento, la serialización y revalidar CV/tuning/reportes; con la limitación ya documentada de forma transparente en el código y en las respuestas de la API, no se consideró indispensable para dejar el sistema funcional localmente.
- **Clima simulado**: no hay proveedor meteorológico real integrado; `clima` se genera con una semilla fija para fines de la demo/tesis.
- **Ejecución síncrona**: `/entrenar-comparar` tarda entre ~10 y ~40 segundos según el tamaño del dataset (EDA + 5 modelos + tuning + CV). No hay cola de tareas en segundo plano (deliberado, para no añadir infraestructura como Celery/Redis en un entorno local de estudiante).
- **Un solo modelo guardado por plato**: `models/` conserva únicamente el artefacto más reciente por plato; el historial completo de ejecuciones vive en la base de datos, no en el sistema de archivos.

---

## Licencia

Proyecto académico — Tesis de Ingeniería de Sistemas.  
Todos los derechos reservados. Uso exclusivo con fines educativos y de investigación.
