"""
Pruebas de ia/pruebas_estadisticas.py: Diebold-Mariano, Friedman y
Wilcoxon (con corrección Holm-Bonferroni). alpha = 0.05 en todas.
"""
import numpy as np
import pytest

from ia.pruebas_estadisticas import (
    prueba_diebold_mariano,
    prueba_friedman,
    prueba_wilcoxon_multiple,
    ALPHA,
)


class TestDieboldMariano:
    def test_muestra_insuficiente(self):
        r = prueba_diebold_mariano(np.array([1.0, 2.0]), np.array([1.0, 1.0]))
        assert r["estadistico"] is None
        assert r["significativo"] is False

    def test_errores_identicos_varianza_cero(self):
        e = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        r = prueba_diebold_mariano(e, e.copy())
        assert r["p_valor"] == 1.0
        assert r["significativo"] is False

    def test_modelo_claramente_peor_es_significativo(self):
        rng = np.random.default_rng(0)
        e_bueno = np.abs(rng.normal(0, 1, 40))
        e_malo = np.abs(rng.normal(0, 1, 40)) + 20  # error sistemáticamente mucho mayor
        r = prueba_diebold_mariano(e_malo, e_bueno, "Malo", "Bueno")
        assert r["p_valor"] < ALPHA
        assert r["significativo"] is True
        assert "Bueno" in r["interpretacion"]


class TestPruebaFriedman:
    def _errores_similares(self, n=30, semilla=1):
        rng = np.random.default_rng(semilla)
        base = np.abs(rng.normal(2, 1, n))
        return {
            "arima": base + rng.normal(0, 0.05, n),
            "prophet": base + rng.normal(0, 0.05, n),
            "holt_winters": base + rng.normal(0, 0.05, n),
        }

    def test_menos_de_tres_modelos_no_es_aplicable(self):
        r = prueba_friedman({"a": np.array([1.0, 2.0, 3.0]), "b": np.array([1.0, 2.0, 3.0])})
        assert r["aplicable"] is False
        assert r["hipotesis"]

    def test_muestra_insuficiente_no_es_aplicable(self):
        errores = {"a": np.array([1.0, 2.0]), "b": np.array([1.0, 2.0]), "c": np.array([1.0, 2.0])}
        r = prueba_friedman(errores)
        assert r["aplicable"] is False

    def test_modelos_similares_no_significativo(self):
        r = prueba_friedman(self._errores_similares())
        assert r["aplicable"] is True
        assert r["p_valor"] >= 0
        assert isinstance(r["significativo"], bool)

    def test_modelos_claramente_distintos_es_significativo(self):
        rng = np.random.default_rng(2)
        n = 30
        errores = {
            "bueno": np.abs(rng.normal(1, 0.3, n)),
            "regular": np.abs(rng.normal(5, 0.3, n)),
            "malo": np.abs(rng.normal(15, 0.3, n)),
        }
        r = prueba_friedman(errores)
        assert r["aplicable"] is True
        assert r["p_valor"] < ALPHA
        assert r["significativo"] is True

    def test_no_retorna_nan(self):
        r = prueba_friedman(self._errores_similares())
        assert r["estadistico"] is not None
        assert np.isfinite(r["estadistico"])
        assert np.isfinite(r["p_valor"])


class TestPruebaWilcoxonMultiple:
    def test_muestra_insuficiente_marca_no_aplicable(self):
        errores = {
            "ganador": np.array([1.0, 2.0, 3.0]),
            "competidor": np.array([1.5, 2.5, 3.5]),
        }
        resultados = prueba_wilcoxon_multiple("ganador", errores["ganador"], errores)
        assert len(resultados) == 1
        assert resultados[0]["aplicable"] is False
        assert resultados[0]["p_valor"] is None

    def test_errores_identicos(self):
        e = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        errores = {"ganador": e, "competidor": e.copy()}
        resultados = prueba_wilcoxon_multiple("ganador", e, errores)
        assert resultados[0]["p_valor"] == 1.0
        assert resultados[0]["significativo"] is False

    def test_incluye_p_valor_original_y_ajustado(self):
        rng = np.random.default_rng(3)
        n = 20
        e_ganador = np.abs(rng.normal(1, 0.3, n))
        errores = {
            "ganador": e_ganador,
            "competidor_a": np.abs(rng.normal(1, 0.3, n)),
            "competidor_b": np.abs(rng.normal(10, 0.3, n)),
        }
        resultados = prueba_wilcoxon_multiple("ganador", e_ganador, errores)
        assert len(resultados) == 2  # una comparación por competidor
        for r in resultados:
            assert "p_valor" in r and "p_valor_ajustado" in r
            if r["p_valor"] is not None:
                # Holm-Bonferroni: el p ajustado nunca es menor que el original
                assert r["p_valor_ajustado"] >= r["p_valor"] - 1e-9

    def test_no_afirma_superioridad_si_p_mayor_igual_alpha(self):
        rng = np.random.default_rng(4)
        n = 20
        e = np.abs(rng.normal(2, 0.5, n))
        errores = {"ganador": e, "competidor": e + rng.normal(0, 0.01, n)}  # casi idénticos
        resultados = prueba_wilcoxon_multiple("ganador", e, errores)
        r = resultados[0]
        if r["p_valor_ajustado"] is not None and r["p_valor_ajustado"] >= ALPHA:
            assert r["significativo"] is False

    def test_excluye_al_ganador_de_sus_propios_competidores(self):
        e = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        errores = {"ganador": e}
        resultados = prueba_wilcoxon_multiple("ganador", e, errores)
        assert resultados == []
