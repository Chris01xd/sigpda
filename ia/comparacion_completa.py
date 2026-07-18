"""
=================================================================
SIGPDA - Comparación científica de los 5 modelos de la tesis
=================================================================
Modelos: ARIMA, Prophet, Holt-Winters, Transformer+Random Forest,
Transformer+Gradient Boosting.

Esta función núcleo la reutilizan:
  - ia.model_registry (reentrenar y guardar el modelo ganador, Fase 6)
  - el endpoint POST /ia/entrenar-comparar (Fase 8), que añade encima
    validación cruzada de 5 folds, tuning de hiperparámetros y las
    pruebas estadísticas completas (Friedman + Wilcoxon + DM).

NO reemplaza ni modifica /comparar-modelos (3 modelos, compatible
hacia atrás con el frontend existente): es un flujo independiente y
puramente aditivo.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import numpy as np

from ia.predictor import (
    construir_dataset_historico,
    enriquecer_features,
    recomendar_produccion,
    calcular_riesgo_desperdicio,
)
from ia.data_preparation import preparar_serie_diaria
from ia.metricas import calcular_metricas
from ia.modelos_clasicos import (
    entrenar_evaluar_arima, predecir_futuro_arima,
    entrenar_evaluar_prophet, predecir_futuro_prophet,
    entrenar_evaluar_holt_winters, predecir_futuro_holt_winters,
)
from ia.modelos_hibridos import (
    entrenar_evaluar_transformer_rf, predecir_futuro_transformer_rf,
    entrenar_evaluar_transformer_gbr, predecir_futuro_transformer_gbr,
)

logger = logging.getLogger(__name__)

MIN_DATOS_HISTORICOS = 30

NOMBRES_LEGIBLES = {
    "arima": "ARIMA",
    "prophet": "Prophet",
    "holt_winters": "Holt-Winters",
    "transformer_random_forest": "Transformer + Random Forest",
    "transformer_gradient_boosting": "Transformer + Gradient Boosting",
}


def _clave_ganador(metricas_por_modelo: dict, nombre: str) -> tuple:
    """Criterio de selección: menor MAE; empate -> menor RMSE -> menor SMAPE (sección 9)."""
    d = metricas_por_modelo[nombre]
    return (d["mae"], d.get("rmse") or 0.0, d.get("smape") or 0.0)


def comparar_cinco_modelos(
    id_plato: int,
    dias_adelante: int = 7,
    clima: int = 2,
    evento: int = 0,
) -> dict:
    """
    Compara los 5 modelos con un único split cronológico train/test
    (80/20, igual criterio que /comparar-modelos). Retorna además, para
    uso interno de otros módulos (no serializar directamente al
    frontend), la serie diaria, el DataFrame del plato y los errores
    por modelo (necesarios para pruebas estadísticas y persistencia).
    """
    df_global = construir_dataset_historico()
    if df_global.empty:
        return {"error": "Sin datos históricos. Genere ventas primero en el sistema."}

    df_enriquecido = enriquecer_features(df_global)
    df_plato = df_enriquecido[df_enriquecido["id_plato"] == id_plato].copy()
    if df_plato.empty:
        return {"error": f"No existen datos históricos para el plato con ID {id_plato}."}

    serie = preparar_serie_diaria(df_plato)
    if len(serie) < MIN_DATOS_HISTORICOS:
        return {
            "error": (
                f"Se requieren mínimo {MIN_DATOS_HISTORICOS} días de historial para "
                f"la comparación de modelos. El plato tiene {len(serie)} días registrados. "
                f"Genere más ventas históricas para activar este módulo."
            )
        }

    n_total = len(serie)
    n_train = max(int(n_total * 0.8), n_total - 20)
    n_train = min(n_train, n_total - 5)

    serie_train = serie.iloc[:n_train].reset_index(drop=True)
    serie_test = serie.iloc[n_train:].reset_index(drop=True)

    fecha_corte = serie_train["fecha"].iloc[-1]
    df_plato_train = df_plato[df_plato["fecha"] <= fecha_corte].copy()
    if df_plato_train.empty:
        n_pt = max(int(len(df_plato) * 0.8), len(df_plato) - 3)
        df_plato_train = df_plato.iloc[:n_pt].copy()

    y_test = serie_test["cantidad"].values.astype(float)
    n_test = len(serie_test)
    cat_enc = int(df_plato["cat_enc"].iloc[0]) if len(df_plato) > 0 else 0
    ventas_7d = float(df_plato["ventas_7d"].iloc[-1]) if len(df_plato) > 0 else 0.0

    metricas_por_modelo: dict = {}
    errores_por_modelo: dict = {}
    info_modelos: dict = {}

    def _evaluar(nombre, fn, *args):
        try:
            pred, err, info = fn(*args)
            metricas_por_modelo[nombre] = calcular_metricas(y_test, pred, valor_anterior=float(serie_train["cantidad"].iloc[-1]))
            errores_por_modelo[nombre] = err
            info_modelos[nombre] = info
        except Exception as exc:
            logger.warning(f"{nombre} falló: {exc}")
            metricas_por_modelo[nombre] = {
                "mae": None, "rmse": None, "mape": None, "smape": None, "u_theil": None, "r2": None, "error": str(exc),
            }
            errores_por_modelo[nombre] = np.full(n_test, np.nan)
            info_modelos[nombre] = {"error": str(exc)}

    _evaluar("arima", entrenar_evaluar_arima, serie_train, serie_test)
    _evaluar("prophet", entrenar_evaluar_prophet, serie_train, serie_test)
    _evaluar("holt_winters", entrenar_evaluar_holt_winters, serie_train, serie_test)
    _evaluar(
        "transformer_random_forest", entrenar_evaluar_transformer_rf,
        df_plato_train, serie_train, serie_test, cat_enc, clima, evento,
    )
    _evaluar(
        "transformer_gradient_boosting", entrenar_evaluar_transformer_gbr,
        df_plato_train, serie_train, serie_test, cat_enc, clima, evento,
    )

    mae_validos = {
        nombre: datos["mae"]
        for nombre, datos in metricas_por_modelo.items()
        if isinstance(datos.get("mae"), (int, float)) and datos["mae"] is not None
    }
    if not mae_validos:
        return {"error": "Ningún modelo pudo entrenarse correctamente. Verifique los datos históricos."}

    modelo_ganador = min(mae_validos, key=lambda n: _clave_ganador(metricas_por_modelo, n))
    mae_ganador = mae_validos[modelo_ganador]

    hoy = date.today()
    fechas_futuras = [hoy + timedelta(days=i + 1) for i in range(dias_adelante)]

    try:
        if modelo_ganador == "arima":
            valores_futuros = predecir_futuro_arima(serie, n_pasos=dias_adelante)
        elif modelo_ganador == "prophet":
            valores_futuros = predecir_futuro_prophet(serie, fechas_futuras)
        elif modelo_ganador == "holt_winters":
            valores_futuros = predecir_futuro_holt_winters(serie, n_pasos=dias_adelante)
        elif modelo_ganador == "transformer_random_forest":
            valores_futuros = predecir_futuro_transformer_rf(
                df_plato, fechas_futuras, ventas_7d, cat_enc, clima, evento,
            )
        else:
            valores_futuros = predecir_futuro_transformer_gbr(
                df_plato, fechas_futuras, ventas_7d, cat_enc, clima, evento,
            )
    except Exception as exc:
        logger.error(f"Error en predicciones futuras ({modelo_ganador}): {exc}")
        valores_futuros = np.zeros(dias_adelante)

    predicciones_futuras = []
    for fecha_f, demanda_f in zip(fechas_futuras, valores_futuros):
        demanda_f = max(0.0, float(demanda_f))
        recomendacion = recomendar_produccion(demanda_f, mae_ganador)
        riesgo = calcular_riesgo_desperdicio(demanda_f, recomendacion, mae_ganador)
        predicciones_futuras.append({
            "fecha": fecha_f.isoformat(),
            "demanda_estimada": round(demanda_f, 2),
            "recomendacion": recomendacion,
            "riesgo": riesgo,
        })

    return {
        "modelo_ganador": modelo_ganador,
        "modelo_ganador_legible": NOMBRES_LEGIBLES.get(modelo_ganador, modelo_ganador),
        "mae_ganador": round(mae_ganador, 4),
        "criterio_seleccion": "menor MAE (empate -> menor RMSE -> menor SMAPE)",
        "metricas_por_modelo": metricas_por_modelo,
        "info_modelos": info_modelos,
        "predicciones_futuras": predicciones_futuras,
        "n_datos_entrenamiento": int(len(serie_train)),
        "n_datos_prueba": int(len(serie_test)),
        # --- Campos de uso interno (NO exponer tal cual en un endpoint JSON) ---
        "_serie": serie,
        "_df_plato": df_plato,
        "_cat_enc": cat_enc,
        "_ventas_7d": ventas_7d,
        "_errores_por_modelo": errores_por_modelo,
    }
