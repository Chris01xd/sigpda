"""
=================================================================
SIGPDA - Validación cruzada temporal (walk-forward, hasta 5 folds)
=================================================================
Usa TimeSeriesSplit (walk-forward): cada fold de validación viene
DESPUÉS de su fold de entrenamiento en el tiempo, nunca se mezclan
fechas futuras en folds anteriores. No se usa KFold aleatorio.

Si no hay datos suficientes para el número de folds solicitado, se
reduce automáticamente y se informa mediante advertencias, sin
lanzar errores internos.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from ia.metricas import calcular_metricas

MAX_FOLDS = 5
NOMBRES_METRICAS = ("mae", "rmse", "mape", "smape", "u_theil", "r2")


def generar_folds_temporales(n_muestras: int, n_splits: int = MAX_FOLDS) -> tuple[list, int, list[str]]:
    """
    Genera los índices de folds walk-forward mediante TimeSeriesSplit.

    Retorna (folds, n_splits_efectivo, advertencias). `folds` es una
    lista de tuplas (idx_train, idx_val); vacía si no hay datos
    suficientes para al menos 2 folds.
    """
    advertencias: list[str] = []
    n_splits_efectivo = min(n_splits, max(0, n_muestras - 1))

    if n_splits_efectivo < 2:
        return [], 0, [
            f"Datos insuficientes ({n_muestras} observaciones) para ejecutar "
            f"validación cruzada temporal; se requieren al menos 3 observaciones "
            f"para poder generar 2 folds."
        ]

    if n_splits_efectivo < n_splits:
        advertencias.append(
            f"Solo se pudieron ejecutar {n_splits_efectivo} de {n_splits} folds "
            f"solicitados debido a datos insuficientes ({n_muestras} observaciones)."
        )

    tscv = TimeSeriesSplit(n_splits=n_splits_efectivo)
    folds = list(tscv.split(np.arange(n_muestras)))
    return folds, n_splits_efectivo, advertencias


def evaluar_modelo_cv(
    entrenar_evaluar_fn,
    serie: pd.DataFrame,
    n_splits: int = MAX_FOLDS,
) -> dict:
    """
    Ejecuta validación cruzada temporal (walk-forward) para un modelo.

    `entrenar_evaluar_fn` debe seguir el contrato:
        (serie_train, serie_val) -> (pred_val, errores_abs, info)
    Para modelos que requieren contexto adicional (los híbridos, que
    necesitan df_plato_train/cat_enc/clima/evento), el llamador debe
    envolver la función en un closure/functools.partial que también
    recorte ese contexto según las fechas del fold.

    Retorna un diccionario con folds, promedios, desviación estándar,
    mínimo, máximo y tiempo total. Nunca lanza una excepción por datos
    insuficientes: en su lugar, "advertencias" lo explica y
    "n_folds_ejecutados" puede ser 0.
    """
    n = len(serie)
    folds_idx, n_efectivo, advertencias = generar_folds_temporales(n, n_splits)

    resultado_folds = []
    tiempo_total = 0.0

    for i, (idx_train, idx_val) in enumerate(folds_idx, start=1):
        serie_train = serie.iloc[idx_train].reset_index(drop=True)
        serie_val = serie.iloc[idx_val].reset_index(drop=True)

        fila = {
            "numero_fold": i,
            "fecha_inicio_train": serie_train["fecha"].iloc[0].date().isoformat(),
            "fecha_fin_train": serie_train["fecha"].iloc[-1].date().isoformat(),
            "fecha_inicio_val": serie_val["fecha"].iloc[0].date().isoformat(),
            "fecha_fin_val": serie_val["fecha"].iloc[-1].date().isoformat(),
            "n_train": int(len(serie_train)),
            "n_val": int(len(serie_val)),
        }

        try:
            t0 = time.perf_counter()
            pred, _errores, _info = entrenar_evaluar_fn(serie_train, serie_val)
            # El contrato de entrenar_evaluar_fn no separa fit de predict
            # (ajusta y pronostica en la misma llamada); se reporta el
            # tiempo combinado como tiempo_entrenamiento. tiempo_inferencia
            # se deja en None en vez de inventar una cifra no medida.
            tiempo_entrenamiento = time.perf_counter() - t0

            y_val = serie_val["cantidad"].values.astype(float)
            metricas = calcular_metricas(y_val, pred, valor_anterior=float(serie_train["cantidad"].iloc[-1]))

            fila.update(metricas)
            fila["tiempo_entrenamiento"] = round(tiempo_entrenamiento, 4)
            fila["tiempo_inferencia"] = None
        except Exception as exc:
            fila.update({m: None for m in NOMBRES_METRICAS})
            fila["tiempo_entrenamiento"] = None
            fila["tiempo_inferencia"] = None
            fila["error"] = str(exc)

        tiempo_total += fila.get("tiempo_entrenamiento") or 0.0
        resultado_folds.append(fila)

    valores_por_metrica = {m: [] for m in NOMBRES_METRICAS}
    for f in resultado_folds:
        for m in NOMBRES_METRICAS:
            v = f.get(m)
            if isinstance(v, (int, float)) and v is not None:
                valores_por_metrica[m].append(v)

    def _agregar(func):
        return {
            m: (round(float(func(vals)), 4) if vals else None)
            for m, vals in valores_por_metrica.items()
        }

    return {
        "folds": resultado_folds,
        "promedio": _agregar(np.mean),
        "desviacion_estandar": _agregar(lambda v: np.std(v, ddof=1) if len(v) > 1 else 0.0),
        "minimo": _agregar(np.min),
        "maximo": _agregar(np.max),
        "tiempo_total": round(tiempo_total, 4),
        "n_folds_ejecutados": n_efectivo,
        "n_folds_solicitados": n_splits,
        "advertencias": advertencias,
    }
