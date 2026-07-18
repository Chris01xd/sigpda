"""
=================================================================
SIGPDA - Persistencia de ejecuciones de entrenamiento en BD
=================================================================
Guarda el resultado de ia.comparacion_completa.comparar_cinco_modelos()
(y, sobre esa base, la validación cruzada + tuning + pruebas
estadísticas de fases posteriores) en las tablas normalizadas:
EjecucionEntrenamiento, ResultadoModelo, ResultadoFold,
ResultadoPruebaEstadistica y ModeloGuardado.

No reemplaza la tabla ComparacionModelos (usada por /comparar-modelos,
3 modelos, compatible hacia atrás): es un historial adicional para la
comparación científica de 5 modelos.
"""

from __future__ import annotations

import json
import logging
from datetime import date

from database.conexion import obtener_sesion
from database.modelos import (
    EjecucionEntrenamiento,
    ResultadoModelo,
    ResultadoFold,
    ResultadoPruebaEstadistica,
    ModeloGuardado,
)

logger = logging.getLogger(__name__)

MODELOS_HIBRIDOS = {"transformer_random_forest", "transformer_gradient_boosting"}


def _a_fecha(valor) -> date | None:
    """Convierte una fecha ISO (str) o date a date; None si no es válida."""
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None


def guardar_ejecucion_comparacion(
    id_plato: int,
    id_usuario,
    resultado_comparacion: dict,
    dias_adelante: int,
    clima: int,
    evento: int,
    duracion_segundos: float | None = None,
    pruebas_estadisticas: list | None = None,
    folds_por_modelo: dict | None = None,
    metadata_extra: dict | None = None,
) -> int:
    """
    Persiste una ejecución completa de comparación de modelos:
    EjecucionEntrenamiento + un ResultadoModelo por modelo evaluado
    (+ ResultadoFold si se pasa `folds_por_modelo`) + las pruebas
    estadísticas dadas. Retorna id_ejecucion.

    `metadata_extra` (opcional) permite guardar en metadata_json datos
    que no tienen columna propia pero que ia.reportes_ia necesita para
    generar el reporte sin tener que reejecutar nada: eda_resumen,
    predicciones_futuras, interpretación y los resultados completos del
    tuning (espacio de búsqueda, combinaciones evaluadas, etc.).
    """
    sesion = obtener_sesion()
    try:
        serie = resultado_comparacion.get("_serie")
        df_plato = resultado_comparacion.get("_df_plato")
        tiene_serie = serie is not None and not serie.empty

        ejecucion = EjecucionEntrenamiento(
            id_plato=id_plato,
            id_usuario=id_usuario,
            estado="completado",
            modelo_ganador=resultado_comparacion.get("modelo_ganador"),
            criterio_seleccion=resultado_comparacion.get("criterio_seleccion"),
            duracion_segundos=duracion_segundos,
            numero_registros=int(len(df_plato)) if df_plato is not None else None,
            fecha_inicio_datos=serie["fecha"].min().date() if tiene_serie else None,
            fecha_fin_datos=serie["fecha"].max().date() if tiene_serie else None,
            dias_adelante=dias_adelante,
            clima=clima,
            evento=evento,
            metadata_json=json.dumps(metadata_extra, ensure_ascii=False, default=str) if metadata_extra else None,
        )
        sesion.add(ejecucion)
        sesion.flush()  # asigna id_ejecucion antes del commit

        metricas_por_modelo = resultado_comparacion.get("metricas_por_modelo", {})
        info_modelos = resultado_comparacion.get("info_modelos", {})
        orden = sorted(
            (n for n, m in metricas_por_modelo.items() if m.get("mae") is not None),
            key=lambda n: metricas_por_modelo[n]["mae"],
        )

        for nombre, metricas in metricas_por_modelo.items():
            posicion = (orden.index(nombre) + 1) if nombre in orden else None
            resultado_modelo = ResultadoModelo(
                id_ejecucion=ejecucion.id_ejecucion,
                modelo=nombre,
                categoria="hibrido" if nombre in MODELOS_HIBRIDOS else "clasico",
                mae=metricas.get("mae"),
                rmse=metricas.get("rmse"),
                mape=metricas.get("mape"),
                smape=metricas.get("smape"),
                r2=metricas.get("r2"),
                hiperparametros_json=json.dumps(info_modelos.get(nombre, {}), ensure_ascii=False, default=str),
                posicion=posicion,
                error_mensaje=metricas.get("error"),
            )
            sesion.add(resultado_modelo)
            sesion.flush()

            if folds_por_modelo and nombre in folds_por_modelo:
                for fold in folds_por_modelo[nombre].get("folds", []):
                    sesion.add(ResultadoFold(
                        id_resultado_modelo=resultado_modelo.id_resultado_modelo,
                        numero_fold=fold.get("numero_fold"),
                        fecha_inicio_train=_a_fecha(fold.get("fecha_inicio_train")),
                        fecha_fin_train=_a_fecha(fold.get("fecha_fin_train")),
                        fecha_inicio_val=_a_fecha(fold.get("fecha_inicio_val")),
                        fecha_fin_val=_a_fecha(fold.get("fecha_fin_val")),
                        n_train=fold.get("n_train"),
                        n_val=fold.get("n_val"),
                        mae=fold.get("mae"),
                        rmse=fold.get("rmse"),
                        mape=fold.get("mape"),
                        smape=fold.get("smape"),
                        r2=fold.get("r2"),
                        tiempo_entrenamiento=fold.get("tiempo_entrenamiento"),
                        tiempo_inferencia=fold.get("tiempo_inferencia"),
                        error_mensaje=fold.get("error"),
                    ))

        for prueba in (pruebas_estadisticas or []):
            sesion.add(ResultadoPruebaEstadistica(
                id_ejecucion=ejecucion.id_ejecucion,
                prueba=prueba.get("prueba", "desconocida"),
                modelo_a=prueba.get("modelo_a") or prueba.get("modelo_1"),
                modelo_b=prueba.get("modelo_b") or prueba.get("modelo_2"),
                estadistico=prueba.get("estadistico"),
                p_valor=prueba.get("p_valor"),
                p_valor_ajustado=prueba.get("p_valor_ajustado"),
                significativo=prueba.get("significativo"),
                interpretacion=prueba.get("interpretacion"),
            ))

        sesion.commit()
        return ejecucion.id_ejecucion
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


def guardar_registro_modelo_guardado(
    id_plato: int,
    id_ejecucion: int | None,
    modelo: str,
    hash_datos: str,
    metadata: dict | None = None,
) -> None:
    """
    Registra en BD que existe un modelo guardado en disco para el
    plato (historial); desactiva cualquier registro previamente activo
    para ese mismo plato.
    """
    sesion = obtener_sesion()
    try:
        sesion.query(ModeloGuardado).filter(
            ModeloGuardado.id_plato == id_plato, ModeloGuardado.activo == True  # noqa: E712
        ).update({"activo": False})

        registro = ModeloGuardado(
            id_plato=id_plato,
            id_ejecucion=id_ejecucion,
            modelo=modelo,
            ruta=f"models/plato_{id_plato}",  # ruta lógica relativa, no absoluta
            hash_datos=hash_datos,
            activo=True,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False, default=str),
        )
        sesion.add(registro)
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
