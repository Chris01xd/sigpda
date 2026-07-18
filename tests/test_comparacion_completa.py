"""
Pruebas de ia/comparacion_completa.py: orquestación de los 5 modelos
(ARIMA, Prophet, Holt-Winters, Transformer+RF, Transformer+GBR) con un
único split cronológico. Usa datos sintéticos vía monkeypatch sobre
construir_dataset_historico para no depender de la base de datos real.
"""
import numpy as np
import pandas as pd
import pytest

import ia.comparacion_completa as cc


def _df_historico_sintetico(n_dias=60, id_plato=1, semilla=11):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n_dias, freq="D")
    return pd.DataFrame({
        "id_plato": id_plato,
        "fecha": fechas,
        "cantidad": rng.integers(1, 20, size=n_dias).astype(float),
        "categoria": "Entradas",
        "precio": 15.0,
    })


class TestCompararCincoModelos:
    def test_sin_datos_historicos(self, monkeypatch):
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: pd.DataFrame())
        resultado = cc.comparar_cinco_modelos(id_plato=1)
        assert "error" in resultado

    def test_plato_sin_datos(self, monkeypatch):
        df = _df_historico_sintetico(id_plato=1)
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: df)
        resultado = cc.comparar_cinco_modelos(id_plato=999)
        assert "error" in resultado

    def test_dataset_insuficiente(self, monkeypatch):
        df = _df_historico_sintetico(n_dias=10, id_plato=1)
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: df)
        resultado = cc.comparar_cinco_modelos(id_plato=1)
        assert "error" in resultado

    def test_comparacion_completa_con_datos_suficientes(self, monkeypatch):
        df = _df_historico_sintetico(n_dias=60, id_plato=1)
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: df)

        resultado = cc.comparar_cinco_modelos(id_plato=1, dias_adelante=5)

        assert "error" not in resultado
        assert set(resultado["metricas_por_modelo"].keys()) == {
            "arima", "prophet", "holt_winters",
            "transformer_random_forest", "transformer_gradient_boosting",
        }
        assert resultado["modelo_ganador"] in resultado["metricas_por_modelo"]
        assert len(resultado["predicciones_futuras"]) == 5
        assert resultado["criterio_seleccion"]
        # Campos de uso interno, para reutilización por model_registry y Fase 8
        assert "_serie" in resultado
        assert "_df_plato" in resultado
        assert "_errores_por_modelo" in resultado
        assert set(resultado["_errores_por_modelo"].keys()) == set(resultado["metricas_por_modelo"].keys())
