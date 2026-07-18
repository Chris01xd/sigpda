"""
Pruebas de ia/tuning.py: optimización de hiperparámetros respetando el
orden temporal (RandomizedSearchCV + TimeSeriesSplit para regresores
sklearn; búsqueda aleatoria temporal propia para modelos estadísticos).
No usa Optuna ni validación aleatoria (KFold).
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from ia.tuning import (
    _muestrear_combinaciones,
    _tamano_espacio,
    buscar_hiperparametros_temporal,
    buscar_hiperparametros_regresor_sklearn,
    ESPACIOS_BUSQUEDA,
)


def _serie(n=40, semilla=1):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame({"fecha": fechas, "cantidad": rng.integers(1, 20, size=n).astype(float)})


class TestMuestrearCombinaciones:
    def test_sin_duplicados(self):
        espacio = {"a": [1, 2, 3], "b": ["x", "y"]}
        combos = _muestrear_combinaciones(espacio, n=6, semilla=1)  # tamaño total = 6
        firmas = {tuple(sorted(c.items())) for c in combos}
        assert len(firmas) == len(combos)

    def test_respeta_limite_del_espacio(self):
        espacio = {"a": [1, 2]}
        combos = _muestrear_combinaciones(espacio, n=10, semilla=1)
        assert len(combos) == _tamano_espacio(espacio) == 2

    def test_reproducible_con_misma_semilla(self):
        espacio = {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30]}
        c1 = _muestrear_combinaciones(espacio, n=5, semilla=42)
        c2 = _muestrear_combinaciones(espacio, n=5, semilla=42)
        assert c1 == c2


class TestBuscarHiperparametrosTemporal:
    def _modelo_lineal_falso(self, serie_train, serie_val, offset=0.0, factor=1.0):
        """Modelo sintético rápido: no depende de statsmodels, para probar la mecánica de búsqueda."""
        media = serie_train["cantidad"].mean()
        pred = np.full(len(serie_val), media * factor + offset)
        errores = np.abs(serie_val["cantidad"].values - pred)
        return pred, errores, {}

    def test_modelo_sin_espacio_definido_no_es_aplicable(self):
        serie = _serie(40)
        resultado = buscar_hiperparametros_temporal("modelo_inexistente", self._modelo_lineal_falso, serie)
        assert resultado["aplicable"] is False

    def test_datos_insuficientes_no_es_aplicable(self):
        serie = _serie(5)
        resultado = buscar_hiperparametros_temporal("arima", self._modelo_lineal_falso, serie)
        assert resultado["aplicable"] is False

    def test_busqueda_registra_metadatos_completos(self):
        espacio_falso = {"offset": [0.0, 1.0, 2.0], "factor": [0.9, 1.0, 1.1]}
        ESPACIOS_BUSQUEDA["_modelo_prueba"] = espacio_falso
        try:
            serie = _serie(40)
            resultado = buscar_hiperparametros_temporal(
                "_modelo_prueba", self._modelo_lineal_falso, serie, n_combinaciones=4, semilla=42,
            )
            assert resultado["aplicable"] is True
            assert resultado["mejor_hiperparametros"] is not None
            assert resultado["mejor_valor"] is not None
            assert resultado["semilla"] == 42
            assert resultado["metrica_objetivo"] == "mae"
            assert "fecha_ejecucion" in resultado
            assert len(resultado["combinaciones_evaluadas"]) == resultado["n_combinaciones"]
        finally:
            del ESPACIOS_BUSQUEDA["_modelo_prueba"]


class TestBuscarHiperparametrosRegresorSklearn:
    def test_randomized_search_cv_con_timeseriessplit(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(60, 5))
        y = rng.normal(size=60)

        resultado = buscar_hiperparametros_regresor_sklearn(
            "transformer_random_forest",
            RandomForestRegressor(random_state=42),
            X, y, n_splits=3, n_iter=4, semilla=42,
        )
        assert resultado["aplicable"] is True
        assert resultado["mejor_hiperparametros"] is not None
        assert resultado["n_combinaciones"] <= 4
        assert resultado["tiempo_total"] >= 0

    def test_modelo_sin_espacio_no_es_aplicable(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(20, 3))
        y = rng.normal(size=20)
        resultado = buscar_hiperparametros_regresor_sklearn(
            "modelo_inexistente", RandomForestRegressor(), X, y,
        )
        assert resultado["aplicable"] is False

    def test_datos_insuficientes_no_es_aplicable(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(2, 3))
        y = rng.normal(size=2)
        resultado = buscar_hiperparametros_regresor_sklearn(
            "transformer_random_forest", RandomForestRegressor(), X, y, n_splits=5,
        )
        assert resultado["aplicable"] is False
