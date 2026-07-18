"""
Pruebas del módulo de Análisis Exploratorio de Datos (ia/eda.py).
Usa `generar_eda_desde_df`, la función pura, con datos sintéticos
para no depender de la base de datos real.
"""
import numpy as np
import pandas as pd
import pytest

from ia.eda import generar_eda_desde_df


def _df_crudo(n_dias=40, id_plato=1, categoria="Entradas", semilla=7):
    """Simula la salida de _consultar_transacciones_crudas: una fila por venta."""
    fechas = pd.date_range("2026-01-01", periods=n_dias, freq="D")
    rng = np.random.default_rng(semilla)
    cantidades = rng.integers(1, 20, size=n_dias).astype(float)
    return pd.DataFrame({
        "id_venta": np.arange(1, n_dias + 1),  # una venta distinta por fila
        "id_plato": id_plato,
        "fecha": fechas,
        "cantidad": cantidades,
        "categoria": categoria,
        "precio": 15.5,
    })


class TestEdaDatosVacios:
    def test_dataframe_vacio(self):
        resultado = generar_eda_desde_df(pd.DataFrame(), plato_nombre="Ceviche", categoria="Marinos")
        assert resultado["resumen"]["registros_transacciones"] == 0
        assert resultado["resumen"]["plato"] == "Ceviche"
        assert resultado["advertencias"]
        assert resultado["serie_historica"] == []
        assert resultado["estadisticas_descriptivas"] == {}

    def test_estructura_contiene_todas_las_claves_minimas(self):
        resultado = generar_eda_desde_df(pd.DataFrame())
        claves_esperadas = {
            "resumen", "estadisticas_descriptivas", "valores_faltantes", "duplicados",
            "outliers", "serie_historica", "distribucion", "por_dia_semana",
            "por_mes", "correlaciones", "advertencias",
        }
        assert claves_esperadas.issubset(resultado.keys())


class TestEdaConNulos:
    def test_nulos_en_precio_se_reportan_pero_no_rompen(self):
        df = _df_crudo(15)
        df.loc[3, "precio"] = np.nan
        resultado = generar_eda_desde_df(df)
        assert resultado["valores_faltantes"]["precio"] == 1
        assert resultado["resumen"]["registros_transacciones"] > 0

    def test_huecos_de_fecha_se_marcan_como_interpolados(self):
        df = _df_crudo(15)
        df_con_hueco = df.drop(df.index[7])
        resultado = generar_eda_desde_df(df_con_hueco)
        interpolados = [p for p in resultado["serie_historica"] if p["interpolado"]]
        assert len(interpolados) == 1
        assert any("interpolad" in a for a in resultado["advertencias"])


class TestEdaDuplicados:
    def test_duplicados_exactos_se_cuentan(self):
        df = _df_crudo(10)
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        resultado = generar_eda_desde_df(df_dup)
        assert resultado["duplicados"] == 1


class TestEdaEstadisticasDescriptivas:
    def test_media_mediana_std_min_max_correctos(self):
        fechas = pd.date_range("2026-01-01", periods=10, freq="D")
        cantidades = np.arange(1, 11, dtype=float)  # 1..10, serie determinista
        df = pd.DataFrame({
            "id_plato": 1, "fecha": fechas, "cantidad": cantidades,
            "categoria": "Entradas", "precio": 10.0,
        })
        resultado = generar_eda_desde_df(df)
        stats = resultado["estadisticas_descriptivas"]

        # El backend redondea a 4 decimales; se compara con esa misma tolerancia.
        assert stats["media"] == pytest.approx(round(float(np.mean(cantidades)), 4))
        assert stats["mediana"] == pytest.approx(round(float(np.median(cantidades)), 4))
        assert stats["desviacion_estandar"] == pytest.approx(round(float(np.std(cantidades, ddof=1)), 4))
        assert stats["minimo"] == pytest.approx(1.0)
        assert stats["maximo"] == pytest.approx(10.0)
        assert stats["q1"] == pytest.approx(round(float(np.percentile(cantidades, 25)), 4))
        assert stats["q3"] == pytest.approx(round(float(np.percentile(cantidades, 75)), 4))
        assert stats["rango_intercuartilico"] == pytest.approx(round(stats["q3"] - stats["q1"], 4))


class TestEdaOutliers:
    def test_valor_extremo_se_detecta_como_outlier(self):
        fechas = pd.date_range("2026-01-01", periods=20, freq="D")
        cantidades = np.full(20, 5.0)
        cantidades[10] = 500.0  # outlier evidente
        df = pd.DataFrame({
            "id_plato": 1, "fecha": fechas, "cantidad": cantidades,
            "categoria": "Entradas", "precio": 10.0,
        })
        resultado = generar_eda_desde_df(df)
        assert resultado["outliers"]["cantidad"] >= 1
        assert fechas[10].date().isoformat() in resultado["outliers"]["fechas"]


class TestEdaEstacionalidad:
    def test_por_dia_semana_tiene_siete_entradas(self):
        df = _df_crudo(30)
        resultado = generar_eda_desde_df(df)
        assert len(resultado["por_dia_semana"]) == 7

    def test_por_mes_vacio_si_cobertura_insuficiente(self):
        df = _df_crudo(20)  # menos de 60 días
        resultado = generar_eda_desde_df(df)
        assert resultado["por_mes"] == []
        assert any("insuficiente" in a.lower() for a in resultado["advertencias"])

    def test_por_mes_presente_con_cobertura_suficiente(self):
        df = _df_crudo(70)
        resultado = generar_eda_desde_df(df)
        assert len(resultado["por_mes"]) >= 2


class TestEdaCorrelaciones:
    def test_matriz_de_correlacion_es_simetrica_y_diagonal_uno(self):
        # 45 días para asegurar variación en "mes" (evita columnas de varianza
        # cero, cuya autocorrelación es indefinida — None — igual que en pandas).
        df = _df_crudo(45)
        resultado = generar_eda_desde_df(df)
        corr = resultado["correlaciones"]
        assert corr, "Se esperaba una matriz de correlaciones no vacía"
        for col in corr:
            diagonal = corr[col][col]
            if diagonal is not None:
                assert diagonal == pytest.approx(1.0)
            for otra_col, valor in corr[col].items():
                if valor is not None:
                    assert valor == pytest.approx(corr[otra_col][col])


class TestEdaAdvertenciaDatasetPequeno:
    def test_advierte_cuando_hay_menos_de_30_dias(self):
        df = _df_crudo(15)
        resultado = generar_eda_desde_df(df)
        assert any("30 días" in a or "30 dias" in a for a in resultado["advertencias"])
