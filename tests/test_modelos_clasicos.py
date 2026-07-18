"""
Pruebas de ia/modelos_clasicos.py: ARIMA, Prophet y Holt-Winters
centralizados. Prophet no se prueba aquí de forma unitaria (su ajuste
es lento); ya se valida indirectamente en tests/test_comparador_modelos.py
y en la verificación manual end-to-end de /comparar-modelos.
"""
import numpy as np
import pandas as pd
import pytest

from ia.modelos_clasicos import (
    entrenar_evaluar_holt_winters,
    predecir_futuro_holt_winters,
    _auto_hiperparametros_holt_winters,
    entrenar_evaluar_arima,
    ajustar_arima_completo,
    ajustar_holt_winters_completo,
)


def _serie_sintetica(n=40, semilla=5):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n, freq="D")
    # patrón semanal + ruido, para que Holt-Winters tenga estacionalidad que capturar
    base = 10 + 3 * np.sin(2 * np.pi * np.arange(n) / 7)
    cantidad = np.maximum(0, base + rng.normal(0, 1, n))
    return pd.DataFrame({"fecha": fechas, "cantidad": cantidad})


class TestAutoHiperparametrosHoltWinters:
    def test_sin_estacionalidad_si_pocos_dias(self):
        hp = _auto_hiperparametros_holt_winters(10)
        assert hp["seasonal"] is None
        assert hp["seasonal_periods"] is None

    def test_con_estacionalidad_si_hay_datos_suficientes(self):
        hp = _auto_hiperparametros_holt_winters(30)
        assert hp["seasonal"] == "add"
        assert hp["seasonal_periods"] == 7

    def test_damped_trend_solo_con_suficientes_dias(self):
        assert _auto_hiperparametros_holt_winters(10)["damped_trend"] is False
        assert _auto_hiperparametros_holt_winters(40)["damped_trend"] is True


class TestHoltWinters:
    def test_entrenar_evaluar_retorna_formas_correctas(self):
        serie = _serie_sintetica(40)
        train = serie.iloc[:30].reset_index(drop=True)
        test = serie.iloc[30:].reset_index(drop=True)
        pred, errores, info = entrenar_evaluar_holt_winters(train, test)

        assert len(pred) == len(test)
        assert len(errores) == len(test)
        assert (pred >= 0).all()
        assert "hiperparametros" in info

    def test_predecir_futuro_longitud_correcta(self):
        serie = _serie_sintetica(40)
        pred = predecir_futuro_holt_winters(serie, n_pasos=5)
        assert len(pred) == 5
        assert (pred >= 0).all()

    def test_funciona_con_pocos_datos_sin_estacionalidad(self):
        serie = _serie_sintetica(12)
        train = serie.iloc[:8].reset_index(drop=True)
        test = serie.iloc[8:].reset_index(drop=True)
        pred, errores, info = entrenar_evaluar_holt_winters(train, test)

        assert len(pred) == len(test)
        assert info["hiperparametros"]["seasonal"] is None


class TestModelosClasicosCentralizados:
    def test_arima_funciona_desde_modulo_centralizado(self):
        serie = _serie_sintetica(35)
        train = serie.iloc[:28].reset_index(drop=True)
        test = serie.iloc[28:].reset_index(drop=True)
        pred, errores, info = entrenar_evaluar_arima(train, test)

        assert len(pred) == len(test)
        assert "orden" in info


class TestAjustarModeloCompleto:
    """
    Fase 6: estos helpers ajustan sobre TODO el dataset y retornan el
    objeto ya entrenado (picklable), para que ia.model_registry pueda
    guardarlo y predecir después sin reentrenar.
    """
    def test_ajustar_arima_completo_retorna_objeto_con_forecast(self):
        serie = _serie_sintetica(35)
        modelo, hp = ajustar_arima_completo(serie)
        pred = modelo.forecast(steps=5)
        assert len(pred) == 5
        assert "orden" in hp

    def test_ajustar_holt_winters_completo_retorna_objeto_con_forecast(self):
        serie = _serie_sintetica(35)
        modelo, hp = ajustar_holt_winters_completo(serie)
        pred = modelo.forecast(5)
        assert len(pred) == 5
        assert "hiperparametros" in hp
