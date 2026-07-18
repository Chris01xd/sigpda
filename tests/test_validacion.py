"""
Pruebas de ia/validacion.py: validación cruzada temporal (walk-forward,
hasta 5 folds) usando TimeSeriesSplit.
"""
import numpy as np
import pandas as pd
import pytest

from ia.validacion import generar_folds_temporales, evaluar_modelo_cv, MAX_FOLDS


def _serie(n=40, semilla=1):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame({"fecha": fechas, "cantidad": rng.integers(1, 20, size=n).astype(float)})


class TestGenerarFoldsTemporales:
    def test_cinco_folds_con_datos_suficientes(self):
        folds, n_efectivo, advertencias = generar_folds_temporales(60, n_splits=5)
        assert n_efectivo == 5
        assert len(folds) == 5
        assert advertencias == []

    def test_folds_son_walk_forward_sin_solapamiento_futuro(self):
        folds, _, _ = generar_folds_temporales(30, n_splits=5)
        for idx_train, idx_val in folds:
            assert idx_train.max() < idx_val.min()  # train siempre antes que val

    def test_reduce_folds_si_datos_insuficientes(self):
        folds, n_efectivo, advertencias = generar_folds_temporales(4, n_splits=5)
        assert n_efectivo == 3  # min(5, n_muestras - 1) = min(5, 3)
        assert len(folds) == 3
        assert any("solo se pudieron ejecutar" in a.lower() for a in advertencias)

    def test_sin_folds_si_datos_muy_escasos(self):
        folds, n_efectivo, advertencias = generar_folds_temporales(2, n_splits=5)
        assert folds == []
        assert n_efectivo == 0
        assert advertencias
        assert "insuficientes" in advertencias[0].lower()

    def test_no_lanza_excepcion_con_cero_muestras(self):
        folds, n_efectivo, advertencias = generar_folds_temporales(0, n_splits=5)
        assert folds == []
        assert n_efectivo == 0


class TestEvaluarModeloCV:
    def _modelo_naive(self, serie_train, serie_val):
        """Modelo trivial: predice la media de train para todo el fold de validación."""
        media = serie_train["cantidad"].mean()
        pred = np.full(len(serie_val), media)
        errores = np.abs(serie_val["cantidad"].values - pred)
        return pred, errores, {"media_train": media}

    def test_estructura_resultado_con_datos_suficientes(self):
        serie = _serie(50)
        resultado = evaluar_modelo_cv(self._modelo_naive, serie, n_splits=5)

        assert resultado["n_folds_ejecutados"] == 5
        assert len(resultado["folds"]) == 5
        for fold in resultado["folds"]:
            assert fold["mae"] is not None
            assert fold["fecha_inicio_train"] <= fold["fecha_fin_train"]
            assert fold["fecha_fin_train"] < fold["fecha_inicio_val"]
        assert set(resultado["promedio"].keys()) == {"mae", "rmse", "mape", "smape", "u_theil", "r2"}
        assert resultado["tiempo_total"] >= 0

    def test_maneja_datos_insuficientes_sin_excepcion(self):
        serie = _serie(2)
        resultado = evaluar_modelo_cv(self._modelo_naive, serie, n_splits=5)
        assert resultado["n_folds_ejecutados"] == 0
        assert resultado["folds"] == []
        assert resultado["advertencias"]

    def test_captura_excepcion_de_fold_individual_sin_abortar(self):
        contador = {"n": 0}

        def modelo_falla_en_el_segundo_fold(serie_train, serie_val):
            contador["n"] += 1
            if contador["n"] == 2:
                raise ValueError("fallo simulado")
            return self._modelo_naive(serie_train, serie_val)

        serie = _serie(40)
        resultado = evaluar_modelo_cv(modelo_falla_en_el_segundo_fold, serie, n_splits=5)

        # Los 5 folds se ejecutan (el conteo no aborta por el fallo de uno solo)
        assert len(resultado["folds"]) == 5
        assert resultado["folds"][1]["error"] == "fallo simulado"
        assert resultado["folds"][1]["mae"] is None
        # Los demás folds sí calcularon métricas normalmente
        assert resultado["folds"][0]["mae"] is not None
        assert resultado["folds"][2]["mae"] is not None
