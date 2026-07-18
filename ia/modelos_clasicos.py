"""
=================================================================
SIGPDA - Modelos clásicos de series de tiempo (ARIMA, Prophet, Holt-Winters)
=================================================================
Fuente única de verdad para los tres modelos estadísticos clásicos
usados en la comparación científica principal de la tesis. Todos
usan hiperparámetros seleccionados automáticamente (sin intervención
del usuario) y siguen el mismo contrato:

    entrenar_evaluar_x(serie_train, serie_test) -> (pred_test, errores_abs, info)
    predecir_futuro_x(serie, ...) -> valores_futuros

`serie_train`/`serie_test`/`serie` son DataFrames con columnas al
menos "fecha" y "cantidad" (ver ia.data_preparation.preparar_serie_diaria).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ================================================================
# MODELO ARIMA — AUTO-SELECCIÓN DE (p, d, q) POR AIC
# ================================================================

def _es_estacionaria_adf(serie: np.ndarray) -> bool:
    """Prueba ADF: True si la serie es estacionaria (p-valor < 0.05)."""
    try:
        from statsmodels.tsa.stattools import adfuller
        _, p_val, *_ = adfuller(serie, autolag="AIC")
        return float(p_val) < 0.05
    except Exception:
        return False


def _auto_orden_arima(serie: np.ndarray) -> tuple[int, int, int]:
    """
    Selección automática de orden (p, d, q) por mínimo AIC.
    Espacio de búsqueda: p ∈ [0,3], d ∈ {0,1}, q ∈ [0,3].
    El usuario no interviene en esta selección.
    """
    from statsmodels.tsa.arima.model import ARIMA

    d = 0 if _es_estacionaria_adf(serie) else 1
    mejor_aic = float("inf")
    mejor_orden = (1, d, 1)

    for p in range(0, 4):
        for q in range(0, 4):
            if p == 0 and q == 0:
                continue
            try:
                res = ARIMA(serie, order=(p, d, q)).fit()
                if res.aic < mejor_aic:
                    mejor_aic = res.aic
                    mejor_orden = (p, d, q)
            except Exception:
                continue

    return mejor_orden


def entrenar_evaluar_arima(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Entrena ARIMA con hiperparámetros automáticos y evalúa sobre el test."""
    from statsmodels.tsa.arima.model import ARIMA

    vals_train = serie_train["cantidad"].values.astype(float)
    vals_test = serie_test["cantidad"].values.astype(float)
    n_test = len(vals_test)

    orden = _auto_orden_arima(vals_train)
    resultado = ARIMA(vals_train, order=orden).fit()

    pred_test = np.maximum(0.0, resultado.forecast(steps=n_test))
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {
        "orden": f"ARIMA({orden[0]},{orden[1]},{orden[2]})",
        "aic": round(float(resultado.aic), 4),
    }


def predecir_futuro_arima(serie: pd.DataFrame, n_pasos: int) -> np.ndarray:
    """Re-entrena ARIMA en la serie completa y pronostica n_pasos hacia adelante."""
    from statsmodels.tsa.arima.model import ARIMA

    vals = serie["cantidad"].values.astype(float)
    orden = _auto_orden_arima(vals)
    res = ARIMA(vals, order=orden).fit()
    return np.maximum(0.0, res.forecast(steps=n_pasos))


def ajustar_arima_completo(serie: pd.DataFrame) -> tuple[object, dict]:
    """
    Ajusta ARIMA (orden automático por AIC) sobre TODA la serie y
    retorna el resultado ajustado (para persistir con ia.model_registry
    y predecir después sin reentrenar) junto a sus hiperparámetros.
    """
    from statsmodels.tsa.arima.model import ARIMA

    vals = serie["cantidad"].values.astype(float)
    orden = _auto_orden_arima(vals)
    resultado = ARIMA(vals, order=orden).fit()
    return resultado, {"orden": f"ARIMA({orden[0]},{orden[1]},{orden[2]})", "aic": round(float(resultado.aic), 4)}


def entrenar_evaluar_arima_con_hp(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
    p: int = 1,
    d: int = 1,
    q: int = 1,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Variante de entrenar_evaluar_arima que usa un orden (p, d, q) EXPLÍCITO
    en vez de seleccionarlo automáticamente por AIC. Se usa para la
    búsqueda de hiperparámetros (ia.tuning), que necesita poder variar
    la configuración entre combinaciones.
    """
    from statsmodels.tsa.arima.model import ARIMA

    vals_train = serie_train["cantidad"].values.astype(float)
    vals_test = serie_test["cantidad"].values.astype(float)
    n_test = len(vals_test)

    resultado = ARIMA(vals_train, order=(p, d, q)).fit()
    pred_test = np.maximum(0.0, resultado.forecast(steps=n_test))
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {"orden": f"ARIMA({p},{d},{q})", "aic": round(float(resultado.aic), 4)}


# ================================================================
# MODELO PROPHET — HIPERPARÁMETROS AUTOMÁTICOS
# ================================================================

def _hiperparametros_prophet(n_dias: int) -> dict:
    """Determina hiperparámetros de Prophet según la longitud de la serie."""
    return {
        "yearly_seasonality": n_dias >= 365,
        "weekly_seasonality": n_dias >= 14,
        "daily_seasonality": False,
        "seasonality_mode": "multiplicative" if n_dias >= 60 else "additive",
        "changepoint_prior_scale": 0.05,
        "seasonality_prior_scale": 10.0,
    }


def entrenar_evaluar_prophet(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Entrena Prophet con hiperparámetros automáticos y evalúa sobre el test."""
    from prophet import Prophet

    df_prophet = pd.DataFrame({
        "ds": serie_train["fecha"],
        "y": serie_train["cantidad"].astype(float),
    })

    hparams = _hiperparametros_prophet(len(serie_train))
    modelo = Prophet(**hparams)
    import logging as _log
    _log.getLogger("cmdstanpy").setLevel(_log.WARNING)
    _log.getLogger("prophet").setLevel(_log.WARNING)
    modelo.fit(df_prophet)

    df_futuro = pd.DataFrame({"ds": serie_test["fecha"].values})
    pronostico = modelo.predict(df_futuro)

    pred_test = np.maximum(0.0, pronostico["yhat"].values)
    vals_test = serie_test["cantidad"].values.astype(float)
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {"hiperparametros": hparams}


def entrenar_evaluar_prophet_con_hp(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
    changepoint_prior_scale: float = 0.05,
    seasonality_prior_scale: float = 10.0,
    seasonality_mode: str = "additive",
    weekly_seasonality: bool = True,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Variante de entrenar_evaluar_prophet con hiperparámetros EXPLÍCITOS
    (para ia.tuning). yearly_seasonality y daily_seasonality se mantienen
    con el mismo criterio automático que la versión por defecto.
    """
    from prophet import Prophet
    import logging as _log
    _log.getLogger("cmdstanpy").setLevel(_log.WARNING)
    _log.getLogger("prophet").setLevel(_log.WARNING)

    hparams = {
        "yearly_seasonality": len(serie_train) >= 365,
        "weekly_seasonality": weekly_seasonality,
        "daily_seasonality": False,
        "seasonality_mode": seasonality_mode,
        "changepoint_prior_scale": changepoint_prior_scale,
        "seasonality_prior_scale": seasonality_prior_scale,
    }

    df_prophet = pd.DataFrame({
        "ds": serie_train["fecha"],
        "y": serie_train["cantidad"].astype(float),
    })
    modelo = Prophet(**hparams)
    modelo.fit(df_prophet)

    df_futuro = pd.DataFrame({"ds": serie_test["fecha"].values})
    pronostico = modelo.predict(df_futuro)

    pred_test = np.maximum(0.0, pronostico["yhat"].values)
    vals_test = serie_test["cantidad"].values.astype(float)
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {"hiperparametros": hparams}


def predecir_futuro_prophet(serie: pd.DataFrame, fechas_futuras: list) -> np.ndarray:
    """Re-entrena Prophet en la serie completa y predice fechas futuras."""
    from prophet import Prophet
    import logging as _log
    _log.getLogger("cmdstanpy").setLevel(_log.WARNING)
    _log.getLogger("prophet").setLevel(_log.WARNING)

    df_completo = pd.DataFrame({
        "ds": serie["fecha"],
        "y": serie["cantidad"].astype(float),
    })

    hparams = _hiperparametros_prophet(len(serie))
    modelo = Prophet(**hparams)
    modelo.fit(df_completo)

    df_futuro = pd.DataFrame({"ds": pd.to_datetime(fechas_futuras)})
    pronostico = modelo.predict(df_futuro)
    return np.maximum(0.0, pronostico["yhat"].values)


def ajustar_prophet_completo(serie: pd.DataFrame) -> tuple[object, dict]:
    """
    Ajusta Prophet sobre TODA la serie y retorna el modelo ajustado
    (para persistir con ia.model_registry) junto a sus hiperparámetros.
    """
    from prophet import Prophet
    import logging as _log
    _log.getLogger("cmdstanpy").setLevel(_log.WARNING)
    _log.getLogger("prophet").setLevel(_log.WARNING)

    hparams = _hiperparametros_prophet(len(serie))
    df_completo = pd.DataFrame({"ds": serie["fecha"], "y": serie["cantidad"].astype(float)})
    modelo = Prophet(**hparams)
    modelo.fit(df_completo)
    return modelo, {"hiperparametros": hparams}


# ================================================================
# MODELO HOLT-WINTERS (EXPONENTIAL SMOOTHING) — HIPERPARÁMETROS AUTO
# ================================================================

SEASONAL_PERIODS_SEMANAL = 7


def _auto_hiperparametros_holt_winters(n_dias: int) -> dict:
    """
    Selecciona tendencia/estacionalidad/amortiguamiento según la
    longitud de la serie. La estacionalidad semanal requiere al menos
    dos ciclos completos (2 * 7 días) para estimarse de forma fiable;
    si no alcanza, se omite ese componente en lugar de fallar.
    """
    usar_estacional = n_dias >= 2 * SEASONAL_PERIODS_SEMANAL
    return {
        "trend": "add",
        "damped_trend": n_dias >= 30,
        "seasonal": "add" if usar_estacional else None,
        "seasonal_periods": SEASONAL_PERIODS_SEMANAL if usar_estacional else None,
    }


def _construir_holt_winters(vals: np.ndarray, hparams: dict):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    return ExponentialSmoothing(
        vals,
        trend=hparams["trend"],
        damped_trend=hparams["damped_trend"],
        seasonal=hparams["seasonal"],
        seasonal_periods=hparams["seasonal_periods"],
        initialization_method="estimated",
    )


def entrenar_evaluar_holt_winters(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Entrena Holt-Winters con hiperparámetros automáticos y evalúa sobre el test."""
    vals_train = serie_train["cantidad"].values.astype(float)
    vals_test = serie_test["cantidad"].values.astype(float)
    n_test = len(vals_test)

    hparams = _auto_hiperparametros_holt_winters(len(vals_train))
    modelo = _construir_holt_winters(vals_train, hparams)
    resultado = modelo.fit(optimized=True)

    pred_test = np.maximum(0.0, resultado.forecast(n_test))
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {"hiperparametros": hparams}


def predecir_futuro_holt_winters(serie: pd.DataFrame, n_pasos: int) -> np.ndarray:
    """Re-entrena Holt-Winters en la serie completa y pronostica n_pasos hacia adelante."""
    vals = serie["cantidad"].values.astype(float)
    hparams = _auto_hiperparametros_holt_winters(len(vals))
    modelo = _construir_holt_winters(vals, hparams)
    resultado = modelo.fit(optimized=True)
    return np.maximum(0.0, resultado.forecast(n_pasos))


def ajustar_holt_winters_completo(serie: pd.DataFrame) -> tuple[object, dict]:
    """
    Ajusta Holt-Winters sobre TODA la serie y retorna el resultado
    ajustado (para persistir con ia.model_registry) junto a sus
    hiperparámetros.
    """
    vals = serie["cantidad"].values.astype(float)
    hparams = _auto_hiperparametros_holt_winters(len(vals))
    modelo = _construir_holt_winters(vals, hparams)
    resultado = modelo.fit(optimized=True)
    return resultado, {"hiperparametros": hparams}


def entrenar_evaluar_holt_winters_con_hp(
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
    trend: str = "add",
    damped_trend: bool = False,
    seasonal: str | None = "add",
    seasonal_periods: int | None = SEASONAL_PERIODS_SEMANAL,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Variante de entrenar_evaluar_holt_winters con hiperparámetros
    EXPLÍCITOS (para ia.tuning). Si la combinación estacional no es
    viable para el tamaño de la serie de entrenamiento (menos de
    2 ciclos), se desactiva el componente estacional automáticamente
    para no fallar de forma innecesaria.
    """
    vals_train = serie_train["cantidad"].values.astype(float)
    vals_test = serie_test["cantidad"].values.astype(float)
    n_test = len(vals_test)

    if seasonal and seasonal_periods and len(vals_train) < 2 * seasonal_periods:
        seasonal, seasonal_periods = None, None

    hparams = {"trend": trend, "damped_trend": damped_trend, "seasonal": seasonal, "seasonal_periods": seasonal_periods}
    modelo = _construir_holt_winters(vals_train, hparams)
    resultado = modelo.fit(optimized=True)

    pred_test = np.maximum(0.0, resultado.forecast(n_test))
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, {"hiperparametros": hparams}
