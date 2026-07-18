"""
=================================================================
SIGPDA - Métricas de error para modelos de predicción de demanda
=================================================================
Fuente única de verdad para las métricas de regresión usadas en toda
la comparación de modelos: MAE, RMSE, MAPE, SMAPE y R².

Mientras las métricas de error tiendan a cero, el modelo se considera
más preciso. R² más cercano a 1 indica mejor ajuste.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error


def calcular_smape(y_real: np.ndarray, y_pred: np.ndarray) -> float | None:
    """
    SMAPE (Symmetric Mean Absolute Percentage Error), en porcentaje.

    Fórmula: SMAPE = (100/n) * Σ |y_real - y_pred| / ((|y_real| + |y_pred|) / 2)

    A diferencia de MAPE, SMAPE está acotado y maneja mejor los ceros:
    solo se excluyen del promedio los días en que y_real Y y_pred son
    ambos cero (denominador cero → no hay error relativo que medir,
    ambos coinciden en "sin demanda"). Nunca se divide por cero.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    denominador = (np.abs(y_real) + np.abs(y_pred)) / 2.0
    mascara = denominador > 0
    if mascara.sum() == 0:
        return None

    smape = float(
        np.mean(np.abs(y_real[mascara] - y_pred[mascara]) / denominador[mascara]) * 100
    )
    return round(smape, 4)


def calcular_u_theil(y_real: np.ndarray, y_pred: np.ndarray, valor_anterior: float | None = None) -> float | None:
    """Calcula U2 de Theil frente al pron?stico ingenuo y[t-1].

    U2 < 1 supera al ingenuo; U2 = 1 lo iguala; U2 > 1 es peor.
    valor_anterior es el ?ltimo dato de entrenamiento y evita fuga temporal.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.maximum(0, np.asarray(y_pred, dtype=float))
    if len(y_real) == 0 or len(y_real) != len(y_pred):
        return None
    if valor_anterior is None:
        if len(y_real) < 2:
            return None
        reales, predicciones, ingenuo = y_real[1:], y_pred[1:], y_real[:-1]
    else:
        reales, predicciones = y_real, y_pred
        ingenuo = np.concatenate(([float(valor_anterior)], y_real[:-1]))
    rmse_modelo = float(np.sqrt(np.mean((reales - predicciones) ** 2)))
    rmse_ingenuo = float(np.sqrt(np.mean((reales - ingenuo) ** 2)))
    if np.isclose(rmse_ingenuo, 0.0):
        return None
    return round(rmse_modelo / rmse_ingenuo, 4)


def calcular_metricas(y_real: np.ndarray, y_pred: np.ndarray, valor_anterior: float | None = None) -> dict:
    """
    Calcula MAE, RMSE, MAPE, SMAPE y R² entre valores reales y pronosticados.

    Ningún valor retornado es NaN ni Infinity: MAPE y SMAPE retornan
    None (no un número) cuando no hay denominador válido, en vez de
    dividir por cero.
    """
    y_real = np.asarray(y_real, dtype=float)
    y_pred = np.maximum(0, np.asarray(y_pred, dtype=float))

    mae = float(mean_absolute_error(y_real, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_real, y_pred)))

    # MAPE: se evita división por cero excluyendo días con demanda real nula
    mascara_positiva = y_real > 0
    if mascara_positiva.sum() > 0:
        mape = float(
            np.mean(
                np.abs((y_real[mascara_positiva] - y_pred[mascara_positiva])
                       / y_real[mascara_positiva])
            ) * 100
        )
    else:
        mape = None

    smape = calcular_smape(y_real, y_pred)
    u_theil = calcular_u_theil(y_real, y_pred, valor_anterior)
    r2 = float(r2_score(y_real, y_pred)) if len(y_real) > 1 else None

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4) if mape is not None else None,
        "smape": smape,
        "u_theil": u_theil,
        "r2": round(r2, 4) if r2 is not None else None,
    }
