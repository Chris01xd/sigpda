"""
=================================================================
SIGPDA - Router de IA / Predicción de Demanda
=================================================================
Endpoints disponibles:

  POST /predecir           — predicción con modelo elegido por el usuario
  POST /comparar-modelos   — comparación automática ARIMA/Prophet/Transformer
  GET  /historial          — historial de predicciones guardadas
  GET  /platos-disponibles — lista de platos activos
=================================================================
"""

import logging
import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import date, timedelta

from backend.auth import obtener_usuario_actual
from ia.predictor import ejecutar_prediccion_completa
from ia.comparador_modelos import comparar_modelos_prediccion
from ia.eda import generar_eda
from ia.comparacion_completa import comparar_cinco_modelos
from ia.modelos_clasicos import (
    ajustar_arima_completo,
    ajustar_prophet_completo,
    ajustar_holt_winters_completo,
)
from ia.modelos_hibridos import (
    TransformerRandomForestModel,
    TransformerGradientBoostingModel,
    ajustar_hibrido_completo,
)
from ia.model_registry import (
    guardar_modelo,
    existe_modelo_vigente,
    listar_modelos_guardados,
    predecir_con_modelo_guardado,
    calcular_hash_dataset,
)
from database.conexion import obtener_sesion
from database.modelos import Plato, Prediccion, ComparacionModelos

router = APIRouter()
logger = logging.getLogger(__name__)

MODELOS_VALIDOS = {"random_forest", "regresion_lineal", "decision_tree", "transformer_hibrido"}


# ================================================================
# SCHEMAS PYDANTIC
# ================================================================

class PrediccionRequest(BaseModel):
    id_plato:     int
    dias_adelante: int = Field(default=7, ge=1, le=30)
    modelo_tipo:  str  = "random_forest"
    clima:        int  = Field(default=2, ge=1, le=3)
    evento:       int  = Field(default=0, ge=0, le=2)
    # Solo para transformer_hibrido (interfaz antigua)
    n_heads: int = Field(default=4, ge=1, le=8)
    d_k:     int = Field(default=16, ge=4, le=64)


class ComparacionRequest(BaseModel):
    """
    Request para la comparación automática de modelos.
    El usuario SOLO especifica: plato, días, clima y evento.
    Los hiperparámetros se calculan automáticamente en el backend.
    """
    id_plato:     int
    dias_adelante: int = Field(default=7, ge=1, le=30)
    clima:        int  = Field(default=2, ge=1, le=3)
    evento:       int  = Field(default=0, ge=0, le=2)


class ModeloGuardadoRequest(BaseModel):
    """Request para predecir/reentrenar con el modelo guardado de un plato."""
    dias_adelante: int = Field(default=7, ge=1, le=30)
    clima:        int  = Field(default=2, ge=1, le=3)
    evento:       int  = Field(default=0, ge=0, le=2)


class EntrenarCompararRequest(BaseModel):
    """
    Request del flujo completo de experimentación: EDA + comparación de
    5 modelos + validación cruzada + tuning + pruebas estadísticas.
    """
    id_plato:       int
    dias_adelante:  int  = Field(default=7, ge=1, le=30)
    clima:          int  = Field(default=2, ge=1, le=3)
    evento:         int  = Field(default=0, ge=0, le=2)
    n_splits:       int  = Field(default=5, ge=2, le=5)
    ejecutar_tuning: bool = Field(default=True)
    guardar_ganador: bool = Field(default=True)


# ================================================================
# ENDPOINT: PREDICCIÓN INDIVIDUAL (existente, sin cambios)
# ================================================================

@router.post("/predecir")
def predecir(
    data: PrediccionRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """Predicción de demanda con el modelo elegido por el usuario."""
    if data.modelo_tipo not in MODELOS_VALIDOS:
        raise HTTPException(400, f"Modelo inválido. Opciones: {', '.join(MODELOS_VALIDOS)}")

    hoy    = date.today()
    fechas = [hoy + timedelta(days=i + 1) for i in range(data.dias_adelante)]

    resultados, mensaje, mae, r2, transformer_info = ejecutar_prediccion_completa(
        id_plato      = data.id_plato,
        fechas_objetivo = fechas,
        modelo_tipo   = data.modelo_tipo,
        clima         = data.clima,
        evento        = data.evento,
        n_heads       = data.n_heads,
        d_k           = data.d_k,
    )

    if not resultados:
        raise HTTPException(400, mensaje)

    # Persistir predicciones en la base de datos
    sesion = obtener_sesion()
    try:
        for r in resultados:
            pred = Prediccion(
                id_plato                = data.id_plato,
                fecha_objetivo          = r["fecha"],
                demanda_estimada        = r["demanda_estimada"],
                recomendacion_produccion = r["recomendacion"],
                riesgo_desperdicio      = r["riesgo"],
                modelo_usado            = data.modelo_tipo,
                mae                     = r["mae"],
                r2                      = r["r2"],
                confianza               = r["confianza"],
                id_usuario              = int(current_user["sub"]),
            )
            sesion.add(pred)
        sesion.commit()
    finally:
        sesion.close()

    return {
        "mensaje":          mensaje,
        "mae":              mae,
        "r2":               r2,
        "modelo_tipo":      data.modelo_tipo,
        "transformer_info": transformer_info,
        "resultados": [
            {**r, "fecha": r["fecha"].isoformat()}
            for r in resultados
        ],
    }


# ================================================================
# ENDPOINT: COMPARACIÓN AUTOMÁTICA DE MODELOS (nuevo)
# ================================================================

@router.post("/comparar-modelos")
def comparar_modelos(
    data: ComparacionRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """
    Compara automáticamente ARIMA, Prophet y Transformer Híbrido.

    El sistema:
      - Selecciona hiperparámetros automáticamente (el usuario NO los configura)
      - Usa validación temporal (split cronológico, no aleatorio)
      - Calcula MAE, RMSE, MAPE, R² para cada modelo
      - Aplica la prueba estadística Diebold-Mariano
      - Selecciona el mejor modelo por menor MAE
      - Guarda el resultado en la base de datos
      - Retorna predicciones futuras con el modelo ganador
    """
    resultado = comparar_modelos_prediccion(
        id_plato      = data.id_plato,
        dias_adelante = data.dias_adelante,
        clima         = data.clima,
        evento        = data.evento,
    )

    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])

    # Persistir comparación en la base de datos
    sesion = obtener_sesion()
    try:
        metricas  = resultado.get("metricas_por_modelo", {})
        dm_dict   = resultado.get("diebold_mariano", {})

        # Obtener primer resultado DM para persistencia
        primer_dm = next(iter(dm_dict.values()), {}) if dm_dict else {}

        comparacion = ComparacionModelos(
            id_plato          = data.id_plato,
            id_usuario        = int(current_user["sub"]),
            modelo_ganador    = resultado.get("modelo_ganador"),
            dias_adelante     = data.dias_adelante,
            clima             = data.clima,
            evento            = data.evento,
            # ARIMA
            mae_arima         = metricas.get("arima",  {}).get("mae"),
            rmse_arima        = metricas.get("arima",  {}).get("rmse"),
            mape_arima        = metricas.get("arima",  {}).get("mape"),
            r2_arima          = metricas.get("arima",  {}).get("r2"),
            # Prophet
            mae_prophet       = metricas.get("prophet", {}).get("mae"),
            rmse_prophet      = metricas.get("prophet", {}).get("rmse"),
            mape_prophet      = metricas.get("prophet", {}).get("mape"),
            r2_prophet        = metricas.get("prophet", {}).get("r2"),
            # Transformer
            mae_transformer   = metricas.get("transformer_hibrido", {}).get("mae"),
            rmse_transformer  = metricas.get("transformer_hibrido", {}).get("rmse"),
            mape_transformer  = metricas.get("transformer_hibrido", {}).get("mape"),
            r2_transformer    = metricas.get("transformer_hibrido", {}).get("r2"),
            # Diebold-Mariano
            dm_estadistico    = primer_dm.get("estadistico"),
            dm_p_valor        = primer_dm.get("p_valor"),
            dm_significativo  = primer_dm.get("significativo"),
            dm_interpretacion = primer_dm.get("interpretacion", "")[:255] if primer_dm.get("interpretacion") else None,
        )
        sesion.add(comparacion)
        sesion.commit()
    except Exception as exc:
        logger.error(f"Error guardando comparación en BD: {exc}")
    finally:
        sesion.close()

    return resultado


# ================================================================
# ENDPOINT: HISTORIAL DE PREDICCIONES
# ================================================================

@router.get("/historial")
def historial(current_user: dict = Depends(obtener_usuario_actual)):
    """Retorna las últimas 100 predicciones individuales registradas."""
    sesion = obtener_sesion()
    try:
        preds = (
            sesion.query(Prediccion)
            .order_by(Prediccion.fecha_generacion.desc())
            .limit(100)
            .all()
        )
        return [
            {
                "id_prediccion":          p.id_prediccion,
                "id_plato":               p.id_plato,
                "plato":                  p.plato.nombre if p.plato else "",
                "fecha_objetivo":         p.fecha_objetivo.isoformat() if p.fecha_objetivo else None,
                "demanda_estimada":       p.demanda_estimada,
                "recomendacion_produccion": p.recomendacion_produccion,
                "riesgo_desperdicio":     p.riesgo_desperdicio,
                "modelo_usado":           p.modelo_usado,
                "mae":                    p.mae,
                "r2":                     p.r2,
                "confianza":              p.confianza,
                "fecha_generacion":       p.fecha_generacion.isoformat() if p.fecha_generacion else None,
            }
            for p in preds
        ]
    finally:
        sesion.close()


# ================================================================
# ENDPOINT: PLATOS DISPONIBLES
# ================================================================

@router.get("/platos-disponibles")
def platos_disponibles(current_user: dict = Depends(obtener_usuario_actual)):
    """Lista de platos activos disponibles para predicción."""
    sesion = obtener_sesion()
    try:
        platos = sesion.query(Plato).filter(Plato.estado == True).all()
        return [
            {"id_plato": p.id_plato, "nombre": p.nombre, "categoria": p.categoria}
            for p in platos
        ]
    finally:
        sesion.close()


# ================================================================
# ENDPOINT: ANÁLISIS EXPLORATORIO DE DATOS (EDA)
# ================================================================

@router.get("/eda/{id_plato}")
def eda_plato(
    id_plato: int,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """
    Análisis exploratorio de datos (EDA) del histórico de un plato:
    estadísticas descriptivas, calidad de datos, distribución,
    estacionalidad y correlaciones. Devuelve datos estructurados
    (no imágenes) para que React construya los gráficos.
    """
    try:
        resultado = generar_eda(id_plato)
    except Exception as exc:
        logger.error(f"Error generando EDA para plato {id_plato}: {exc}")
        raise HTTPException(status_code=500, detail="No se pudo generar el análisis exploratorio.")

    if resultado is None:
        raise HTTPException(status_code=404, detail=f"No existe el plato con ID {id_plato}.")

    return resultado


# ================================================================
# ENDPOINTS: MODELO GUARDADO (persistencia sin reentrenar)
# ================================================================

def _hash_dataset_actual(id_plato: int) -> str | None:
    """Calcula la firma del histórico actual de un plato (o None si no hay datos)."""
    from ia.predictor import construir_dataset_historico
    from ia.data_preparation import preparar_serie_diaria

    df_plato = construir_dataset_historico(id_plato=id_plato)
    if df_plato.empty:
        return None

    serie = preparar_serie_diaria(df_plato)
    return calcular_hash_dataset(
        n_registros=len(df_plato),
        fecha_inicio=str(serie["fecha"].min().date()),
        fecha_fin=str(serie["fecha"].max().date()),
        suma_cantidad=float(df_plato["cantidad"].sum()),
    )


@router.get("/modelos-guardados")
def modelos_guardados_lista(current_user: dict = Depends(obtener_usuario_actual)):
    """Lista todos los modelos guardados (uno por plato como máximo)."""
    return listar_modelos_guardados()


@router.get("/modelos-guardados/{id_plato}")
def modelo_guardado_detalle(
    id_plato: int,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """
    Informa si hay un modelo guardado para el plato, cuándo se
    entrenó, sus métricas, y si los datos históricos cambiaron desde
    entonces (recomendando reentrenar en ese caso).
    """
    hash_actual = _hash_dataset_actual(id_plato)
    resultado = existe_modelo_vigente(id_plato, hash_datos_actual=hash_actual)

    if not resultado["existe"]:
        raise HTTPException(status_code=404, detail=f"No hay modelo guardado para el plato {id_plato}.")

    return resultado


@router.post("/modelos-guardados/{id_plato}/predecir")
def modelo_guardado_predecir(
    id_plato: int,
    data: ModeloGuardadoRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """Predice usando el modelo previamente guardado para el plato, SIN reentrenar."""
    resultado = predecir_con_modelo_guardado(
        id_plato, data.dias_adelante, data.clima, data.evento,
    )
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    return resultado


@router.post("/modelos-guardados/{id_plato}/reentrenar")
def modelo_guardado_reentrenar(
    id_plato: int,
    data: ModeloGuardadoRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """
    Ejecuta la comparación de los 5 modelos y guarda el ganador,
    reemplazando el modelo previamente guardado (si existía) para
    este plato.
    """
    t0 = time.perf_counter()
    resultado = comparar_cinco_modelos(
        id_plato=id_plato,
        dias_adelante=data.dias_adelante,
        clima=data.clima,
        evento=data.evento,
    )
    duracion = time.perf_counter() - t0
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])

    ganador = resultado["modelo_ganador"]
    serie = resultado["_serie"]
    df_plato = resultado["_df_plato"]

    sesion = obtener_sesion()
    try:
        plato = sesion.query(Plato).filter(Plato.id_plato == id_plato).first()
        nombre_plato = plato.nombre if plato else str(id_plato)
    finally:
        sesion.close()

    try:
        if ganador == "arima":
            modelo_objeto, hp = ajustar_arima_completo(serie)
        elif ganador == "prophet":
            modelo_objeto, hp = ajustar_prophet_completo(serie)
        elif ganador == "holt_winters":
            modelo_objeto, hp = ajustar_holt_winters_completo(serie)
        elif ganador == "transformer_random_forest":
            modelo_objeto, hp = ajustar_hibrido_completo(TransformerRandomForestModel, df_plato)
        else:
            modelo_objeto, hp = ajustar_hibrido_completo(TransformerGradientBoostingModel, df_plato)
    except Exception as exc:
        logger.error(f"Error ajustando el modelo ganador '{ganador}' para persistir (plato {id_plato}): {exc}")
        raise HTTPException(status_code=500, detail="No se pudo entrenar el modelo ganador para guardarlo.")

    hash_datos = calcular_hash_dataset(
        n_registros=len(df_plato),
        fecha_inicio=str(serie["fecha"].min().date()),
        fecha_fin=str(serie["fecha"].max().date()),
        suma_cantidad=float(df_plato["cantidad"].sum()),
    )

    guardado = guardar_modelo(
        id_plato=id_plato,
        nombre_plato=nombre_plato,
        tipo_modelo=ganador,
        modelo_objeto=modelo_objeto,
        hiperparametros=hp,
        metricas=resultado["metricas_por_modelo"][ganador],
        n_registros=len(df_plato),
        fecha_inicio_datos=str(serie["fecha"].min().date()),
        fecha_fin_datos=str(serie["fecha"].max().date()),
        hash_datos=hash_datos,
        contexto_prediccion={"ventas_7d": resultado["_ventas_7d"], "cat_enc": resultado["_cat_enc"]},
    )

    # Historial en BD (tablas normalizadas, Fase 7). No debe romper la
    # respuesta si falla: el modelo ya quedó guardado en disco.
    try:
        from ia.persistencia_bd import guardar_ejecucion_comparacion, guardar_registro_modelo_guardado

        id_ejecucion = guardar_ejecucion_comparacion(
            id_plato=id_plato,
            id_usuario=int(current_user["sub"]),
            resultado_comparacion=resultado,
            dias_adelante=data.dias_adelante,
            clima=data.clima,
            evento=data.evento,
            duracion_segundos=round(duracion, 4),
        )
        guardar_registro_modelo_guardado(
            id_plato=id_plato,
            id_ejecucion=id_ejecucion,
            modelo=ganador,
            hash_datos=hash_datos,
            metadata={"tipo_modelo": ganador, "fecha": guardado.get("fecha")},
        )
    except Exception as exc:
        logger.error(f"Error guardando historial de ejecución en BD (plato {id_plato}): {exc}")

    return {
        "guardado": guardado,
        "modelo_ganador": ganador,
        "modelo_ganador_legible": resultado["modelo_ganador_legible"],
        "criterio_seleccion": resultado["criterio_seleccion"],
        "metricas": resultado["metricas_por_modelo"][ganador],
        "metricas_por_modelo": resultado["metricas_por_modelo"],
        "predicciones_futuras": resultado["predicciones_futuras"],
        "mensaje": f"Modelo '{ganador}' entrenado y guardado correctamente para el plato {id_plato}.",
    }


# ================================================================
# ENDPOINT PRINCIPAL DE EXPERIMENTACIÓN: 5 MODELOS + CV + TUNING + PRUEBAS
# ================================================================

@router.post("/entrenar-comparar")
def entrenar_comparar(
    data: EntrenarCompararRequest,
    current_user: dict = Depends(obtener_usuario_actual),
):
    """
    Flujo completo de experimentación científica para un plato:
      1. EDA resumido
      2. Comparación de 5 modelos (ARIMA, Prophet, Holt-Winters,
         Transformer+Random Forest, Transformer+Gradient Boosting)
      3. Optimización de hiperparámetros (RandomizedSearchCV /
         búsqueda temporal propia; sin Optuna, sin validación aleatoria)
      4. Validación cruzada temporal (hasta 5 folds walk-forward)
      5. Pruebas estadísticas: Friedman, Wilcoxon (Holm-Bonferroni),
         Diebold-Mariano
      6. Guardado opcional del modelo ganador (sin reentrenar después)

    Es SÍNCRONO y puede tardar decenas de segundos: React debe mostrar
    un indicador de carga explícito mientras se ejecuta.
    """
    from ia.orquestador import ejecutar_flujo_completo
    from ia.persistencia_bd import guardar_ejecucion_comparacion, guardar_registro_modelo_guardado

    resultado = ejecutar_flujo_completo(
        id_plato=data.id_plato,
        dias_adelante=data.dias_adelante,
        clima=data.clima,
        evento=data.evento,
        n_splits=data.n_splits,
        ejecutar_tuning=data.ejecutar_tuning,
    )
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])

    ganador = resultado["modelo_ganador"]
    serie = resultado["_serie"]
    df_plato = resultado["_df_plato"]

    # --- Guardado opcional del modelo ganador (sin exponer objetos internos) ---
    modelo_guardado_info: dict = {"guardado": False}
    hash_datos = None

    if data.guardar_ganador:
        try:
            if ganador == "arima":
                modelo_objeto, hp = ajustar_arima_completo(serie)
            elif ganador == "prophet":
                modelo_objeto, hp = ajustar_prophet_completo(serie)
            elif ganador == "holt_winters":
                modelo_objeto, hp = ajustar_holt_winters_completo(serie)
            elif ganador == "transformer_random_forest":
                modelo_objeto, hp = ajustar_hibrido_completo(TransformerRandomForestModel, df_plato)
            else:
                modelo_objeto, hp = ajustar_hibrido_completo(TransformerGradientBoostingModel, df_plato)

            sesion = obtener_sesion()
            try:
                plato = sesion.query(Plato).filter(Plato.id_plato == data.id_plato).first()
                nombre_plato = plato.nombre if plato else str(data.id_plato)
            finally:
                sesion.close()

            hash_datos = calcular_hash_dataset(
                n_registros=len(df_plato),
                fecha_inicio=str(serie["fecha"].min().date()),
                fecha_fin=str(serie["fecha"].max().date()),
                suma_cantidad=float(df_plato["cantidad"].sum()),
            )
            modelo_guardado_info = guardar_modelo(
                id_plato=data.id_plato,
                nombre_plato=nombre_plato,
                tipo_modelo=ganador,
                modelo_objeto=modelo_objeto,
                hiperparametros=hp,
                metricas=resultado["metricas_por_modelo"][ganador],
                n_registros=len(df_plato),
                fecha_inicio_datos=str(serie["fecha"].min().date()),
                fecha_fin_datos=str(serie["fecha"].max().date()),
                hash_datos=hash_datos,
                contexto_prediccion={"ventas_7d": resultado["_ventas_7d"], "cat_enc": resultado["_cat_enc"]},
            )
        except Exception as exc:
            logger.error(f"No se pudo guardar el modelo ganador (plato {data.id_plato}): {exc}")
            modelo_guardado_info = {"guardado": False, "motivo": "No se pudo entrenar/guardar el modelo ganador."}

    # --- Historial en BD (tablas normalizadas). No debe romper la respuesta si falla. ---
    id_ejecucion = None
    try:
        pruebas_lista = (
            [resultado["pruebas_estadisticas"]["friedman"]]
            + resultado["pruebas_estadisticas"]["wilcoxon"]
            + resultado["pruebas_estadisticas"]["diebold_mariano"]
        )
        id_ejecucion = guardar_ejecucion_comparacion(
            id_plato=data.id_plato,
            id_usuario=int(current_user["sub"]),
            resultado_comparacion=resultado,
            dias_adelante=data.dias_adelante,
            clima=data.clima,
            evento=data.evento,
            duracion_segundos=resultado.get("duracion_total_segundos"),
            pruebas_estadisticas=pruebas_lista,
            folds_por_modelo=resultado.get("validacion_cruzada"),
            metadata_extra={
                "eda_resumen": resultado.get("eda_resumen"),
                "predicciones_futuras": resultado.get("predicciones_futuras"),
                "interpretacion": resultado.get("interpretacion"),
                "hiperparametros_tuning": resultado.get("hiperparametros"),
                "modelo_ganador_legible": resultado.get("modelo_ganador_legible"),
                "mae_ganador": resultado.get("mae_ganador"),
            },
        )
        if data.guardar_ganador and modelo_guardado_info.get("guardado") and hash_datos:
            guardar_registro_modelo_guardado(
                id_plato=data.id_plato, id_ejecucion=id_ejecucion, modelo=ganador,
                hash_datos=hash_datos, metadata={"tipo_modelo": ganador},
            )
    except Exception as exc:
        logger.error(f"Error guardando historial de ejecución en BD (plato {data.id_plato}): {exc}")

    # --- Respuesta pública (sin objetos internos no serializables) ---
    respuesta = {k: v for k, v in resultado.items() if not k.startswith("_")}
    respuesta["ejecucion_id"] = id_ejecucion
    respuesta["estado"] = "completado"
    respuesta["dataset"] = {
        "registros": len(df_plato),
        "fecha_inicio": str(serie["fecha"].min().date()),
        "fecha_fin": str(serie["fecha"].max().date()),
        "advertencias": resultado["eda_resumen"]["advertencias"],
    }
    respuesta["modelo_guardado"] = modelo_guardado_info

    return respuesta
