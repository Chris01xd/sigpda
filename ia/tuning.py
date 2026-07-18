"""
=================================================================
SIGPDA - Optimización de hiperparámetros con validación temporal
=================================================================
NO usa Optuna. NO usa validación aleatoria (KFold).

- Para los regresores scikit-learn internos de los modelos híbridos
  (Random Forest, Gradient Boosting): RandomizedSearchCV + TimeSeriesSplit.
- Para los modelos estadísticos clásicos (ARIMA, Prophet, Holt-Winters),
  que no son estimadores de scikit-learn: una búsqueda aleatoria propia
  que respeta el orden temporal, evaluando cada combinación sobre un
  único split train/validation cronológico (el tramo final de la serie).

Cada búsqueda registra: espacio de búsqueda, combinaciones evaluadas,
mejor configuración, métrica objetivo, valor obtenido, tiempo empleado,
semilla y fecha de ejecución — para reproducibilidad y trazabilidad.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ia.metricas import calcular_metricas

SEMILLA_DEFECTO = 42
N_COMBINACIONES_DEFECTO = 8

# Espacios de búsqueda razonables y computacionalmente viables en un
# equipo de estudiante (ver CLAUDE.md sección 10).
ESPACIOS_BUSQUEDA = {
    "arima": {
        "p": [0, 1, 2, 3],
        "d": [0, 1, 2],
        "q": [0, 1, 2, 3],
    },
    "prophet": {
        "changepoint_prior_scale": [0.01, 0.05, 0.1, 0.5],
        "seasonality_prior_scale": [1.0, 5.0, 10.0, 20.0],
        "seasonality_mode": ["additive", "multiplicative"],
        "weekly_seasonality": [True, False],
    },
    "holt_winters": {
        "trend": ["add"],
        "damped_trend": [True, False],
        "seasonal": ["add", None],
        "seasonal_periods": [7],
    },
    "transformer_random_forest": {
        "n_estimators": [80, 120, 150, 200],
        "max_depth": [6, 8, 10, 14, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", None],
    },
    "transformer_gradient_boosting": {
        "n_estimators": [60, 100, 150],
        "learning_rate": [0.03, 0.05, 0.08, 0.12],
        "max_depth": [3, 4, 5],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "subsample": [0.7, 0.85, 1.0],
    },
}


def _tamano_espacio(espacio: dict) -> int:
    total = 1
    for valores in espacio.values():
        total *= len(valores)
    return total


def _muestrear_combinaciones(espacio: dict, n: int, semilla: int) -> list[dict]:
    """Muestreo aleatorio sin repetición del espacio de búsqueda (semilla fija)."""
    rng = random.Random(semilla)
    claves = list(espacio.keys())
    n = min(n, _tamano_espacio(espacio))

    combinaciones: list[dict] = []
    vistas: set[tuple] = set()
    intentos = 0
    max_intentos = max(50, n * 20)

    while len(combinaciones) < n and intentos < max_intentos:
        intentos += 1
        combo = {k: rng.choice(espacio[k]) for k in claves}
        firma = tuple(sorted(combo.items(), key=lambda kv: kv[0]))
        if firma in vistas:
            continue
        vistas.add(firma)
        combinaciones.append(combo)

    return combinaciones


def buscar_hiperparametros_temporal(
    nombre_modelo: str,
    entrenar_evaluar_fn,
    serie: pd.DataFrame,
    n_combinaciones: int = N_COMBINACIONES_DEFECTO,
    semilla: int = SEMILLA_DEFECTO,
    val_size: float = 0.2,
) -> dict:
    """
    Búsqueda aleatoria de hiperparámetros respetando el orden temporal.

    `entrenar_evaluar_fn` debe aceptar (serie_train, serie_val, **hiperparametros)
    y retornar (pred_val, errores_abs, info). Evalúa cada combinación sobre
    UN único split train/val cronológico (no aleatorio, no k-fold).
    """
    espacio = ESPACIOS_BUSQUEDA.get(nombre_modelo, {})
    if not espacio:
        return {"aplicable": False, "motivo": f"Sin espacio de búsqueda definido para '{nombre_modelo}'."}

    n = len(serie)
    n_val = max(3, int(n * val_size))
    if n - n_val < 5:
        return {
            "aplicable": False,
            "motivo": f"Datos insuficientes ({n} observaciones) para tuning con validación temporal.",
        }

    serie_train = serie.iloc[:n - n_val].reset_index(drop=True)
    serie_val = serie.iloc[n - n_val:].reset_index(drop=True)
    y_val = serie_val["cantidad"].values.astype(float)

    combinaciones = _muestrear_combinaciones(espacio, n_combinaciones, semilla)
    resultados = []
    t0_total = time.perf_counter()

    for combo in combinaciones:
        t0 = time.perf_counter()
        try:
            pred, _errores, _info = entrenar_evaluar_fn(serie_train, serie_val, **combo)
            metricas = calcular_metricas(y_val, pred, valor_anterior=float(serie_train["cantidad"].iloc[-1]))
            resultados.append({
                "hiperparametros": combo,
                "mae": metricas["mae"],
                "rmse": metricas["rmse"],
                "tiempo": round(time.perf_counter() - t0, 4),
            })
        except Exception as exc:
            resultados.append({
                "hiperparametros": combo,
                "mae": None,
                "rmse": None,
                "tiempo": round(time.perf_counter() - t0, 4),
                "error": str(exc),
            })

    validos = [r for r in resultados if r["mae"] is not None]
    mejor = min(validos, key=lambda r: r["mae"]) if validos else None

    return {
        "aplicable": True,
        "modelo": nombre_modelo,
        "espacio_busqueda": espacio,
        "combinaciones_evaluadas": resultados,
        "n_combinaciones": len(combinaciones),
        "mejor_hiperparametros": mejor["hiperparametros"] if mejor else None,
        "metrica_objetivo": "mae",
        "mejor_valor": mejor["mae"] if mejor else None,
        "tiempo_total": round(time.perf_counter() - t0_total, 4),
        "semilla": semilla,
        "fecha_ejecucion": datetime.now(timezone.utc).isoformat(),
    }


def buscar_hiperparametros_regresor_sklearn(
    nombre_modelo: str,
    regresor_base,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    n_iter: int = 10,
    semilla: int = SEMILLA_DEFECTO,
) -> dict:
    """
    RandomizedSearchCV + TimeSeriesSplit sobre el regresor interno
    (Random Forest o Gradient Boosting) de un modelo híbrido, operando
    sobre la matriz de features ya expandida por la capa de atención.
    """
    from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

    espacio = ESPACIOS_BUSQUEDA.get(nombre_modelo, {})
    if not espacio:
        return {"aplicable": False, "motivo": f"Sin espacio de búsqueda definido para '{nombre_modelo}'."}

    n_splits_efectivo = min(n_splits, max(2, len(X) - 1))
    if len(X) < n_splits_efectivo + 1:
        return {
            "aplicable": False,
            "motivo": f"Datos insuficientes ({len(X)} observaciones) para tuning con TimeSeriesSplit.",
        }

    tscv = TimeSeriesSplit(n_splits=n_splits_efectivo)
    n_iter_efectivo = min(n_iter, _tamano_espacio(espacio))

    t0 = time.perf_counter()
    buscador = RandomizedSearchCV(
        estimator=regresor_base,
        param_distributions=espacio,
        n_iter=n_iter_efectivo,
        cv=tscv,
        scoring="neg_mean_absolute_error",
        random_state=semilla,
        n_jobs=-1,
    )
    buscador.fit(X, y)
    tiempo_total = time.perf_counter() - t0

    return {
        "aplicable": True,
        "modelo": nombre_modelo,
        "espacio_busqueda": espacio,
        "n_combinaciones": n_iter_efectivo,
        "mejor_hiperparametros": buscador.best_params_,
        "metrica_objetivo": "mae",
        "mejor_valor": round(float(-buscador.best_score_), 4),
        "tiempo_total": round(tiempo_total, 4),
        "semilla": semilla,
        "fecha_ejecucion": datetime.now(timezone.utc).isoformat(),
    }
