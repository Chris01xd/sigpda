"""
Pruebas de ia/metricas.py: MAE, RMSE, MAPE, SMAPE y R², sin NaN ni
Infinity y sin divisiones por cero.
"""
import numpy as np
import pytest

from ia.metricas import calcular_metricas, calcular_smape, calcular_u_theil


class TestCalcularUTheil:
    def test_menor_a_uno_si_supera_al_ingenuo(self):
        assert calcular_u_theil(np.array([12., 14., 16.]), np.array([11.5, 13.5, 15.5]), 10.) < 1

    def test_igual_a_uno_para_pronostico_ingenuo(self):
        assert calcular_u_theil(np.array([12., 14., 16.]), np.array([10., 12., 14.]), 10.) == pytest.approx(1.0)

    def test_none_si_referencia_constante(self):
        assert calcular_u_theil(np.array([5., 5., 5.]), np.array([5., 5., 5.]), 5.) is None


class TestCalcularSmape:
    def test_smape_con_todos_ceros_retorna_none(self):
        y_real = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([0.0, 0.0, 0.0])
        assert calcular_smape(y_real, y_pred) is None

    def test_smape_ignora_solo_los_pares_cero_cero(self):
        y_real = np.array([0.0, 0.0, 10.0])
        y_pred = np.array([0.0, 5.0, 8.0])
        resultado = calcular_smape(y_real, y_pred)
        # Solo se promedian los índices 1 y 2 (índice 0 es 0 vs 0, se excluye)
        esperado = np.mean([
            abs(0.0 - 5.0) / ((0.0 + 5.0) / 2),
            abs(10.0 - 8.0) / ((10.0 + 8.0) / 2),
        ]) * 100
        assert resultado == pytest.approx(round(esperado, 4))

    def test_smape_prediccion_perfecta_es_cero(self):
        y_real = np.array([5.0, 10.0, 15.0])
        assert calcular_smape(y_real, y_real.copy()) == pytest.approx(0.0)

    def test_smape_nunca_negativo_ni_mayor_a_200(self):
        rng = np.random.default_rng(0)
        y_real = rng.uniform(0, 50, 30)
        y_pred = rng.uniform(0, 50, 30)
        resultado = calcular_smape(y_real, y_pred)
        assert 0 <= resultado <= 200


class TestCalcularMetricas:
    def test_sin_nan_ni_infinito(self):
        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
        m = calcular_metricas(y_real, y_pred)
        for clave in ("mae", "rmse", "mape", "smape", "u_theil", "r2"):
            valor = m[clave]
            assert valor is None or np.isfinite(valor)

    def test_mape_none_cuando_todos_los_reales_son_cero(self):
        y_real = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([1.0, 2.0, 0.0])
        m = calcular_metricas(y_real, y_pred)
        assert m["mape"] is None
        assert m["mae"] is not None  # MAE sí se calcula siempre

    def test_prediccion_perfecta(self):
        y_real = np.array([2.0, 4.0, 6.0, 8.0])
        m = calcular_metricas(y_real, y_real.copy())
        assert m["mae"] == 0.0
        assert m["rmse"] == 0.0
        assert m["mape"] == 0.0
        assert m["smape"] == 0.0
        assert m["r2"] == pytest.approx(1.0)

    def test_predicciones_negativas_se_recortan_a_cero(self):
        y_real = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([-5.0, 2.0, 3.0])
        m = calcular_metricas(y_real, y_pred)
        # mae debe reflejar max(0, -5) = 0 comparado con 1.0 -> error de 1.0 en esa posición
        # (el backend redondea a 4 decimales)
        assert m["mae"] == pytest.approx(round((1.0 + 0.0 + 0.0) / 3, 4))

    def test_r2_none_con_una_sola_observacion(self):
        m = calcular_metricas(np.array([5.0]), np.array([4.0]))
        assert m["r2"] is None
