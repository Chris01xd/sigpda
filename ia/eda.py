"""
=================================================================
SIGPDA - Análisis Exploratorio de Datos (EDA) para IA
=================================================================
Genera un diagnóstico estructurado (JSON, no imágenes) del
histórico de demanda de un plato: estadísticas descriptivas,
calidad de datos, distribución, estacionalidad y correlaciones.

Separación de responsabilidades:
  - `generar_eda_desde_df(...)`  : lógica pura sobre un DataFrame.
                                    Probable con datos sintéticos.
  - `generar_eda(id_plato)`      : wrapper que consulta la base de
                                    datos y delega en la función pura.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from database.conexion import obtener_sesion
from database.modelos import Venta, DetalleVenta, Plato
from ia.data_preparation import limpiar_y_validar, preparar_serie_diaria, columnas_clave_duplicados
from ia.predictor import enriquecer_features

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MIN_DIAS_ANALISIS_MENSUAL = 60
MIN_DIAS_COMPARACION_ROBUSTA = 30

COLUMNAS_CORRELACION = [
    "cantidad", "precio", "dia_semana", "mes", "es_finde", "clima", "evento", "ventas_7d",
]


# ================================================================
# CONSULTA CRUDA (nivel transacción, sin agregar) — solo para EDA
# ================================================================

def _consultar_transacciones_crudas(id_plato: int) -> pd.DataFrame:
    """
    Consulta las ventas de un plato SIN agregación por día, para
    poder diagnosticar duplicados y nulos a nivel de transacción.
    """
    sesion = obtener_sesion()
    try:
        filas = (
            sesion.query(
                DetalleVenta.id_venta, DetalleVenta.id_plato, Venta.fecha, DetalleVenta.cantidad,
                Plato.categoria, Plato.precio_venta,
            )
            .join(Venta, DetalleVenta.id_venta == Venta.id_venta)
            .join(Plato, DetalleVenta.id_plato == Plato.id_plato)
            .filter(DetalleVenta.id_plato == id_plato)
            .all()
        )
    finally:
        sesion.close()

    columnas = ["id_venta", "id_plato", "fecha", "cantidad", "categoria", "precio"]
    if not filas:
        return pd.DataFrame(columns=columnas)

    df = pd.DataFrame(filas, columns=columnas)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def _obtener_plato(id_plato: int) -> Plato | None:
    sesion = obtener_sesion()
    try:
        return sesion.query(Plato).filter(Plato.id_plato == id_plato).first()
    finally:
        sesion.close()


# ================================================================
# ESTRUCTURA VACÍA (dataset insuficiente / inexistente)
# ================================================================

def _estructura_vacia(plato_nombre: str, categoria: str, advertencias: list[str]) -> dict:
    return {
        "resumen": {
            "plato": plato_nombre, "categoria": categoria,
            "registros_transacciones": 0, "dias_con_venta": 0, "dias_cubiertos": 0,
            "fecha_inicio": None, "fecha_fin": None,
        },
        "estadisticas_descriptivas": {},
        "valores_faltantes": {},
        "duplicados": 0,
        "outliers": {"cantidad": 0, "limite_inferior": None, "limite_superior": None, "fechas": []},
        "serie_historica": [],
        "distribucion": [],
        "por_dia_semana": [],
        "por_mes": [],
        "correlaciones": {},
        "clima_evento": {},
        "advertencias": advertencias,
    }


# ================================================================
# FUNCIÓN PURA — TESTEABLE CON DATOS SINTÉTICOS
# ================================================================

def generar_eda_desde_df(
    df_crudo: pd.DataFrame,
    plato_nombre: str = "",
    categoria: str = "",
) -> dict:
    """Genera el diagnóstico EDA completo a partir de un DataFrame crudo (una fila por venta)."""
    if df_crudo.empty:
        return _estructura_vacia(plato_nombre, categoria, ["Sin datos históricos para este plato."])

    # --- Calidad de datos sobre los datos crudos (antes de limpiar) ---
    # "Duplicado" = el mismo plato facturado más de una vez en la MISMA venta
    # (id_venta + id_plato repetidos). Dos ventas distintas del mismo plato el
    # mismo día por igual cantidad NO son un duplicado, son dos pedidos reales.
    columnas_dup = columnas_clave_duplicados(df_crudo)
    duplicados = int(df_crudo.duplicated(subset=columnas_dup).sum()) if columnas_dup else 0
    valores_faltantes = {col: int(df_crudo[col].isna().sum()) for col in df_crudo.columns}

    df_limpio, advertencias = limpiar_y_validar(df_crudo)
    if df_limpio.empty:
        advertencias.append("Tras la limpieza no quedaron registros válidos.")
        return _estructura_vacia(plato_nombre, categoria, advertencias)

    serie = preparar_serie_diaria(df_limpio)
    cantidades = serie["cantidad"].values.astype(float)

    fecha_inicio = serie["fecha"].min()
    fecha_fin = serie["fecha"].max()
    dias_cubiertos = int((fecha_fin - fecha_inicio).days) + 1
    dias_con_venta = int(df_limpio["fecha"].nunique())

    n_interpolados = int(serie["interpolado"].sum())
    if n_interpolados > 0:
        advertencias.append(
            f"{n_interpolados} día(s) sin ventas registradas fueron interpolados linealmente."
        )

    resumen = {
        "plato": plato_nombre,
        "categoria": categoria,
        "registros_transacciones": int(len(df_limpio)),
        "dias_con_venta": dias_con_venta,
        "dias_cubiertos": dias_cubiertos,
        "fecha_inicio": fecha_inicio.date().isoformat(),
        "fecha_fin": fecha_fin.date().isoformat(),
    }

    # --- Estadísticas descriptivas ---
    q1, mediana, q3 = np.percentile(cantidades, [25, 50, 75])
    iqr = q3 - q1
    estadisticas_descriptivas = {
        "media": round(float(np.mean(cantidades)), 4),
        "mediana": round(float(mediana), 4),
        "desviacion_estandar": round(float(np.std(cantidades, ddof=1)), 4) if len(cantidades) > 1 else 0.0,
        "minimo": round(float(np.min(cantidades)), 4),
        "maximo": round(float(np.max(cantidades)), 4),
        "q1": round(float(q1), 4),
        "q3": round(float(q3), 4),
        "rango_intercuartilico": round(float(iqr), 4),
    }

    # --- Outliers vía rango intercuartílico (IQR) ---
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr
    mascara_outliers = (cantidades < limite_inferior) | (cantidades > limite_superior)
    outliers = {
        "cantidad": int(mascara_outliers.sum()),
        "limite_inferior": round(float(limite_inferior), 4),
        "limite_superior": round(float(limite_superior), 4),
        "fechas": serie.loc[mascara_outliers, "fecha"].dt.date.astype(str).tolist()[:20],
    }

    # --- Serie histórica (evolución) ---
    serie_historica = [
        {
            "fecha": row.fecha.date().isoformat(),
            "cantidad": round(float(row.cantidad), 2),
            "interpolado": bool(row.interpolado),
        }
        for row in serie.itertuples()
    ]

    # --- Distribución (histograma) ---
    n_bins = min(10, max(3, int(np.sqrt(len(cantidades)))))
    frecuencias, bordes = np.histogram(cantidades, bins=n_bins)
    distribucion = [
        {
            "rango_inicio": round(float(bordes[i]), 2),
            "rango_fin": round(float(bordes[i + 1]), 2),
            "frecuencia": int(frecuencias[i]),
        }
        for i in range(len(frecuencias))
    ]

    # --- Demanda por día de la semana ---
    serie_dia = serie.copy()
    serie_dia["dia_semana"] = serie_dia["fecha"].dt.dayofweek
    agg_dia = serie_dia.groupby("dia_semana")["cantidad"].agg(["mean", "sum", "count"]).reindex(range(7))
    por_dia_semana = [
        {
            "dia_semana": DIAS_SEMANA[i],
            "demanda_promedio": round(float(agg_dia.loc[i, "mean"]), 4) if not pd.isna(agg_dia.loc[i, "mean"]) else 0.0,
            "demanda_total": round(float(agg_dia.loc[i, "sum"]), 2) if not pd.isna(agg_dia.loc[i, "sum"]) else 0.0,
            "n": int(agg_dia.loc[i, "count"]) if not pd.isna(agg_dia.loc[i, "count"]) else 0,
        }
        for i in range(7)
    ]

    # --- Demanda por mes (solo si hay cobertura suficiente) ---
    por_mes: list[dict] = []
    if dias_cubiertos >= MIN_DIAS_ANALISIS_MENSUAL:
        serie_mes = serie.copy()
        serie_mes["periodo_mes"] = serie_mes["fecha"].dt.strftime("%Y-%m")
        agg_mes = serie_mes.groupby("periodo_mes")["cantidad"].agg(["mean", "sum", "count"]).reset_index()
        por_mes = [
            {
                "mes": row["periodo_mes"],
                "demanda_promedio": round(float(row["mean"]), 4),
                "demanda_total": round(float(row["sum"]), 2),
                "n": int(row["count"]),
            }
            for _, row in agg_mes.iterrows()
        ]
    else:
        advertencias.append(
            f"Cobertura insuficiente ({dias_cubiertos} días, mínimo {MIN_DIAS_ANALISIS_MENSUAL}) "
            f"para un análisis mensual confiable."
        )

    # --- Correlaciones entre variables numéricas (incluye clima/evento simulados) ---
    df_enriquecido = enriquecer_features(df_limpio)
    columnas_presentes = [c for c in COLUMNAS_CORRELACION if c in df_enriquecido.columns]
    correlaciones: dict = {}
    clima_evento: dict = {}
    if len(df_enriquecido) > 1 and columnas_presentes:
        corr_df = df_enriquecido[columnas_presentes].corr(numeric_only=True)
        correlaciones = {
            col: {
                c2: (round(float(v), 4) if pd.notna(v) else None)
                for c2, v in corr_df[col].items()
            }
            for col in corr_df.columns
        }
        if "clima" in df_enriquecido.columns and "evento" in df_enriquecido.columns:
            clima_evento = {
                "clima_distribucion": {int(k): int(v) for k, v in df_enriquecido["clima"].value_counts().sort_index().items()},
                "evento_distribucion": {int(k): int(v) for k, v in df_enriquecido["evento"].value_counts().sort_index().items()},
                "nota": (
                    "El clima es simulado (no hay proveedor meteorológico integrado); "
                    "el evento se deriva de feriados nacionales del Perú."
                ),
            }

    if dias_cubiertos < MIN_DIAS_COMPARACION_ROBUSTA:
        advertencias.append(
            f"Dataset con solo {dias_cubiertos} día(s) de cobertura: insuficiente para una "
            f"comparación robusta de modelos (mínimo recomendado: {MIN_DIAS_COMPARACION_ROBUSTA} días)."
        )

    return {
        "resumen": resumen,
        "estadisticas_descriptivas": estadisticas_descriptivas,
        "valores_faltantes": valores_faltantes,
        "duplicados": duplicados,
        "outliers": outliers,
        "serie_historica": serie_historica,
        "distribucion": distribucion,
        "por_dia_semana": por_dia_semana,
        "por_mes": por_mes,
        "correlaciones": correlaciones,
        "clima_evento": clima_evento,
        "advertencias": advertencias,
    }


# ================================================================
# WRAPPER — CONSULTA LA BASE DE DATOS
# ================================================================

def generar_eda(id_plato: int) -> dict | None:
    """
    Genera el EDA para un plato consultando la base de datos.
    Retorna None si el plato no existe (para que el router responda 404).
    """
    plato = _obtener_plato(id_plato)
    if plato is None:
        return None

    df_crudo = _consultar_transacciones_crudas(id_plato)
    return generar_eda_desde_df(df_crudo, plato_nombre=plato.nombre, categoria=plato.categoria or "")
