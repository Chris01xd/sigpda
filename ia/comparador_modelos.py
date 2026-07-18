"""
=================================================================
SIGPDA - Comparador Automático de Modelos de Predicción
=================================================================
Módulo de tesis que compara tres enfoques de predicción de demanda
alimentaria para el sistema SIGPDA:

  1. ARIMA     — modelo estadístico clásico para series de tiempo
  2. Prophet   — modelo de pronóstico de Meta/Facebook
  3. Transformer Híbrido — modelo propuesto del sistema (MHA + Ensemble)

Metodología:
  - Validación temporal (split cronológico, NO aleatorio)
  - Métricas de error: MAE, RMSE, MAPE, R²
  - Prueba estadística: Diebold-Mariano (1995)
  - Selección automática del mejor modelo por menor MAE
  - Hiperparámetros automáticos (sin intervención del usuario)

Referencias de tesis:
  - Diebold, F.X. & Mariano, R.S. (1995). Comparing Predictive Accuracy.
    Journal of Business & Economic Statistics, 13(3), 253-263.
  - Taylor, S.J. & Letham, B. (2018). Forecasting at scale. The American
    Statistician, 72(1), 37-45.
"""

from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd
from datetime import date, timedelta

from ia.predictor import (
    construir_dataset_historico,
    enriquecer_features,
    HybridTransformerModel,
    recomendar_produccion,
    calcular_riesgo_desperdicio,
    FEATURES,
)
from ia.data_preparation import preparar_serie_diaria as _preparar_serie_diaria
from ia.modelos_clasicos import (
    entrenar_evaluar_arima,
    predecir_futuro_arima,
    entrenar_evaluar_prophet,
    predecir_futuro_prophet,
)
from ia.modelos_hibridos import construir_features_desde_serie as _construir_features_desde_serie
from ia.metricas import calcular_metricas
from ia.pruebas_estadisticas import prueba_diebold_mariano

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# Mínimo de días históricos continuos requeridos para la comparación
MIN_DATOS_HISTORICOS = 30


# ================================================================
# MÉTRICAS DE ERROR
# ================================================================
# calcular_metricas (MAE, RMSE, MAPE, SMAPE, R²) está centralizada en
# ia.metricas (ver import arriba). Este endpoint ahora también recibe
# el campo "smape" en cada entrada de metricas_por_modelo (adición
# compatible: los campos anteriores mae/rmse/mape/r2 no cambian).


# ================================================================
# PRUEBA ESTADÍSTICA DIEBOLD-MARIANO (1995)
# ================================================================
# prueba_diebold_mariano está centralizada en ia.pruebas_estadisticas
# (ver import arriba), junto con las pruebas de Friedman y Wilcoxon
# (con corrección Holm-Bonferroni) añadidas para la comparación de 5
# modelos.

# ================================================================
# PREPARACIÓN DE SERIE TEMPORAL DIARIA CONTINUA
# ================================================================
# La construcción de la serie diaria continua (agregación + relleno
# de fechas por interpolación lineal) está centralizada en
# ia.data_preparation.preparar_serie_diaria() para que EDA y todos
# los modelos usen exactamente la misma lógica (ver import arriba).

# ================================================================
# MODELO ARIMA y MODELO PROPHET
# ================================================================
# entrenar_evaluar_arima / predecir_futuro_arima y
# entrenar_evaluar_prophet / predecir_futuro_prophet están
# centralizados en ia.modelos_clasicos (ver import arriba) para que
# la comparación de 3 modelos (este módulo) y la de 5 modelos
# (ia.modelos_clasicos + ia.modelos_hibridos) usen exactamente la
# misma implementación.

# ================================================================
# TRANSFORMER HÍBRIDO — VALIDACIÓN TEMPORAL E HIPERPARÁMETROS AUTO
# ================================================================
# NOTA: este es el HybridTransformerModel original (ensemble de 4
# modelos + meta-learner Ridge), conservado únicamente por
# compatibilidad con el endpoint /predecir (modelo_tipo=
# "transformer_hibrido") y con esta comparación de 3 modelos.
# La comparación científica de 5 modelos usa en su lugar los
# modelos independientes Transformer+RF y Transformer+GBR de
# ia.modelos_hibridos (construir_features_desde_serie, importado
# arriba, es la misma función que usan esos modelos).

def _auto_hiperparametros_transformer(n_muestras: int) -> tuple[int, int]:
    """
    Selecciona n_heads y d_k en función del tamaño del dataset.
    Mayor cantidad de datos → mayor capacidad representacional.
    """
    if n_muestras >= 200:
        return 4, 16
    elif n_muestras >= 100:
        return 4, 8
    elif n_muestras >= 50:
        return 2, 8
    else:
        return 2, 4


def entrenar_evaluar_transformer(
    df_plato_train: pd.DataFrame,
    serie_train:    pd.DataFrame,
    serie_test:     pd.DataFrame,
    cat_enc:        int,
    clima:          int,
    evento:         int,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Entrena el HybridTransformerModel con split temporal cronológico
    y evalúa sobre el mismo período de prueba que ARIMA y Prophet.

    El entrenamiento usa las features reales de df_plato_train.
    La evaluación construye features para cada fecha del test set.

    Retorna:
        pred_test   : predicciones
        errores_abs : |y_real − y_pred| por día
        info        : arquitectura e hiperparámetros seleccionados
    """
    if len(df_plato_train) < 5:
        raise ValueError(
            "Datos insuficientes en el período de entrenamiento "
            f"para el Transformer (solo {len(df_plato_train)} registros)."
        )

    X_train = df_plato_train[FEATURES].fillna(0).values
    y_train = df_plato_train["cantidad"].values.astype(float)

    n_heads, d_k = _auto_hiperparametros_transformer(len(X_train))
    modelo = HybridTransformerModel(n_heads=n_heads, d_k=d_k)
    modelo.fit(X_train, y_train)

    # Referencia de ventas para el período de prueba
    ventas_7d_ref = float(serie_train["cantidad"].tail(7).mean())

    X_test_transf = _construir_features_desde_serie(
        serie_test, ventas_7d_ref, cat_enc, clima, evento
    )
    pred_test = np.maximum(0.0, modelo.predict(X_test_transf))
    vals_test = serie_test["cantidad"].values.astype(float)
    errores   = np.abs(vals_test - pred_test)

    return pred_test, errores, {
        "arquitectura": modelo.get_info()["arquitectura"],
        "n_heads":      n_heads,
        "d_k":          d_k,
        "pesos_ensemble": modelo.meta_weights_,
    }


def predecir_futuro_transformer(
    df_plato:       pd.DataFrame,
    fechas_futuras: list,
    ventas_7d_ref:  float,
    cat_enc:        int,
    clima:          int,
    evento:         int,
) -> np.ndarray:
    """Re-entrena el Transformer en todo el dataset y predice fechas futuras."""
    X = df_plato[FEATURES].fillna(0).values
    y = df_plato["cantidad"].values.astype(float)

    n_heads, d_k = _auto_hiperparametros_transformer(len(X))
    modelo = HybridTransformerModel(n_heads=n_heads, d_k=d_k)
    modelo.fit(X, y)

    filas_futuras = []
    for f in fechas_futuras:
        fecha_dt = pd.Timestamp(f)
        filas_futuras.append({
            "dia_semana": fecha_dt.dayofweek,
            "mes":        fecha_dt.month,
            "dia_mes":    fecha_dt.day,
            "es_finde":   int(fecha_dt.dayofweek >= 5),
            "clima":      clima,
            "evento":     evento,
            "cat_enc":    cat_enc,
            "ventas_7d":  ventas_7d_ref,
        })

    X_fut = pd.DataFrame(filas_futuras)[FEATURES].values
    return np.maximum(0.0, modelo.predict(X_fut))


# ================================================================
# FUNCIÓN PRINCIPAL DE COMPARACIÓN DE MODELOS
# ================================================================

def comparar_modelos_prediccion(
    id_plato:     int,
    dias_adelante: int = 7,
    clima:        int = 2,
    evento:       int = 0,
) -> dict:
    """
    Función principal del comparador de modelos SIGPDA.

    Compara automáticamente ARIMA, Prophet y Transformer Híbrido
    para un plato específico, seleccionando el mejor por menor MAE
    y validando la diferencia con la prueba Diebold-Mariano.

    Flujo de ejecución:
      1.  Construir dataset histórico desde la base de datos
      2.  Agrupar demanda diaria por plato
      3.  Preparar serie temporal continua (relleno de fechas)
      4.  Split temporal 80/20 (cronológico, no aleatorio)
      5.  Entrenar y evaluar ARIMA con hiperparámetros automáticos
      6.  Entrenar y evaluar Prophet con hiperparámetros automáticos
      7.  Entrenar y evaluar Transformer con hiperparámetros automáticos
      8.  Calcular MAE, RMSE, MAPE, R² para cada modelo
      9.  Seleccionar modelo ganador (menor MAE)
      10. Aplicar Diebold-Mariano entre ganador y demás modelos
      11. Generar predicciones futuras con el modelo ganador
      12. Retornar resultado completo en JSON

    Parámetros:
        id_plato     : ID del plato en la base de datos
        dias_adelante: número de días futuros a predecir (1–30)
        clima        : condición climática (1=soleado, 2=nublado, 3=lluvia)
        evento       : tipo de evento (0=normal, 1=local, 2=feriado)

    Retorna:
        dict con modelo_ganador, métricas, Diebold-Mariano, predicciones
        y explicación interpretable para la tesis.
    """
    NOMBRES_LEGIBLES = {
        "arima":              "ARIMA",
        "prophet":            "Prophet",
        "transformer_hibrido": "Transformer Híbrido",
    }

    # ——— 1–2. Dataset histórico ———
    df_global = construir_dataset_historico()
    if df_global.empty:
        return {"error": "Sin datos históricos. Genere ventas primero en el sistema."}

    df_enriquecido = enriquecer_features(df_global)
    df_plato = df_enriquecido[df_enriquecido["id_plato"] == id_plato].copy()

    if df_plato.empty:
        return {"error": f"No existen datos históricos para el plato con ID {id_plato}."}

    # ——— 3. Serie temporal diaria continua ———
    serie = _preparar_serie_diaria(df_plato)

    if len(serie) < MIN_DATOS_HISTORICOS:
        return {
            "error": (
                f"Se requieren mínimo {MIN_DATOS_HISTORICOS} días de historial para "
                f"la comparación de modelos. El plato tiene {len(serie)} días registrados. "
                f"Genere más ventas históricas para activar este módulo."
            )
        }

    # ——— 4. Split temporal cronológico (80% train / 20% test) ———
    n_total = len(serie)
    n_train  = max(int(n_total * 0.8), n_total - 20)
    n_train  = min(n_train, n_total - 5)   # Al menos 5 puntos de test

    serie_train = serie.iloc[:n_train].reset_index(drop=True)
    serie_test  = serie.iloc[n_train:].reset_index(drop=True)

    # Alinear df_plato con la misma fecha de corte
    fecha_corte = serie_train["fecha"].iloc[-1]
    df_plato_train = df_plato[df_plato["fecha"] <= fecha_corte].copy()
    df_plato_test  = df_plato[df_plato["fecha"] > fecha_corte].copy()

    # Fallback si el split de df_plato queda vacío
    if df_plato_train.empty:
        n_pt = max(int(len(df_plato) * 0.8), len(df_plato) - 3)
        df_plato_train = df_plato.iloc[:n_pt].copy()

    y_test_serie = serie_test["cantidad"].values.astype(float)
    n_test       = len(serie_test)

    # Variables de contexto del plato
    cat_enc    = int(df_plato["cat_enc"].iloc[0]) if len(df_plato) > 0 else 0
    ventas_7d  = float(df_plato["ventas_7d"].iloc[-1]) if len(df_plato) > 0 else 0.0

    # ——— 5–7. Entrenar y evaluar los tres modelos ———
    metricas_por_modelo  = {}
    errores_por_modelo   = {}
    info_modelos         = {}

    # 5. ARIMA
    try:
        pred_arima, err_arima, info_arima = entrenar_evaluar_arima(
            serie_train, serie_test
        )
        metricas_por_modelo["arima"]  = calcular_metricas(y_test_serie, pred_arima, valor_anterior=float(serie_train["cantidad"].iloc[-1]))
        errores_por_modelo["arima"]   = err_arima
        info_modelos["arima"]         = info_arima
    except Exception as exc:
        logger.warning(f"ARIMA falló: {exc}")
        metricas_por_modelo["arima"]  = {
            "mae": None, "rmse": None, "mape": None, "smape": None, "u_theil": None, "r2": None, "error": str(exc)
        }
        errores_por_modelo["arima"]   = np.full(n_test, np.nan)
        info_modelos["arima"]         = {"error": str(exc)}

    # 6. Prophet
    try:
        pred_prophet, err_prophet, info_prophet = entrenar_evaluar_prophet(
            serie_train, serie_test
        )
        metricas_por_modelo["prophet"]  = calcular_metricas(y_test_serie, pred_prophet, valor_anterior=float(serie_train["cantidad"].iloc[-1]))
        errores_por_modelo["prophet"]   = err_prophet
        info_modelos["prophet"]         = info_prophet
    except Exception as exc:
        logger.warning(f"Prophet falló: {exc}")
        metricas_por_modelo["prophet"]  = {
            "mae": None, "rmse": None, "mape": None, "smape": None, "u_theil": None, "r2": None, "error": str(exc)
        }
        errores_por_modelo["prophet"]   = np.full(n_test, np.nan)
        info_modelos["prophet"]         = {"error": str(exc)}

    # 7. Transformer Híbrido (con validación temporal, sin split aleatorio)
    try:
        pred_transf, err_transf, info_transf = entrenar_evaluar_transformer(
            df_plato_train, serie_train, serie_test, cat_enc, clima, evento
        )
        metricas_por_modelo["transformer_hibrido"]  = calcular_metricas(y_test_serie, pred_transf, valor_anterior=float(serie_train["cantidad"].iloc[-1]))
        errores_por_modelo["transformer_hibrido"]   = err_transf
        info_modelos["transformer_hibrido"]         = info_transf
    except Exception as exc:
        logger.warning(f"Transformer falló: {exc}")
        metricas_por_modelo["transformer_hibrido"]  = {
            "mae": None, "rmse": None, "mape": None, "smape": None, "u_theil": None, "r2": None, "error": str(exc)
        }
        errores_por_modelo["transformer_hibrido"]   = np.full(n_test, np.nan)
        info_modelos["transformer_hibrido"]         = {"error": str(exc)}

    # ——— 8. Seleccionar modelo ganador por menor MAE ———
    mae_validos = {
        nombre: datos["mae"]
        for nombre, datos in metricas_por_modelo.items()
        if isinstance(datos.get("mae"), (int, float)) and datos["mae"] is not None
    }

    if not mae_validos:
        return {"error": "Ningún modelo pudo entrenarse correctamente. Verifique los datos históricos."}

    modelo_ganador = min(mae_validos, key=mae_validos.get)
    mae_ganador    = mae_validos[modelo_ganador]

    # ——— 9. Prueba Diebold-Mariano: ganador vs demás modelos ———
    dm_resultados = {}
    err_ganador   = errores_por_modelo[modelo_ganador]

    for nombre_modelo, err_modelo in errores_por_modelo.items():
        if nombre_modelo == modelo_ganador:
            continue
        # Filtrar NaN y alinear longitud para la prueba DM
        mascara  = ~(np.isnan(err_ganador) | np.isnan(err_modelo))
        err_g_ok = err_ganador[mascara]
        err_m_ok = err_modelo[mascara]
        min_len  = min(len(err_g_ok), len(err_m_ok))

        dm = prueba_diebold_mariano(
            errores_m1=err_m_ok[:min_len],
            errores_m2=err_g_ok[:min_len],
            nombre_m1=NOMBRES_LEGIBLES.get(nombre_modelo, nombre_modelo),
            nombre_m2=NOMBRES_LEGIBLES.get(modelo_ganador, modelo_ganador),
        )
        clave = f"{nombre_modelo}_vs_{modelo_ganador}"
        dm_resultados[clave] = dm

    # ——— 10. Predicciones futuras con el modelo ganador ———
    hoy            = date.today()
    fechas_futuras = [hoy + timedelta(days=i + 1) for i in range(dias_adelante)]

    try:
        if modelo_ganador == "arima":
            valores_futuros = predecir_futuro_arima(serie, n_pasos=dias_adelante)

        elif modelo_ganador == "prophet":
            valores_futuros = predecir_futuro_prophet(serie, fechas_futuras)

        else:  # transformer_hibrido
            valores_futuros = predecir_futuro_transformer(
                df_plato=df_plato,
                fechas_futuras=fechas_futuras,
                ventas_7d_ref=ventas_7d,
                cat_enc=cat_enc,
                clima=clima,
                evento=evento,
            )
    except Exception as exc:
        logger.error(f"Error en predicciones futuras ({modelo_ganador}): {exc}")
        valores_futuros = np.zeros(dias_adelante)

    predicciones_futuras = []
    for fecha_f, demanda_f in zip(fechas_futuras, valores_futuros):
        demanda_f    = max(0.0, float(demanda_f))
        recomendacion = recomendar_produccion(demanda_f, mae_ganador)
        riesgo        = calcular_riesgo_desperdicio(demanda_f, recomendacion, mae_ganador)
        predicciones_futuras.append({
            "fecha":            fecha_f.isoformat(),
            "demanda_estimada": round(demanda_f, 2),
            "recomendacion":    recomendacion,
            "riesgo":           riesgo,
        })

    # ——— 11. Construir respuesta final ———
    nombre_ganador_legible = NOMBRES_LEGIBLES.get(modelo_ganador, modelo_ganador)
    mae_ganador_fmt        = round(mae_ganador, 4)

    return {
        "modelo_ganador":          modelo_ganador,
        "modelo_ganador_legible":  nombre_ganador_legible,
        "mae_ganador":             mae_ganador_fmt,
        "metricas_por_modelo":     metricas_por_modelo,
        "info_modelos":            info_modelos,
        "diebold_mariano":         dm_resultados,
        "predicciones_futuras":    predicciones_futuras,
        "n_datos_entrenamiento":   int(len(serie_train)),
        "n_datos_prueba":          int(len(serie_test)),
        "explicacion": (
            f"El modelo {nombre_ganador_legible} fue seleccionado automáticamente "
            f"por presentar el menor error absoluto medio (MAE = {mae_ganador_fmt}). "
            f"Mientras el error tiende a cero, el modelo se considera más preciso. "
            f"La validación se realizó con un split temporal cronológico "
            f"({len(serie_train)} días de entrenamiento / {len(serie_test)} de prueba). "
            f"La prueba Diebold-Mariano valida estadísticamente si la diferencia "
            f"de precisión entre modelos es significativa (p < 0.05)."
        ),
    }
