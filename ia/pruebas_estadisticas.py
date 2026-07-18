"""
=================================================================
SIGPDA - Pruebas estadísticas para la comparación de modelos
=================================================================
- Diebold-Mariano (1995): comparación pareada de precisión predictiva
  (movida aquí desde ia.comparador_modelos; ver ese módulo, que ahora
  la reutiliza en vez de duplicarla).
- Prueba de Friedman: compara simultáneamente los k modelos.
- Prueba de Wilcoxon (signed-rank): modelo ganador vs cada competidor,
  con corrección de comparaciones múltiples Holm-Bonferroni.

Todas usan alpha = 0.05. Ninguna función retorna NaN sin explicación:
cuando una prueba no es aplicable (muestra insuficiente, varianza
cero, etc.) se documenta la razón en "interpretacion" y "aplicable"
queda en False. Nunca se afirma superioridad estadística si p >= alpha.

Referencia:
  Diebold, F.X. & Mariano, R.S. (1995). Comparing Predictive Accuracy.
    Journal of Business & Economic Statistics, 13(3), 253-263.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05
MIN_MUESTRA_DM = 3
MIN_MUESTRA_WILCOXON = 5
MIN_MODELOS_FRIEDMAN = 3
MIN_OBSERVACIONES_FRIEDMAN = 3


# ================================================================
# DIEBOLD-MARIANO (1995)
# ================================================================

def prueba_diebold_mariano(
    errores_m1: np.ndarray,
    errores_m2: np.ndarray,
    nombre_m1: str = "Modelo 1",
    nombre_m2: str = "Modelo 2",
) -> dict:
    """
    Prueba Diebold-Mariano para comparar la precisión predictiva de dos modelos.

    H₀: Los dos modelos tienen igual precisión predictiva (E[d_t] = 0).
    H₁: Los modelos difieren en precisión predictiva.

    Diferencial de pérdida cuadrática: d_t = L(e₁_t) - L(e₂_t)
    Estadístico: DM = d̄ / sqrt(V̂(d̄))  ~  N(0,1) asintóticamente

    Interpretación:
      DM > 0 → modelo 2 es más preciso (menor pérdida)
      DM < 0 → modelo 1 es más preciso
      p < 0.05 → diferencia estadísticamente significativa
    """
    e1 = np.asarray(errores_m1, dtype=float)
    e2 = np.asarray(errores_m2, dtype=float)
    n = len(e1)

    if n < MIN_MUESTRA_DM:
        return {
            "estadistico": None,
            "p_valor": None,
            "significativo": False,
            "interpretacion": f"Muestra insuficiente para la prueba DM (mín. {MIN_MUESTRA_DM} obs.)",
            "modelo_1": nombre_m1,
            "modelo_2": nombre_m2,
        }

    # Diferencial de pérdida cuadrática
    d = e1**2 - e2**2
    d_mean = float(np.mean(d))

    # Estimación de varianza espectral con corrección Newey-West (h=1)
    gamma_0 = float(np.var(d, ddof=1))
    if n > 2:
        gamma_1 = float(np.cov(d[1:], d[:-1], ddof=1)[0, 1])
        var_espectral = (gamma_0 + 2.0 * gamma_1) / n
    else:
        var_espectral = gamma_0 / n

    if var_espectral <= 0:
        return {
            "estadistico": 0.0,
            "p_valor": 1.0,
            "significativo": False,
            "interpretacion": "Varianza nula — ambos modelos producen errores idénticos",
            "modelo_1": nombre_m1,
            "modelo_2": nombre_m2,
        }

    dm_stat = d_mean / np.sqrt(abs(var_espectral))
    p_valor = float(2.0 * (1.0 - stats.norm.cdf(abs(dm_stat))))
    es_signi = p_valor < ALPHA

    if es_signi:
        mejor = nombre_m2 if dm_stat > 0 else nombre_m1
        interpretacion = (
            f"Diferencia significativa al 5 % — "
            f"{mejor} presenta mayor precisión predictiva"
        )
    else:
        interpretacion = (
            f"Sin diferencia estadísticamente significativa "
            f"entre {nombre_m1} y {nombre_m2} (p = {round(p_valor, 4)})"
        )

    return {
        "estadistico": round(float(dm_stat), 4),
        "p_valor": round(p_valor, 4),
        "significativo": es_signi,
        "interpretacion": interpretacion,
        "modelo_1": nombre_m1,
        "modelo_2": nombre_m2,
    }


# ================================================================
# PRUEBA DE FRIEDMAN — COMPARACIÓN SIMULTÁNEA DE k MODELOS
# ================================================================

def prueba_friedman(errores_por_modelo: dict) -> dict:
    """
    Prueba de Friedman: compara simultáneamente k >= 3 modelos
    relacionados (mismas fechas de evaluación) según sus errores
    absolutos.

    H0: todos los modelos tienen igual precisión predictiva.
    H1: al menos un modelo difiere de los demás.
    """
    hipotesis = "H0: igual precisión predictiva entre todos los modelos"
    nombres = list(errores_por_modelo.keys())
    n_modelos = len(nombres)

    if n_modelos < MIN_MODELOS_FRIEDMAN:
        return {
            "aplicable": False, "estadistico": None, "p_valor": None, "significativo": False,
            "hipotesis": hipotesis,
            "interpretacion": (
                f"Se requieren al menos {MIN_MODELOS_FRIEDMAN} modelos con errores "
                f"válidos para ejecutar Friedman (hay {n_modelos})."
            ),
        }

    arrays = [np.asarray(errores_por_modelo[n], dtype=float) for n in nombres]
    min_len = min(len(a) for a in arrays) if arrays else 0
    if min_len < MIN_OBSERVACIONES_FRIEDMAN:
        return {
            "aplicable": False, "estadistico": None, "p_valor": None, "significativo": False,
            "hipotesis": hipotesis,
            "interpretacion": (
                f"Muestra insuficiente ({min_len} observaciones alineadas) para Friedman "
                f"(mín. {MIN_OBSERVACIONES_FRIEDMAN})."
            ),
        }

    arrays = [a[:min_len] for a in arrays]
    mascara = np.ones(min_len, dtype=bool)
    for a in arrays:
        mascara &= ~np.isnan(a)
    arrays = [a[mascara] for a in arrays]
    n_validas = int(mascara.sum())

    if n_validas < MIN_OBSERVACIONES_FRIEDMAN:
        return {
            "aplicable": False, "estadistico": None, "p_valor": None, "significativo": False,
            "hipotesis": hipotesis,
            "interpretacion": (
                f"Muestra insuficiente tras excluir valores no válidos ({n_validas} observaciones)."
            ),
        }

    try:
        estadistico, p_valor = stats.friedmanchisquare(*arrays)
    except ValueError as exc:
        return {
            "aplicable": False, "estadistico": None, "p_valor": None, "significativo": False,
            "hipotesis": hipotesis,
            "interpretacion": f"No se pudo ejecutar la prueba de Friedman: {exc}",
        }

    significativo = bool(p_valor < ALPHA)
    p_fmt = round(float(p_valor), 4)
    interpretacion = (
        f"Diferencia estadísticamente significativa entre los {n_modelos} modelos "
        f"(p = {p_fmt} < {ALPHA})."
        if significativo else
        f"Sin diferencia estadísticamente significativa entre los {n_modelos} modelos "
        f"(p = {p_fmt} >= {ALPHA})."
    )

    return {
        "aplicable": True,
        "estadistico": round(float(estadistico), 4),
        "p_valor": p_fmt,
        "significativo": significativo,
        "n_observaciones": n_validas,
        "modelos": nombres,
        "hipotesis": hipotesis,
        "interpretacion": interpretacion,
    }


# ================================================================
# PRUEBA DE WILCOXON — GANADOR vs CADA COMPETIDOR (Holm-Bonferroni)
# ================================================================

def prueba_wilcoxon_multiple(
    nombre_ganador: str,
    errores_ganador: np.ndarray,
    errores_por_modelo: dict,
) -> list:
    """
    Prueba de Wilcoxon (signed-rank) entre el modelo ganador y cada uno
    de los demás modelos, con corrección de comparaciones múltiples
    Holm-Bonferroni (statsmodels.stats.multitest, method="holm").

    H0 (por comparación): la mediana de las diferencias de error entre
    el ganador y el competidor es cero (igual precisión predictiva).

    Retorna una lista de dicts, cada uno con p_valor original Y
    p_valor_ajustado.
    """
    hipotesis = "H0: la mediana de las diferencias de error es cero (igual precisión)"
    competidores = [n for n in errores_por_modelo if n != nombre_ganador]
    e_g = np.asarray(errores_ganador, dtype=float)

    resultados = []
    for nombre_comp in competidores:
        e_c = np.asarray(errores_por_modelo[nombre_comp], dtype=float)
        min_len = min(len(e_g), len(e_c))
        a, b = e_g[:min_len], e_c[:min_len]
        mascara = ~(np.isnan(a) | np.isnan(b))
        a, b = a[mascara], b[mascara]

        base = {"prueba": "wilcoxon", "modelo_a": nombre_ganador, "modelo_b": nombre_comp}

        if len(a) < MIN_MUESTRA_WILCOXON:
            resultados.append({
                **base, "estadistico": None, "p_valor": None, "aplicable": False,
                "interpretacion": (
                    f"Muestra insuficiente ({len(a)} obs.) para Wilcoxon "
                    f"(mín. {MIN_MUESTRA_WILCOXON})."
                ),
            })
            continue

        diffs = a - b
        if np.all(diffs == 0):
            resultados.append({
                **base, "estadistico": 0.0, "p_valor": 1.0, "aplicable": True,
                "interpretacion": "Errores idénticos entre ambos modelos en todas las observaciones.",
            })
            continue

        try:
            estadistico, p_valor = stats.wilcoxon(a, b, zero_method="wilcox")
            resultados.append({
                **base,
                "estadistico": round(float(estadistico), 4),
                "p_valor": round(float(p_valor), 4),
                "aplicable": True,
                "interpretacion": None,  # se completa tras la corrección Holm-Bonferroni
            })
        except ValueError as exc:
            resultados.append({
                **base, "estadistico": None, "p_valor": None, "aplicable": False,
                "interpretacion": f"No se pudo ejecutar Wilcoxon: {exc}",
            })

    # --- Corrección Holm-Bonferroni sobre los p-valores aplicables ---
    aplicables = [r for r in resultados if r["aplicable"] and r["p_valor"] is not None]
    if aplicables:
        p_valores = [r["p_valor"] for r in aplicables]
        rechazos, p_ajustados, _, _ = multipletests(p_valores, alpha=ALPHA, method="holm")
        for r, p_adj, rechazo in zip(aplicables, p_ajustados, rechazos):
            r["p_valor_ajustado"] = round(float(p_adj), 4)
            r["significativo"] = bool(rechazo)
            r["hipotesis"] = hipotesis
            if r["interpretacion"] is None:
                if r["significativo"]:
                    r["interpretacion"] = (
                        f"Diferencia significativa tras corrección Holm-Bonferroni "
                        f"(p original = {r['p_valor']}, p ajustado = {r['p_valor_ajustado']} < {ALPHA})."
                    )
                else:
                    r["interpretacion"] = (
                        f"Sin diferencia significativa tras corrección Holm-Bonferroni "
                        f"(p original = {r['p_valor']}, p ajustado = {r['p_valor_ajustado']} >= {ALPHA})."
                    )

    for r in resultados:
        r.setdefault("p_valor_ajustado", None)
        r.setdefault("significativo", False)
        r.setdefault("hipotesis", hipotesis)

    return resultados
