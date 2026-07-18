"""
Pruebas de ia/modelos_hibridos.py: Transformer+RandomForest y
Transformer+GradientBoosting como modelos independientes.
"""
import numpy as np
import pandas as pd
import pytest

from ia.modelos_hibridos import (
    TransformerRandomForestModel,
    TransformerGradientBoostingModel,
    construir_features_desde_serie,
    entrenar_evaluar_transformer_rf,
    entrenar_evaluar_transformer_gbr,
    predecir_futuro_transformer_rf,
    predecir_futuro_transformer_gbr,
    ajustar_hibrido_completo,
    NOTA_ATENCION_NO_ENTRENADA,
)
from ia.predictor import FEATURES


def _df_features(n=40, semilla=3):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2026-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "dia_semana": fechas.dayofweek,
        "mes": fechas.month,
        "dia_mes": fechas.day,
        "es_finde": (fechas.dayofweek >= 5).astype(int),
        "clima": rng.integers(1, 4, size=n),
        "evento": rng.integers(0, 3, size=n),
        "cat_enc": 0,
        "ventas_7d": rng.uniform(2, 10, size=n),
    })
    df["cantidad"] = rng.integers(1, 20, size=n).astype(float)
    df["fecha"] = fechas
    return df


class TestModelosBase:
    @pytest.mark.parametrize("clase", [TransformerRandomForestModel, TransformerGradientBoostingModel])
    def test_fit_predict_shapes(self, clase):
        df = _df_features(40)
        X = df[FEATURES].values
        y = df["cantidad"].values

        modelo = clase(n_heads=2, d_k=4, semilla=42)
        modelo.fit(X[:30], y[:30])
        pred = modelo.predict(X[30:])

        assert pred.shape == (10,)
        assert (pred >= 0).all()

    @pytest.mark.parametrize("clase", [TransformerRandomForestModel, TransformerGradientBoostingModel])
    def test_get_info_documenta_atencion_no_entrenada(self, clase):
        df = _df_features(30)
        X = df[FEATURES].values
        y = df["cantidad"].values
        modelo = clase(n_heads=2, d_k=4)
        modelo.fit(X, y)
        info = modelo.get_info()

        assert info["nota_atencion"] == NOTA_ATENCION_NO_ENTRENADA
        assert info["regresor"] == clase.NOMBRE_REGRESOR

    def test_predict_sin_entrenar_lanza_error(self):
        modelo = TransformerRandomForestModel()
        with pytest.raises(RuntimeError):
            modelo.predict(np.zeros((3, len(FEATURES))))

    def test_semilla_reproducible(self):
        df = _df_features(40)
        X = df[FEATURES].values
        y = df["cantidad"].values

        m1 = TransformerRandomForestModel(n_heads=2, d_k=4, semilla=7)
        m1.fit(X[:30], y[:30])
        p1 = m1.predict(X[30:])

        m2 = TransformerRandomForestModel(n_heads=2, d_k=4, semilla=7)
        m2.fit(X[:30], y[:30])
        p2 = m2.predict(X[30:])

        np.testing.assert_allclose(p1, p2)


class TestConstruirFeaturesDesdeSerie:
    def test_columnas_y_orden_correctos(self):
        fechas = pd.DataFrame({"fecha": pd.date_range("2026-02-01", periods=5, freq="D")})
        X = construir_features_desde_serie(fechas, ventas_7d_ref=5.0, cat_enc=2, clima=1, evento=0)
        assert X.shape == (5, len(FEATURES))
        assert X[0, 0] == pd.Timestamp("2026-02-01").dayofweek


class TestEntrenarEvaluarHibrido:
    def test_transformer_rf_entrena_y_evalua(self):
        df = _df_features(40)
        serie_train = df.iloc[:30][["fecha", "cantidad"]].reset_index(drop=True)
        serie_test = df.iloc[30:][["fecha", "cantidad"]].reset_index(drop=True)
        df_plato_train = df.iloc[:30]

        pred, errores, info = entrenar_evaluar_transformer_rf(
            df_plato_train, serie_train, serie_test, cat_enc=0, clima=2, evento=0,
        )
        assert len(pred) == len(serie_test)
        assert len(errores) == len(serie_test)
        assert info["regresor"] == "Random Forest"

    def test_transformer_gbr_entrena_y_evalua(self):
        df = _df_features(40)
        serie_train = df.iloc[:30][["fecha", "cantidad"]].reset_index(drop=True)
        serie_test = df.iloc[30:][["fecha", "cantidad"]].reset_index(drop=True)
        df_plato_train = df.iloc[:30]

        pred, errores, info = entrenar_evaluar_transformer_gbr(
            df_plato_train, serie_train, serie_test, cat_enc=0, clima=2, evento=0,
        )
        assert len(pred) == len(serie_test)
        assert info["regresor"] == "Gradient Boosting"

    def test_datos_insuficientes_lanza_valueerror(self):
        df = _df_features(4)
        serie_train = df[["fecha", "cantidad"]].reset_index(drop=True)
        serie_test = df[["fecha", "cantidad"]].reset_index(drop=True)
        with pytest.raises(ValueError):
            entrenar_evaluar_transformer_rf(df, serie_train, serie_test, 0, 2, 0)


class TestPredecirFuturo:
    def test_predecir_futuro_transformer_rf(self):
        df = _df_features(40)
        fechas_futuras = pd.date_range("2026-03-01", periods=5, freq="D")
        pred = predecir_futuro_transformer_rf(
            df, fechas_futuras, ventas_7d_ref=5.0, cat_enc=0, clima=2, evento=0,
        )
        assert len(pred) == 5
        assert (pred >= 0).all()

    def test_predecir_futuro_transformer_gbr(self):
        df = _df_features(40)
        fechas_futuras = pd.date_range("2026-03-01", periods=5, freq="D")
        pred = predecir_futuro_transformer_gbr(
            df, fechas_futuras, ventas_7d_ref=5.0, cat_enc=0, clima=2, evento=0,
        )
        assert len(pred) == 5


class TestAjustarHibridoCompleto:
    """Fase 6: ajusta sobre todo el dataset y retorna el objeto ya entrenado, para persistirlo."""

    @pytest.mark.parametrize("clase", [TransformerRandomForestModel, TransformerGradientBoostingModel])
    def test_retorna_modelo_ajustado_y_listo_para_predecir(self, clase):
        df = _df_features(40)
        modelo, info = ajustar_hibrido_completo(clase, df)

        assert modelo.is_fitted is True
        assert info["regresor"] == clase.NOMBRE_REGRESOR

        X_fut = construir_features_desde_serie(
            pd.DataFrame({"fecha": pd.date_range("2026-03-01", periods=3, freq="D")}),
            ventas_7d_ref=5.0, cat_enc=0, clima=2, evento=0,
        )
        pred = modelo.predict(X_fut)
        assert len(pred) == 3
