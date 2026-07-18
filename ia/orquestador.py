"""
=================================================================
SIGPDA - Orquestador del flujo completo de experimentación de IA
=================================================================
Combina, para un plato:
  1. EDA resumido
  2. Comparación de 5 modelos con un único split (ia.comparacion_completa)
  3. Tuning de hiperparámetros por modelo (ia.tuning) — UNA sola vez
  4. Validación cruzada de hasta 5 folds POR MODELO (ia.validacion),
     usando los hiperparámetros hallados en el tuning — para no
     repetir una búsqueda costosa dentro de cada fold (sección 20:
     rendimiento en equipo de estudiante)
  5. Pruebas estadísticas: Friedman, Wilcoxon (Holm-Bonferroni), DM

Es la función que respalda el endpoint POST /ia/entrenar-comparar
(Fase 8). Retorna también campos internos (prefijo "_") con los
objetos de pandas/numpy necesarios para guardar el modelo ganador y
persistir el historial en BD; el router debe excluirlos de la
respuesta JSON.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from ia.eda import generar_eda_desde_df
from ia.comparacion_completa import comparar_cinco_modelos, NOMBRES_LEGIBLES
from ia.validacion import evaluar_modelo_cv
from ia.tuning import buscar_hiperparametros_temporal, buscar_hiperparametros_regresor_sklearn
from ia.pruebas_estadisticas import prueba_friedman, prueba_wilcoxon_multiple, prueba_diebold_mariano
from ia.modelos_clasicos import (
    entrenar_evaluar_arima_con_hp,
    entrenar_evaluar_prophet_con_hp,
    entrenar_evaluar_holt_winters_con_hp,
)
from ia.modelos_hibridos import (
    TransformerRandomForestModel,
    TransformerGradientBoostingModel,
    construir_features_desde_serie,
)
from ia.predictor import FEATURES, MultiHeadSelfAttention

logger = logging.getLogger(__name__)

N_COMBINACIONES_TUNING = 4


# ================================================================
# ADAPTADORES PARA VALIDACIÓN CRUZADA (contrato uniforme)
# ================================================================

def _adaptador_cv_clasico(fn_con_hp, hp: dict):
    """Envuelve un modelo clásico *_con_hp con hiperparámetros fijos para ia.validacion."""
    def _fn(serie_train, serie_val):
        return fn_con_hp(serie_train, serie_val, **hp)
    return _fn


def _adaptador_cv_hibrido(clase_modelo, df_plato, cat_enc, clima, evento, hp_regresor):
    """
    Crea un callable (serie_train, serie_val) -> (pred, err, info) para
    ia.validacion.evaluar_modelo_cv, cerrando sobre el contexto extra
    que los modelos híbridos necesitan (df_plato, clima, evento, etc.).
    """
    def _fn(serie_train, serie_val):
        fecha_ini, fecha_fin = serie_train["fecha"].min(), serie_train["fecha"].max()
        df_train = df_plato[(df_plato["fecha"] >= fecha_ini) & (df_plato["fecha"] <= fecha_fin)]
        if df_train.empty:
            df_train = df_plato.iloc[:max(5, len(df_plato) // 2)]

        modelo = clase_modelo(n_heads=4, d_k=16, **hp_regresor)
        X_train = df_train[FEATURES].fillna(0).values
        y_train = df_train["cantidad"].values.astype(float)
        modelo.fit(X_train, y_train)

        ventas_7d_ref = float(serie_train["cantidad"].tail(7).mean())
        X_val = construir_features_desde_serie(serie_val, ventas_7d_ref, cat_enc, clima, evento)
        pred = np.maximum(0.0, modelo.predict(X_val))
        err = np.abs(serie_val["cantidad"].values.astype(float) - pred)
        return pred, err, modelo.get_info()

    return _fn


def _tunear_regresor_hibrido(nombre: str, clase_modelo, df_plato) -> dict:
    """Tuning del regresor sklearn interno, sobre las features ya atendidas."""
    X = df_plato[FEATURES].fillna(0).values
    y = df_plato["cantidad"].values.astype(float)

    modelo_base = clase_modelo(n_heads=4, d_k=16)
    modelo_base.scaler.fit(X)
    Xs = modelo_base.scaler.transform(X)
    atencion = MultiHeadSelfAttention(Xs.shape[1], 4, 16, seed=42)
    Xa, _ = atencion.forward(Xs)
    Xc = np.concatenate([Xs, Xa], axis=1)

    regresor_base = modelo_base._crear_regresor()
    return buscar_hiperparametros_regresor_sklearn(nombre, regresor_base, Xc, y, n_iter=N_COMBINACIONES_TUNING)


# ================================================================
# FLUJO COMPLETO
# ================================================================

def ejecutar_flujo_completo(
    id_plato: int,
    dias_adelante: int = 7,
    clima: int = 2,
    evento: int = 0,
    n_splits: int = 5,
    ejecutar_tuning: bool = True,
) -> dict:
    """Orquesta EDA + comparación de 5 modelos + tuning + CV + pruebas estadísticas."""
    t0_total = time.perf_counter()

    resultado_base = comparar_cinco_modelos(id_plato, dias_adelante, clima, evento)
    if "error" in resultado_base:
        return resultado_base

    serie = resultado_base["_serie"]
    df_plato = resultado_base["_df_plato"]
    cat_enc = resultado_base["_cat_enc"]
    errores_por_modelo = resultado_base["_errores_por_modelo"]

    # --- EDA resumido ---
    # Incluye también las series necesarias para los gráficos de los
    # reportes (correlación, serie histórica, distribución, día de
    # semana): se persisten en metadata_json para no tener que
    # reconsultar ni reejecutar el EDA al generar PDF/Word/Excel.
    eda_completo = generar_eda_desde_df(df_plato, plato_nombre="", categoria="")
    eda_resumen = {
        "resumen": eda_completo["resumen"],
        "estadisticas_descriptivas": eda_completo["estadisticas_descriptivas"],
        "advertencias": eda_completo["advertencias"],
        "correlaciones": eda_completo.get("correlaciones") or {},
        "serie_historica": eda_completo.get("serie_historica") or [],
        "distribucion": eda_completo.get("distribucion") or [],
        "por_dia_semana": eda_completo.get("por_dia_semana") or [],
    }

    # --- Tuning por modelo (una sola vez; la CV reutiliza estos hiperparámetros) ---
    hiperparametros_por_modelo: dict = {}
    mejores_hp: dict = {}

    if ejecutar_tuning:
        r_arima = buscar_hiperparametros_temporal(
            "arima", entrenar_evaluar_arima_con_hp, serie, n_combinaciones=N_COMBINACIONES_TUNING,
        )
        hiperparametros_por_modelo["arima"] = r_arima
        mejores_hp["arima"] = r_arima.get("mejor_hiperparametros") or {}

        r_prophet = buscar_hiperparametros_temporal(
            "prophet", entrenar_evaluar_prophet_con_hp, serie, n_combinaciones=N_COMBINACIONES_TUNING,
        )
        hiperparametros_por_modelo["prophet"] = r_prophet
        mejores_hp["prophet"] = r_prophet.get("mejor_hiperparametros") or {}

        r_hw = buscar_hiperparametros_temporal(
            "holt_winters", entrenar_evaluar_holt_winters_con_hp, serie, n_combinaciones=N_COMBINACIONES_TUNING,
        )
        hiperparametros_por_modelo["holt_winters"] = r_hw
        mejores_hp["holt_winters"] = r_hw.get("mejor_hiperparametros") or {}

        for nombre, clase in (
            ("transformer_random_forest", TransformerRandomForestModel),
            ("transformer_gradient_boosting", TransformerGradientBoostingModel),
        ):
            try:
                r_tuning = _tunear_regresor_hibrido(nombre, clase, df_plato)
            except Exception as exc:
                logger.warning(f"Tuning de {nombre} falló: {exc}")
                r_tuning = {"aplicable": False, "motivo": str(exc)}
            hiperparametros_por_modelo[nombre] = r_tuning
            mejores_hp[nombre] = r_tuning.get("mejor_hiperparametros") or {}
    else:
        for nombre in NOMBRES_LEGIBLES:
            hiperparametros_por_modelo[nombre] = {"aplicable": False, "motivo": "Tuning desactivado por el usuario."}
            mejores_hp[nombre] = {}

    # --- Validación cruzada (hasta 5 folds), con los hiperparámetros del tuning ---
    validacion_cruzada = {
        "arima": evaluar_modelo_cv(
            _adaptador_cv_clasico(entrenar_evaluar_arima_con_hp, mejores_hp.get("arima") or {}),
            serie, n_splits=n_splits,
        ),
        "prophet": evaluar_modelo_cv(
            _adaptador_cv_clasico(entrenar_evaluar_prophet_con_hp, mejores_hp.get("prophet") or {}),
            serie, n_splits=n_splits,
        ),
        "holt_winters": evaluar_modelo_cv(
            _adaptador_cv_clasico(entrenar_evaluar_holt_winters_con_hp, mejores_hp.get("holt_winters") or {}),
            serie, n_splits=n_splits,
        ),
        "transformer_random_forest": evaluar_modelo_cv(
            _adaptador_cv_hibrido(
                TransformerRandomForestModel, df_plato, cat_enc, clima, evento,
                mejores_hp.get("transformer_random_forest") or {},
            ),
            serie, n_splits=n_splits,
        ),
        "transformer_gradient_boosting": evaluar_modelo_cv(
            _adaptador_cv_hibrido(
                TransformerGradientBoostingModel, df_plato, cat_enc, clima, evento,
                mejores_hp.get("transformer_gradient_boosting") or {},
            ),
            serie, n_splits=n_splits,
        ),
    }

    # --- Pruebas estadísticas ---
    friedman = prueba_friedman(errores_por_modelo)

    modelo_ganador = resultado_base["modelo_ganador"]
    wilcoxon = prueba_wilcoxon_multiple(modelo_ganador, errores_por_modelo[modelo_ganador], errores_por_modelo)

    diebold_mariano = []
    err_ganador = errores_por_modelo[modelo_ganador]
    for nombre, err in errores_por_modelo.items():
        if nombre == modelo_ganador:
            continue
        mascara = ~(np.isnan(err_ganador) | np.isnan(err))
        b, a = err_ganador[mascara], err[mascara]
        min_len = min(len(a), len(b))
        dm = prueba_diebold_mariano(
            a[:min_len], b[:min_len],
            NOMBRES_LEGIBLES.get(nombre, nombre), NOMBRES_LEGIBLES.get(modelo_ganador, modelo_ganador),
        )
        dm["modelo_a"] = nombre
        dm["modelo_b"] = modelo_ganador
        diebold_mariano.append(dm)

    duracion_total = time.perf_counter() - t0_total

    interpretacion = [
        resultado_base.get("explicacion") or (
            f"El modelo {resultado_base['modelo_ganador_legible']} fue seleccionado automáticamente "
            f"por presentar el menor error absoluto medio (MAE = {resultado_base['mae_ganador']})."
        ),
        friedman.get("interpretacion", ""),
    ]

    return {
        **{k: v for k, v in resultado_base.items() if not k.startswith("_")},
        "eda_resumen": eda_resumen,
        "hiperparametros": hiperparametros_por_modelo,
        "validacion_cruzada": validacion_cruzada,
        "pruebas_estadisticas": {
            "friedman": friedman,
            "wilcoxon": wilcoxon,
            "diebold_mariano": diebold_mariano,
        },
        "duracion_total_segundos": round(duracion_total, 2),
        "interpretacion": [i for i in interpretacion if i],
        # --- Campos de uso interno (el router debe excluirlos de la respuesta JSON) ---
        "_serie": serie,
        "_df_plato": df_plato,
        "_cat_enc": cat_enc,
        "_ventas_7d": resultado_base["_ventas_7d"],
        "_errores_por_modelo": errores_por_modelo,
    }
