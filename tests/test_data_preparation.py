"""
Pruebas del pipeline centralizado de preparación de datos (ia/data_preparation.py).
Usa datasets sintéticos pequeños; no requiere la base de datos real.
"""
import numpy as np
import pandas as pd
import pytest

from ia.data_preparation import (
    limpiar_y_validar,
    preparar_serie_diaria,
    construir_lags_y_medias_moviles,
    dividir_train_val_test,
    escalar_features,
    preparar_pipeline_completo,
)


def _df_sintetico(n_dias=40, id_plato=1, categoria="Entradas"):
    fechas = pd.date_range("2026-01-01", periods=n_dias, freq="D")
    rng = np.random.default_rng(7)
    cantidades = rng.integers(1, 20, size=n_dias).astype(float)
    return pd.DataFrame({
        "id_plato": id_plato,
        "fecha": fechas,
        "cantidad": cantidades,
        "categoria": categoria,
        "precio": 15.5,
    })


class TestLimpiarYValidar:
    def test_dataframe_vacio(self):
        df, advertencias = limpiar_y_validar(pd.DataFrame())
        assert df.empty
        assert advertencias

    def test_orden_cronologico(self):
        df = _df_sintetico(10)
        df_desordenado = df.sample(frac=1, random_state=1).reset_index(drop=True)
        limpio, _ = limpiar_y_validar(df_desordenado)
        assert limpio["fecha"].is_monotonic_increasing

    def test_cantidades_negativas_se_corrigen(self):
        df = _df_sintetico(10)
        df.loc[0, "cantidad"] = -5
        limpio, advertencias = limpiar_y_validar(df)
        assert (limpio["cantidad"] >= 0).all()
        assert any("negativ" in a for a in advertencias)

    def test_nulos_en_cantidad_se_imputan(self):
        df = _df_sintetico(10)
        df.loc[2, "cantidad"] = np.nan
        limpio, advertencias = limpiar_y_validar(df)
        assert limpio["cantidad"].isna().sum() == 0
        assert any("nulo" in a for a in advertencias)

    def test_duplicados_exactos_se_eliminan(self):
        df = _df_sintetico(5)
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        limpio, advertencias = limpiar_y_validar(df_dup)
        assert len(limpio) == 5
        assert any("duplicada" in a for a in advertencias)


class TestPrepararSerieDiaria:
    def test_rellena_huecos_y_marca_interpolados(self):
        df = _df_sintetico(10)
        df_con_hueco = df.drop(df.index[5])  # elimina el día 6
        serie = preparar_serie_diaria(df_con_hueco)
        assert len(serie) == 10
        assert serie["interpolado"].sum() == 1
        assert bool(serie.loc[5, "interpolado"]) is True

    def test_dias_completos_no_marcados_como_interpolados(self):
        df = _df_sintetico(10)
        serie = preparar_serie_diaria(df)
        assert serie["interpolado"].sum() == 0


class TestLagsYMediasMoviles:
    def test_lag_1_es_el_dia_anterior(self):
        df = _df_sintetico(15)
        serie = preparar_serie_diaria(df)
        resultado = construir_lags_y_medias_moviles(serie, lags=(1,), ventanas_media=())
        for i in range(1, len(resultado)):
            assert resultado.loc[i, "lag_1"] == pytest.approx(serie.loc[i - 1, "cantidad"])
        assert pd.isna(resultado.loc[0, "lag_1"])

    def test_media_movil_excluye_dia_actual(self):
        df = _df_sintetico(20)
        serie = preparar_serie_diaria(df)
        resultado = construir_lags_y_medias_moviles(serie, lags=(), ventanas_media=(7,))
        fila = 10
        esperado = serie.loc[fila - 7:fila - 1, "cantidad"].mean()
        assert resultado.loc[fila, "media_movil_7"] == pytest.approx(esperado)

    def test_no_hay_fuga_de_informacion_del_futuro(self):
        """Alterar valores futuros no debe cambiar el lag/media móvil de una fila pasada."""
        df = _df_sintetico(20)
        serie = preparar_serie_diaria(df)
        r1 = construir_lags_y_medias_moviles(serie.copy(), lags=(1,), ventanas_media=(7,))

        serie_alterada = serie.copy()
        serie_alterada.loc[15:, "cantidad"] = 999.0
        r2 = construir_lags_y_medias_moviles(serie_alterada, lags=(1,), ventanas_media=(7,))

        assert r1.loc[10, "lag_1"] == pytest.approx(r2.loc[10, "lag_1"])
        assert r1.loc[10, "media_movil_7"] == pytest.approx(r2.loc[10, "media_movil_7"])


class TestDividirTrainValTest:
    def test_split_es_cronologico_y_sin_solapamiento(self):
        df = _df_sintetico(40)
        serie = preparar_serie_diaria(df)
        train, val, test = dividir_train_val_test(serie, val_size=0.2, test_size=0.2)

        assert len(train) + len(val) + len(test) == len(serie)
        assert train["fecha"].max() < val["fecha"].min()
        assert val["fecha"].max() < test["fecha"].min()

    def test_dataset_pequeno_no_falla(self):
        df = _df_sintetico(4)
        serie = preparar_serie_diaria(df)
        train, val, test = dividir_train_val_test(serie)
        assert len(train) >= 1
        assert len(train) + len(val) + len(test) == len(serie)


class TestEscalarFeatures:
    def test_scaler_se_ajusta_solo_con_train(self):
        df = _df_sintetico(30)
        serie = preparar_serie_diaria(df)
        train, val, test = dividir_train_val_test(serie, val_size=0.2, test_size=0.2)

        train_e, _val_e, _test_e, params = escalar_features(train, val, test, ["cantidad"])

        assert train_e["cantidad_esc"].mean() == pytest.approx(0.0, abs=1e-8)
        assert params["media"][0] == pytest.approx(train["cantidad"].mean())

    def test_no_falla_con_bloque_vacio(self):
        df = _df_sintetico(3)
        serie = preparar_serie_diaria(df)
        train, val, test = dividir_train_val_test(serie, val_size=0.4, test_size=0.4)
        # No debe lanzar excepción aunque algún bloque quede vacío
        escalar_features(train, val, test, ["cantidad"])


class TestPipelineCompleto:
    def test_pipeline_con_dataset_vacio(self, monkeypatch):
        import ia.data_preparation as dp
        monkeypatch.setattr(dp, "construir_dataset_historico", lambda id_plato=None: pd.DataFrame())

        resultado = preparar_pipeline_completo(id_plato=9999)
        assert resultado["train"].empty
        assert "Sin datos históricos" in resultado["advertencias"][0]

    def test_pipeline_con_datos_sinteticos(self, monkeypatch):
        import ia.data_preparation as dp
        df = _df_sintetico(60)
        monkeypatch.setattr(dp, "construir_dataset_historico", lambda id_plato=None: df)

        resultado = preparar_pipeline_completo(id_plato=1)
        assert not resultado["serie_diaria"].empty
        assert len(resultado["train"]) > 0
        assert "columnas" in resultado["scaler_params"]
