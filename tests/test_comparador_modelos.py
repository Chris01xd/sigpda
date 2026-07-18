"""
Prueba de regresión: ia.comparador_modelos debe reutilizar la
preparación de la serie diaria centralizada en ia.data_preparation
(sin mantener una segunda implementación paralela) y su comportamiento
numérico debe permanecer intacto.
"""
import numpy as np
import pandas as pd

import ia.comparador_modelos as comparador
import ia.data_preparation as data_prep
import ia.modelos_clasicos as modelos_clasicos
import ia.modelos_hibridos as modelos_hibridos
import ia.metricas as metricas
import ia.pruebas_estadisticas as pruebas_estadisticas


def test_preparar_serie_diaria_es_la_funcion_centralizada():
    """No debe existir una implementación paralela: debe ser el mismo objeto función."""
    assert comparador._preparar_serie_diaria is data_prep.preparar_serie_diaria


def test_arima_y_prophet_son_las_funciones_centralizadas():
    """
    Fase 3: ARIMA y Prophet se movieron a ia.modelos_clasicos; comparador_modelos
    debe reutilizarlas (mismo objeto función), no reimplementarlas.
    """
    assert comparador.entrenar_evaluar_arima is modelos_clasicos.entrenar_evaluar_arima
    assert comparador.predecir_futuro_arima is modelos_clasicos.predecir_futuro_arima
    assert comparador.entrenar_evaluar_prophet is modelos_clasicos.entrenar_evaluar_prophet
    assert comparador.predecir_futuro_prophet is modelos_clasicos.predecir_futuro_prophet


def test_construir_features_desde_serie_es_la_funcion_centralizada():
    assert comparador._construir_features_desde_serie is modelos_hibridos.construir_features_desde_serie


def test_calcular_metricas_es_la_funcion_centralizada_y_ahora_incluye_smape():
    """
    Fase 4: calcular_metricas se movió a ia.metricas (con SMAPE añadido).
    /comparar-modelos debe seguir devolviendo mae/rmse/mape/r2 igual que
    antes, más el campo nuevo "smape" (adición compatible).
    """
    assert comparador.calcular_metricas is metricas.calcular_metricas

    resultado = comparador.calcular_metricas(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))
    assert set(resultado.keys()) == {"mae", "rmse", "mape", "smape", "u_theil", "r2"}


def test_prueba_diebold_mariano_es_la_funcion_centralizada():
    """Fase 5: Diebold-Mariano se movió a ia.pruebas_estadisticas (junto con Friedman y Wilcoxon)."""
    assert comparador.prueba_diebold_mariano is pruebas_estadisticas.prueba_diebold_mariano


def test_serie_diaria_mantiene_el_comportamiento_de_interpolacion():
    fechas = pd.date_range("2026-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "id_plato": 1,
        "fecha": fechas,
        "cantidad": np.arange(1, 11, dtype=float),
        "categoria": "Entradas",
        "precio": 10.0,
    })
    df_con_hueco = df.drop(df.index[4])  # elimina un día para forzar interpolación

    serie = comparador._preparar_serie_diaria(df_con_hueco)

    assert len(serie) == 10
    # Día eliminado (índice 4, valor original 5) entre vecinos 4 (índice 3) y 6 (índice 5)
    # -> interpolación lineal = (4 + 6) / 2 = 5.0
    assert serie.loc[4, "cantidad"] == 5.0
    assert bool(serie.loc[4, "interpolado"]) is True
    assert list(serie.columns[:2]) == ["fecha", "cantidad"]
