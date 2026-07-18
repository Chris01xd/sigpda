"""
Pruebas de ia/orquestador.py: flujo completo (EDA + 5 modelos + tuning
+ validación cruzada + pruebas estadísticas). Usa datos sintéticos vía
monkeypatch sobre construir_dataset_historico (en ia.comparacion_completa)
para no depender de la base de datos real. n_splits se reduce a 2 para
mantener las pruebas razonablemente rápidas (Prophet es el modelo más
lento de ajustar y se entrena varias veces: comparación base + tuning + CV).
"""
import numpy as np
import pandas as pd
import pytest

import ia.comparacion_completa as cc
import ia.orquestador as orq


def _df_historico_sintetico(n_dias=45, id_plato=1, semilla=21):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n_dias, freq="D")
    return pd.DataFrame({
        "id_plato": id_plato,
        "fecha": fechas,
        "cantidad": rng.integers(1, 20, size=n_dias).astype(float),
        "categoria": "Entradas",
        "precio": 15.0,
    })


class TestEjecutarFlujoCompleto:
    def test_propaga_error_de_comparar_cinco_modelos(self, monkeypatch):
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: pd.DataFrame())
        resultado = orq.ejecutar_flujo_completo(id_plato=1)
        assert "error" in resultado

    def test_estructura_completa_sin_tuning(self, monkeypatch):
        df = _df_historico_sintetico(n_dias=45)
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: df)

        resultado = orq.ejecutar_flujo_completo(
            id_plato=1, dias_adelante=5, n_splits=2, ejecutar_tuning=False,
        )

        assert "error" not in resultado
        assert resultado["eda_resumen"]["resumen"]["registros_transacciones"] > 0

        nombres_modelos = {
            "arima", "prophet", "holt_winters",
            "transformer_random_forest", "transformer_gradient_boosting",
        }
        assert set(resultado["hiperparametros"].keys()) == nombres_modelos
        for hp in resultado["hiperparametros"].values():
            assert hp["aplicable"] is False  # tuning desactivado por el usuario

        assert set(resultado["validacion_cruzada"].keys()) == nombres_modelos
        for cv in resultado["validacion_cruzada"].values():
            assert cv["n_folds_solicitados"] == 2
            assert "promedio" in cv and "desviacion_estandar" in cv

        pruebas = resultado["pruebas_estadisticas"]
        assert "friedman" in pruebas
        assert isinstance(pruebas["wilcoxon"], list)
        assert isinstance(pruebas["diebold_mariano"], list)
        assert len(pruebas["diebold_mariano"]) == 4  # ganador vs los otros 4

        assert resultado["interpretacion"]
        assert resultado["duracion_total_segundos"] >= 0

        # Campos internos presentes, para que el router guarde el modelo/BD
        assert "_serie" in resultado
        assert "_df_plato" in resultado
        assert "_errores_por_modelo" in resultado

    def test_con_tuning_registra_metadatos_de_busqueda(self, monkeypatch):
        df = _df_historico_sintetico(n_dias=45)
        monkeypatch.setattr(cc, "construir_dataset_historico", lambda: df)

        resultado = orq.ejecutar_flujo_completo(
            id_plato=1, dias_adelante=3, n_splits=2, ejecutar_tuning=True,
        )

        assert "error" not in resultado

        hp_arima = resultado["hiperparametros"]["arima"]
        assert hp_arima["aplicable"] is True
        assert hp_arima["semilla"] == 42
        assert "fecha_ejecucion" in hp_arima

        hp_rf = resultado["hiperparametros"]["transformer_random_forest"]
        assert hp_rf["aplicable"] is True
        assert hp_rf["mejor_hiperparametros"] is not None
