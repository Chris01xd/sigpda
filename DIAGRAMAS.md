# SIGPDA — Diagramas del Sistema

**Tesis de Ingeniería de Sistemas — Valle Jequetepeque**

> Los diagramas están escritos en [Mermaid](https://mermaid.js.org/) y se renderizan automáticamente en GitHub, GitLab y VS Code (extensión Markdown Preview Mermaid).

---

## Índice

1. [Modelo de Datos (ERD)](#1-modelo-de-datos-erd)
   - 1.1 Dominio Operacional
   - 1.2 Dominio de Inteligencia Artificial
2. [Modelo de Arquitectura](#2-modelo-de-arquitectura)
3. [Modelo de Capas](#3-modelo-de-capas)
4. [Modelo de Despliegue](#4-modelo-de-despliegue)
5. [Flujo del Módulo IA — Comparación Automática](#5-flujo-del-módulo-ia--comparación-automática)
6. [Arquitectura del Transformer Híbrido](#6-arquitectura-del-transformer-híbrido)
7. [Flujo de la Prueba Diebold-Mariano](#7-flujo-de-la-prueba-diebold-mariano)
8. [Diagrama de Casos de Uso](#8-diagrama-de-casos-de-uso)
9. [Diagrama de Secuencia — Comparación de Modelos](#9-diagrama-de-secuencia--comparación-de-modelos)

---

## 1. Modelo de Datos (ERD)

### 1.1 Dominio Operacional

Entidades principales del sistema de gestión restaurante-PyME.

```mermaid
erDiagram
    roles {
        int id_rol PK
        string nombre
        string descripcion
        bool estado
    }

    permisos {
        int id_permiso PK
        int id_rol FK
        string modulo
        string accion
    }

    usuarios {
        int id_usuario PK
        int id_rol FK
        string nombre
        string apellido
        string correo
        string usuario
        string contrasena
        bool estado
        datetime ultimo_acceso
    }

    sesiones {
        int id_sesion PK
        int id_usuario FK
        datetime fecha_ingreso
        datetime fecha_salida
        string ip_equipo
        string estado
    }

    restaurantes {
        int id_restaurante PK
        string nombre_comercial
        string ruc
        string distrito
        string provincia
        bool estado
    }

    clientes {
        int id_cliente PK
        int id_restaurante FK
        string nombre
        string tipo_documento
        string numero_documento
    }

    proveedores {
        int id_proveedor PK
        string nombre
        string tipo_documento
        string numero_documento
        string contacto
    }

    platos {
        int id_plato PK
        int id_restaurante FK
        string nombre
        string categoria
        decimal precio_venta
        decimal costo_estimado
        bool estado
    }

    insumos {
        int id_insumo PK
        int id_restaurante FK
        int id_proveedor FK
        string nombre
        decimal stock_disponible
        decimal stock_minimo
        date fecha_vencimiento
    }

    recetas {
        int id_receta PK
        int id_plato FK
        int id_insumo FK
        decimal cantidad_usada
        string unidad_medida
    }

    ventas {
        int id_venta PK
        int id_restaurante FK
        int id_usuario FK
        int id_cliente FK
        date fecha
        decimal total
        string metodo_pago
        string tipo_comprobante
    }

    detalle_ventas {
        int id_detalle PK
        int id_venta FK
        int id_plato FK
        int cantidad
        decimal precio_unitario
        decimal subtotal
    }

    producciones {
        int id_produccion PK
        int id_restaurante FK
        int id_plato FK
        int id_usuario FK
        date fecha
        int cantidad_preparada
        int cantidad_vendida
        int cantidad_sobrante
    }

    desperdicios {
        int id_desperdicio PK
        int id_restaurante FK
        int id_plato FK
        int id_insumo FK
        int id_usuario FK
        date fecha
        string tipo
        decimal cantidad
        string motivo
        decimal costo_estimado
    }

    bitacora {
        int id_bitacora PK
        int id_usuario FK
        string modulo
        string accion
        date fecha
        string resultado
    }

    configuracion {
        int id_configuracion PK
        string clave
        string valor
        string descripcion
    }

    alertas {
        int id_alerta PK
        int id_restaurante FK
        string tipo
        string titulo
        string severidad
        bool enviado_n8n
    }

    roles ||--o{ permisos        : "tiene"
    roles ||--o{ usuarios        : "asignado a"
    usuarios ||--o{ sesiones     : "genera"
    usuarios ||--o{ bitacora     : "registra"
    restaurantes ||--o{ platos   : "ofrece"
    restaurantes ||--o{ insumos  : "gestiona"
    restaurantes ||--o{ ventas   : "registra"
    restaurantes ||--o{ clientes : "atiende"
    restaurantes ||--o{ alertas  : "recibe"
    proveedores ||--o{ insumos   : "suministra"
    platos ||--o{ recetas        : "compuesto por"
    insumos ||--o{ recetas       : "ingrediente de"
    ventas ||--o{ detalle_ventas : "contiene"
    platos ||--o{ detalle_ventas : "vendido en"
    platos ||--o{ producciones   : "producido en"
    platos ||--o{ desperdicios   : "desperdiciado en"
    insumos ||--o{ desperdicios  : "desperdiciado en"
    usuarios ||--o{ ventas       : "registra"
    usuarios ||--o{ producciones : "registra"
    usuarios ||--o{ desperdicios : "registra"
    clientes ||--o{ ventas       : "realiza"
```

---

### 1.2 Dominio de Inteligencia Artificial

Tablas del módulo de predicción y comparación automática de modelos.

```mermaid
erDiagram
    platos {
        int id_plato PK
        string nombre
        string categoria
        decimal precio_venta
    }

    usuarios {
        int id_usuario PK
        string nombre
        string correo
    }

    predicciones {
        int id_prediccion PK
        int id_plato FK
        int id_usuario FK
        int id_restaurante FK
        date fecha_objetivo
        float demanda_estimada
        int recomendacion_produccion
        string riesgo_desperdicio
        string modelo_usado
        float mae
        float r2
        float confianza
        datetime fecha_generacion
    }

    comparaciones_modelos {
        int id_comparacion PK
        int id_plato FK
        int id_usuario FK
        datetime fecha_comparacion
        string modelo_ganador
        int dias_adelante
        int clima
        int evento
        float mae_arima
        float rmse_arima
        float mape_arima
        float r2_arima
        float mae_prophet
        float rmse_prophet
        float mape_prophet
        float r2_prophet
        float mae_transformer
        float rmse_transformer
        float mape_transformer
        float r2_transformer
        float dm_estadistico
        float dm_p_valor
        bool dm_significativo
        string dm_interpretacion
    }

    platos ||--o{ predicciones          : "predicho en"
    platos ||--o{ comparaciones_modelos : "comparado en"
    usuarios ||--o{ predicciones          : "ejecuta"
    usuarios ||--o{ comparaciones_modelos : "ejecuta"
```

---

## 2. Modelo de Arquitectura

Visión general de los componentes del sistema y sus interacciones.

```mermaid
flowchart TB
    subgraph CLIENTE["Capa de Presentación — Navegador Web"]
        direction LR
        UI["React 18 + TypeScript\nVite · Tailwind CSS"]
        CHARTS["Recharts\nVisualización"]
        AXIOS["Axios\nCliente HTTP"]
        UI --- CHARTS
        UI --- AXIOS
    end

    subgraph BACKEND["Capa de Aplicación — Servidor FastAPI"]
        direction TB
        FASTAPI["FastAPI 0.111\nUvicorn ASGI"]
        AUTH["JWT Auth\npython-jose · bcrypt"]
        subgraph ROUTERS["Routers"]
            R1["auth · usuarios · roles"]
            R2["restaurantes · platos · insumos"]
            R3["ventas · produccion · desperdicio"]
            R4["dashboard · estadisticas · reportes"]
            R5["ia_prediccion"]
        end
        FASTAPI --> AUTH
        FASTAPI --> ROUTERS
    end

    subgraph IA["Módulo de IA — ia/"]
        direction TB
        PRED["predictor.py\nRF · LR · DT · Transformer Híbrido"]
        COMP["comparador_modelos.py\nARIMA · Prophet · Transformer"]
        ARIMA["statsmodels\nARIMA auto-(p,d,q)"]
        PROPHET["prophet\nMeta/Facebook"]
        TRANSF["HybridTransformerModel\nMHA + Ensemble + Ridge"]
        DM["Prueba Diebold-Mariano\nscipy · stats"]
        COMP --> ARIMA
        COMP --> PROPHET
        COMP --> TRANSF
        COMP --> DM
    end

    subgraph BD["Capa de Datos"]
        direction LR
        ORM["SQLAlchemy 2.0\nORM"]
        DB[("PostgreSQL 15\nSQLite (dev)")]
        ORM --> DB
    end

    AXIOS -->|"HTTP/JSON :8000/api"| FASTAPI
    R5 --> PRED
    R5 --> COMP
    BACKEND --> ORM

    style CLIENTE fill:#e0f2fe,stroke:#0284c7
    style BACKEND fill:#f0fdf4,stroke:#16a34a
    style IA     fill:#faf5ff,stroke:#9333ea
    style BD     fill:#fff7ed,stroke:#ea580c
```

---

## 3. Modelo de Capas

Arquitectura en cuatro capas siguiendo el patrón N-Tier.

```mermaid
flowchart TD
    subgraph L1["CAPA 1 — Presentación"]
        direction LR
        L1A["Páginas React\nDashboard · Ventas · IA · Platos · ..."]
        L1B["Componentes UI\nTailwind CSS · Recharts · Lucide Icons"]
        L1C["Estado\nuseState · useEffect"]
    end

    subgraph L2["CAPA 2 — Aplicación"]
        direction LR
        L2A["FastAPI Routers\n21 módulos de negocio"]
        L2B["Autenticación\nJWT · bcrypt · RBAC"]
        L2C["Schemas Pydantic\nValidación entrada/salida"]
    end

    subgraph L3["CAPA 3 — Dominio / IA"]
        direction LR
        L3A["Lógica de Negocio\npredicciones · reportes · alertas"]
        L3B["Modelos ML\npredictor.py"]
        L3C["Comparador\ncomparador_modelos.py\nARIMA · Prophet · Transformer · DM"]
    end

    subgraph L4["CAPA 4 — Datos"]
        direction LR
        L4A["ORM SQLAlchemy\n15 modelos de dominio"]
        L4B[("Base de Datos\nPostgreSQL / SQLite")]
    end

    L1 -->|"Axios HTTP/JSON"| L2
    L2 -->|"Llamadas Python"| L3
    L3 -->|"Queries ORM"| L4

    style L1 fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    style L2 fill:#dcfce7,stroke:#22c55e,color:#14532d
    style L3 fill:#ede9fe,stroke:#8b5cf6,color:#3b0764
    style L4 fill:#ffedd5,stroke:#f97316,color:#7c2d12
```

---

## 4. Modelo de Despliegue

Infraestructura de ejecución para desarrollo y producción.

```mermaid
flowchart LR
    subgraph DEV["Entorno de Desarrollo (localhost)"]
        direction TB
        subgraph PC["Máquina del Desarrollador"]
            BROWSER["Navegador Web\nChrome / Firefox / Edge"]

            subgraph VITE["Vite Dev Server :5173"]
                REACT["React + TypeScript\nHot Module Replacement"]
            end

            subgraph UVICORN["Uvicorn :8000"]
                FAPI["FastAPI\n+ Routers + IA"]
            end

            subgraph DBDEV["Base de Datos"]
                SQLITE[("SQLite\nsigpda.db")]
            end
        end
    end

    subgraph PROD["Entorno de Producción"]
        direction TB
        subgraph SERVER["Servidor Linux (VPS / Cloud)"]
            NGINX["Nginx\nProxy inverso :80 / :443"]

            subgraph APP["Proceso Python"]
                GUNICORN["Gunicorn + Uvicorn Workers\nFastAPI"]
                IA_MOD["Módulo IA\npredictor + comparador"]
            end

            subgraph DBPROD["Base de Datos"]
                POSTGRES[("PostgreSQL 15\nsigpda_prod")]
            end
        end

        CLIENT_PROD["Navegador del\nUsuario Final"]
    end

    BROWSER -->|":5173"| VITE
    VITE -->|"HTTP :8000/api"| UVICORN
    UVICORN --- SQLITE

    CLIENT_PROD -->|"HTTPS :443"| NGINX
    NGINX -->|"proxy_pass :8000"| GUNICORN
    GUNICORN --- IA_MOD
    GUNICORN --- POSTGRES

    style DEV  fill:#f0f9ff,stroke:#0ea5e9
    style PROD fill:#fef9ee,stroke:#f59e0b
```

---

## 5. Flujo del Módulo IA — Comparación Automática

Flujo interno de la función `comparar_modelos_prediccion()` en `ia/comparador_modelos.py`.

```mermaid
flowchart TD
    START(["POST /api/ia/comparar-modelos\n{id_plato, dias_adelante, clima, evento}"])

    A["1. Construir dataset histórico\nconstruir_dataset_historico()"]
    B{"Datos\nexisten?"}
    ERR1(["Error 400\nSin datos históricos"])

    C["2. Enriquecer features\nenriquecer_features()"]
    D["3. Filtrar por id_plato"]
    E{"Plato tiene\ndatos?"}
    ERR2(["Error 400\nSin datos para el plato"])

    F["4. Serie temporal diaria\n_preparar_serie_diaria()\nRelleno lineal de fechas faltantes"]
    G{"n_datos\n>= 30?"}
    ERR3(["Error 400\nMínimo 30 días requeridos"])

    H["5. Split temporal cronológico\n80% entrenamiento / 20% prueba\nNO aleatorio — por fecha de corte"]

    subgraph TRAIN["6. Entrenamiento de los tres modelos"]
        T1["ARIMA\nADF → d\nBúsqueda AIC → p, d, q\nforecast(n_test)"]
        T2["Prophet\nHiperparámetros automáticos\nseasonality · changepoint\npredict(fechas_test)"]
        T3["Transformer Híbrido\nn_heads y d_k automáticos\nMHA + Ensemble + Ridge\npredict(X_test)"]
    end

    I["7. Calcular métricas\nMAE · RMSE · MAPE · R²\npara cada modelo"]
    J["8. Seleccionar ganador\nmin(MAE)"]

    subgraph DM["9. Prueba Diebold-Mariano"]
        DM1["d_t = e_alt² - e_gan²"]
        DM2["V̂ = (γ₀ + 2γ₁) / n\nNewey-West"]
        DM3["DM = d̄ / sqrt(V̂)"]
        DM4{"p-valor\n< 0.05?"}
        DM5["Significativo\nGanador es superior"]
        DM6["No significativo\nSin diferencia formal"]
        DM1 --> DM2 --> DM3 --> DM4
        DM4 -->|"Sí"| DM5
        DM4 -->|"No"| DM6
    end

    K["10. Predicciones futuras\ncon modelo ganador\ndias_adelante pasos"]
    L["11. Persistir en BD\ncomparaciones_modelos"]
    END(["Respuesta JSON\nmodelo_ganador · métricas\nDM · predicciones · explicación"])

    START --> A --> B
    B -->|"No"| ERR1
    B -->|"Sí"| C --> D --> E
    E -->|"No"| ERR2
    E -->|"Sí"| F --> G
    G -->|"No"| ERR3
    G -->|"Sí"| H --> TRAIN --> I --> J --> DM --> K --> L --> END

    style TRAIN fill:#ede9fe,stroke:#7c3aed
    style DM    fill:#fef3c7,stroke:#d97706
    style ERR1  fill:#fee2e2,stroke:#ef4444
    style ERR2  fill:#fee2e2,stroke:#ef4444
    style ERR3  fill:#fee2e2,stroke:#ef4444
    style START fill:#dcfce7,stroke:#16a34a
    style END   fill:#dcfce7,stroke:#16a34a
```

---

## 6. Arquitectura del Transformer Híbrido

Modelo propuesto de la tesis: Multi-Head Self-Attention + Ensemble + Ridge Meta-Learner, implementado en NumPy puro (sin PyTorch ni TensorFlow).

```mermaid
flowchart TD
    subgraph IN["Entrada"]
        X["Vector de features x ∈ R^8\ndia_semana · mes · dia_mes · es_finde\nclima · evento · cat_enc · ventas_7d"]
    end

    subgraph NORM["Normalización"]
        SC["StandardScaler\nmu=0  sigma=1"]
    end

    subgraph ATTN["Multi-Head Self-Attention (NumPy)"]
        direction LR
        H1["Cabeza 1\nQ·K·V / sqrt(d_k)"]
        H2["Cabeza 2\nQ·K·V / sqrt(d_k)"]
        H3["Cabeza 3\nQ·K·V / sqrt(d_k)"]
        H4["Cabeza 4\nQ·K·V / sqrt(d_k)"]
        CONCAT["Concat + W_O"]
        RES1["Residual + LayerNorm"]
        FFN["Feed-Forward\nReLU + Residual + LayerNorm"]
        H1 & H2 & H3 & H4 --> CONCAT --> RES1 --> FFN
    end

    subgraph MERGE["Concatenación de representaciones"]
        CAT["x_original concat x_atendido  en R^16"]
    end

    subgraph ENS["Ensemble de modelos base"]
        direction LR
        RF["Random Forest\nn=150  depth=10"]
        GBR["Gradient Boosting\nn=100  lr=0.08"]
        LR["Regresión\nLineal"]
        DT["Árbol de\nDecisión  depth=7"]
    end

    subgraph META["Meta-Learner"]
        RIDGE["Ridge Regression alpha=0.5\ncombina predicciones OOF"]
    end

    subgraph OUT["Salida"]
        PRED["demanda estimada (unidades >= 0)"]
        REC["recomendacion_produccion\nriesgo_desperdicio"]
    end

    X --> SC --> ATTN
    SC -->|"x original"| MERGE
    FFN -->|"x atendido"| MERGE
    MERGE --> RF & GBR & LR & DT
    RF & GBR & LR & DT --> RIDGE
    RIDGE --> PRED --> REC

    style IN   fill:#dbeafe,stroke:#3b82f6
    style ATTN fill:#ede9fe,stroke:#7c3aed
    style ENS  fill:#dcfce7,stroke:#16a34a
    style META fill:#fef3c7,stroke:#d97706
    style OUT  fill:#fee2e2,stroke:#ef4444
```

### Hiperparámetros automáticos del Transformer

| Tamaño del dataset | n_heads | d_k | Dimensión de atención |
|---|---|---|---|
| n >= 200 muestras | 4 | 16 | 64 |
| 100 <= n < 200    | 4 | 8  | 32 |
| 50 <= n < 100     | 2 | 8  | 16 |
| n < 50            | 2 | 4  | 8  |

---

## 7. Flujo de la Prueba Diebold-Mariano

Implementación de la prueba estadística de Diebold & Mariano (1995) para validar que la diferencia de precisión entre el modelo ganador y los demás es estadísticamente significativa.

```mermaid
flowchart TD
    subgraph INPUT["Entrada"]
        E1["e1 = errores absolutos del modelo alternativo\ne2 = errores absolutos del modelo ganador\n(mismo período de prueba, misma longitud n)"]
    end

    A["Diferencial de pérdida cuadrática\nd_t = e1_t^2 - e2_t^2"]
    B["Media del diferencial\nd_barra = (1/n) * suma(d_t)"]

    subgraph VAR["Estimación de varianza espectral — Newey-West (h=1)"]
        V1["gamma_0 = Var(d)  con ddof=1"]
        V2["gamma_1 = Cov(d_t, d_{t-1})  con ddof=1"]
        V3["V_hat = (gamma_0 + 2*gamma_1) / n"]
        V1 & V2 --> V3
    end

    C["Estadístico DM\nDM = d_barra / sqrt(|V_hat|)"]
    D["p-valor bilateral\np = 2 * (1 - Fi(|DM|))"]

    subgraph DEC["Decisión estadística"]
        E{"p < 0.05?"}
        F["Rechazar H0\nDiferencia significativa al 5%\nGanador es formalmente superior"]
        G["No rechazar H0\nSin diferencia estadísticamente\nsignificativa entre modelos"]
    end

    subgraph OUT["Salida JSON"]
        R["estadistico · p_valor\nsignificativo · interpretacion\nmodelo_1 · modelo_2"]
    end

    INPUT --> A --> B --> VAR --> C --> D --> E
    E -->|"Sí"| F --> R
    E -->|"No"| G --> R

    subgraph HIP["Hipótesis"]
        H0["H0: E[d_t] = 0  (igual precisión predictiva)"]
        H1_["H1: E[d_t] != 0  (distinta precisión predictiva)"]
        NOTE["DM > 0  ->  modelo ganador es más preciso\nDM < 0  ->  modelo alternativo es más preciso"]
    end

    style INPUT fill:#dbeafe,stroke:#3b82f6
    style VAR   fill:#fef3c7,stroke:#d97706
    style DEC   fill:#ede9fe,stroke:#7c3aed
    style OUT   fill:#dcfce7,stroke:#16a34a
    style HIP   fill:#f8fafc,stroke:#94a3b8
```

---

## 8. Diagrama de Casos de Uso

```mermaid
flowchart LR
    subgraph ACTORES["Actores"]
        ADM["Administrador"]
        GER["Gerente"]
        TRA["Trabajador"]
        ANA["Analista"]
    end

    subgraph UC["Casos de Uso — SIGPDA"]
        direction TB

        subgraph GESTION["Gestión Operativa"]
            UC1["Registrar Venta"]
            UC2["Registrar Producción"]
            UC3["Registrar Desperdicio"]
            UC4["Gestionar Insumos"]
            UC5["Gestionar Platos"]
        end

        subgraph IA_UC["Módulo de IA"]
            UC6["Ejecutar Predicción Individual\nRF · LR · DT · Transformer"]
            UC7["Comparar Modelos Automáticamente\nARIMA · Prophet · Transformer + DM"]
            UC8["Ver Historial de Predicciones"]
        end

        subgraph REPORTES["Reportes y Analítica"]
            UC9["Ver Dashboard BI"]
            UC10["Ver Estadísticas"]
            UC11["Generar Reporte PDF"]
            UC12["Exportar Excel / CSV"]
        end

        subgraph ADMIN["Administración"]
            UC13["Gestionar Usuarios"]
            UC14["Gestionar Roles y Permisos"]
            UC15["Ver Bitácora"]
            UC16["Configurar Sistema"]
        end
    end

    ADM --> UC1 & UC2 & UC3 & UC4 & UC5
    ADM --> UC6 & UC7 & UC8
    ADM --> UC9 & UC10 & UC11 & UC12
    ADM --> UC13 & UC14 & UC15 & UC16

    GER --> UC1 & UC2 & UC3
    GER --> UC6 & UC7 & UC8
    GER --> UC9 & UC10 & UC11 & UC12

    TRA --> UC1 & UC2 & UC3 & UC4
    TRA --> UC6

    ANA --> UC6 & UC7 & UC8
    ANA --> UC9 & UC10 & UC11 & UC12

    style IA_UC    fill:#ede9fe,stroke:#7c3aed
    style GESTION  fill:#dcfce7,stroke:#16a34a
    style REPORTES fill:#dbeafe,stroke:#3b82f6
    style ADMIN    fill:#fef3c7,stroke:#d97706
```

---

## 9. Diagrama de Secuencia — Comparación de Modelos

Interacción completa al ejecutar una comparación automática desde el frontend.

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as React (Frontend)
    participant API as FastAPI Router
    participant CM as comparador_modelos.py
    participant BD as Base de Datos

    U->>FE: Selecciona plato, días, clima, evento
    U->>FE: Clic "Comparar modelos automáticamente"

    FE->>API: POST /api/ia/comparar-modelos
    Note right of FE: { id_plato, dias_adelante,<br/>clima, evento }

    API->>API: Validar token JWT
    API->>CM: comparar_modelos_prediccion(...)

    CM->>BD: SELECT ventas JOIN detalle_ventas JOIN platos
    BD-->>CM: Historial de ventas del plato

    CM->>CM: enriquecer_features()
    CM->>CM: _preparar_serie_diaria()
    CM->>CM: Split temporal 80% train / 20% test

    Note over CM: Entrenamiento de los tres modelos

    CM->>CM: entrenar_evaluar_arima()
    Note right of CM: ADF test + búsqueda AIC<br/>auto-selección (p,d,q)

    CM->>CM: entrenar_evaluar_prophet()
    Note right of CM: Hiperparámetros automáticos<br/>según longitud de la serie

    CM->>CM: entrenar_evaluar_transformer()
    Note right of CM: n_heads y d_k automáticos<br/>según tamaño del dataset

    CM->>CM: calcular_metricas() — MAE, RMSE, MAPE, R²
    CM->>CM: Seleccionar ganador — min(MAE)
    CM->>CM: prueba_diebold_mariano() — ganador vs alternativas
    CM->>CM: Generar predicciones futuras con modelo ganador

    CM-->>API: Resultado completo (dict)

    API->>BD: INSERT INTO comparaciones_modelos
    BD-->>API: OK — id_comparacion generado

    API-->>FE: 200 OK — JSON con métricas y predicciones

    FE->>FE: Renderizar tabla comparativa
    FE->>FE: Renderizar resultado Diebold-Mariano
    FE->>FE: Renderizar gráfico de predicciones
    FE->>FE: Mostrar explicación interpretable

    FE-->>U: Resultado visual completo
```

---

## Convenciones

| Símbolo / Término | Significado |
|---|---|
| `PK` | Clave primaria (Primary Key) |
| `FK` | Clave foránea (Foreign Key) |
| `\|\|--o{` | Relación uno a muchos |
| `\|\|--\|\|` | Relación uno a uno |
| MAE | Mean Absolute Error — Error Absoluto Medio |
| RMSE | Root Mean Square Error — Raíz del Error Cuadrático Medio |
| MAPE | Mean Absolute Percentage Error — Error Porcentual Absoluto Medio |
| R² | Coeficiente de determinación (bondad de ajuste) |
| DM | Estadístico Diebold-Mariano |
| MHA | Multi-Head Self-Attention |
| OOF | Out-Of-Fold (predicciones fuera de pliegue para el meta-learner) |
| AIC | Criterio de Información de Akaike (selección de orden ARIMA) |
| ADF | Augmented Dickey-Fuller (prueba de estacionariedad) |
| RBAC | Role-Based Access Control (control de acceso por roles) |
| JWT | JSON Web Token (autenticación sin estado) |

---

## 10. Flujo del Motor de Alertas Inteligentes

Muestra cómo el backend analiza el estado del sistema, detecta patrones de riesgo y genera alertas persistidas en la BD — sin depender de n8n ni servicios externos.

```mermaid
flowchart TD
    TRIGGER([Solicitud POST /generar\nclima + evento]) --> MOTOR

    subgraph MOTOR["Motor de Alertas — backend/services/alertas_inteligentes.py"]
        direction TB
        A1["1 Sobreproducción\n(sobrante/preparado ≥ 10 %)"]
        A2["2 Próximo a vencer\n(insumo vence ≤ 7 días)"]
        A3["3 Stock excesivo\n(stock > 3× mínimo)"]
        A4["4 Baja demanda\n(caída ventas > 20 %)"]
        A5["5 Alto desperdicio\n(costo últimos 30 días)"]
        A6["6 Recomendación menú\n(0 ventas en 30 días)"]
        A7["7 Alerta crítica\n(baja demanda + alto desperdicio)"]
    end

    MOTOR --> DUP{¿Alerta pendiente\ndel mismo tipo\nen las últimas 24 h?}
    DUP -->|Sí| SKIP[Omitir — evitar duplicados]
    DUP -->|No| NIVEL

    NIVEL["Calcular nivel de riesgo\nBAJO / MEDIO / ALTO / CRITICO\nSegún umbrales por tipo"] --> REC
    REC["Generar recomendación operativa\nTexto adaptado a clima y evento"] --> SAVE

    SAVE[("alertas_inteligentes\nBD — SQLite / PostgreSQL")] --> RESP

    RESP([Respuesta JSON\ntotal_generadas + desglose\npor tipo y nivel])

    style MOTOR fill:#f0f4ff,stroke:#6366f1
    style SAVE fill:#ecfdf5,stroke:#10b981
```

### Flujo de estados de una alerta

```mermaid
stateDiagram-v2
    [*] --> pendiente : generar_alertas_inteligentes()
    pendiente --> leida : PUT /marcar-leida
    pendiente --> resuelta : PUT /resolver
    leida --> resuelta : PUT /resolver
    resuelta --> [*]
```

### Integración con el Dashboard

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant DB as Base de Datos

    U->>FE: Abre Dashboard
    FE->>API: GET /api/dashboard/kpis
    API->>DB: COUNT alertas nivel ALTO/CRITICO estado=pendiente
    DB-->>API: alertas_criticas = N
    API-->>FE: { ..., alertas_criticas: N }
    FE->>U: StatCard "Alertas críticas: N"

    U->>FE: Navega a Alertas Inteligentes
    FE->>API: POST /api/alertas-inteligentes/generar
    API->>DB: Analiza producciones, insumos, ventas, desperdicios
    DB-->>API: Datos operativos
    API->>DB: INSERT INTO alertas_inteligentes (nuevas alertas)
    API-->>FE: { total_generadas, por_tipo, por_nivel }
    FE->>U: Tarjetas de alerta con recomendaciones
```

---

## Referencias

- Diebold, F.X. & Mariano, R.S. (1995). *Comparing Predictive Accuracy*. Journal of Business & Economic Statistics, 13(3), 253–263.
- Taylor, S.J. & Letham, B. (2018). *Forecasting at scale*. The American Statistician, 72(1), 37–45.
- Box, G.E.P., Jenkins, G.M. & Reinsel, G.C. (2015). *Time Series Analysis: Forecasting and Control* (5th ed.). Wiley.
- Vaswani, A. et al. (2017). *Attention is All You Need*. Advances in Neural Information Processing Systems (NeurIPS 2017).
- Newey, W.K. & West, K.D. (1987). *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*. Econometrica, 55(3), 703–708.
