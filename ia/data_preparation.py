"""
=================================================================
SIGPDA - Pipeline centralizado de preparación de datos para IA
=================================================================
Fuente única de verdad para limpiar, validar y transformar el
histórico de ventas antes de entrenar o analizar cualquier modelo.

Reutiliza ia.predictor.construir_dataset_historico() y
enriquecer_features() (ya probados en producción) y añade lo que
falta para el flujo de tesis:

  - limpieza y validación explícita con advertencias
  - lags y medias móviles construidos EXCLUSIVAMENTE con datos
    pasados (shift(1) antes de cualquier rolling) para evitar
    fuga de información
  - división train / validation / test estrictamente cronológica
  - escalado (StandardScaler) ajustado únicamente sobre train

Todas las funciones que transforman datos reciben/retornan
DataFrames de pandas puros (sin tocar la base de datos), de modo
que pueden probarse con datasets sintéticos pequeños. La única
función que toca la base de datos es `preparar_pipeline_completo`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ia.predictor import construir_dataset_historico, enriquecer_features, FEATURES

# Columnas numéricas sobre las que tiene sentido construir lags / medias móviles
COLUMNA_OBJETIVO = "cantidad"

# Lags y ventanas de medias móviles por defecto (en días)
LAGS_DEFECTO = (1, 7, 14)
VENTANAS_MEDIA_DEFECTO = (7, 14)


# ================================================================
# 1. LIMPIEZA Y VALIDACIÓN
# ================================================================

def columnas_clave_duplicados(df: pd.DataFrame) -> list[str]:
    """
    Determina la clave que identifica una fila como transacción única.

    - Si el DataFrame es a nivel de transacción (incluye `id_venta`), una
      fila duplicada es el mismo plato facturado más de una vez dentro
      de la MISMA venta (bug real de registro). NO se usa `cantidad`
      ni `precio` como parte de la clave: dos ventas distintas del
      mismo plato, el mismo día, por la misma cantidad, al mismo precio
      de carta, son transacciones legítimas — no duplicados.
    - Si el DataFrame ya está agregado por día (sin `id_venta`, p. ej.
      la salida de construir_dataset_historico), la clave natural es
      (fecha, id_plato), que tras el agregado nunca debería repetirse
      (chequeo defensivo, no debería eliminar nada en la práctica).
    """
    if "id_venta" in df.columns and "id_plato" in df.columns:
        return ["id_venta", "id_plato"]
    return [c for c in ["fecha", "id_plato"] if c in df.columns]


def limpiar_y_validar(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Ordena cronológicamente, controla duplicados, maneja nulos de
    forma justificada, valida tipos y evita cantidades negativas.

    Retorna (df_limpio, advertencias).
    """
    advertencias: list[str] = []

    if df.empty:
        return df, ["Sin datos históricos: el dataset está vacío."]

    df = df.copy()

    # --- Validar tipos de fecha y cantidad ---
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    filas_fecha_invalida = int(df["fecha"].isna().sum())
    if filas_fecha_invalida > 0:
        advertencias.append(
            f"Se descartaron {filas_fecha_invalida} registro(s) con fecha inválida."
        )
        df = df[df["fecha"].notna()]

    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    nulos_cantidad = int(df["cantidad"].isna().sum())
    if nulos_cantidad > 0:
        advertencias.append(
            f"Se encontraron {nulos_cantidad} valor(es) nulo(s) en 'cantidad'; "
            f"se imputaron con 0 por tratarse de una ausencia de venta registrada."
        )
        df["cantidad"] = df["cantidad"].fillna(0)

    # --- Evitar cantidades negativas ---
    negativos = int((df["cantidad"] < 0).sum())
    if negativos > 0:
        advertencias.append(
            f"Se detectaron {negativos} valor(es) de cantidad negativos; "
            f"se corrigieron a 0 (una venta no puede ser negativa)."
        )
        df["cantidad"] = df["cantidad"].clip(lower=0)

    # --- Duplicados (ver columnas_clave_duplicados para el criterio exacto) ---
    columnas_dup = columnas_clave_duplicados(df)
    duplicados = int(df.duplicated(subset=columnas_dup).sum()) if columnas_dup else 0
    if duplicados > 0:
        advertencias.append(
            f"Se encontraron {duplicados} fila(s) duplicada(s) según clave {columnas_dup}; "
            f"se conservó una copia de cada una."
        )
        df = df.drop_duplicates(subset=columnas_dup)

    # --- Orden cronológico ---
    df = df.sort_values("fecha").reset_index(drop=True)

    return df, advertencias


# ================================================================
# 2. SERIE DIARIA CONTINUA (sin huecos)
# ================================================================

def preparar_serie_diaria(df_plato: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega la demanda por día y rellena fechas faltantes mediante
    interpolación lineal, para obtener una serie continua apta para
    ARIMA, Prophet y Holt-Winters.

    Retorna DataFrame con columnas: fecha, cantidad, interpolado (bool).
    """
    serie = (
        df_plato.groupby("fecha")["cantidad"]
        .sum()
        .reset_index()
        .sort_values("fecha")
        .set_index("fecha")
    )

    idx_completo = pd.date_range(serie.index.min(), serie.index.max(), freq="D")
    serie = serie.reindex(idx_completo)
    serie["interpolado"] = serie["cantidad"].isna()
    serie["cantidad"] = serie["cantidad"].interpolate(method="linear").fillna(0)
    serie.index.name = "fecha"

    return serie.reset_index()


# ================================================================
# 3. LAGS Y MEDIAS MÓVILES — SIN FUGA DE INFORMACIÓN
# ================================================================

def construir_lags_y_medias_moviles(
    serie: pd.DataFrame,
    lags: tuple[int, ...] = LAGS_DEFECTO,
    ventanas_media: tuple[int, ...] = VENTANAS_MEDIA_DEFECTO,
    columna: str = COLUMNA_OBJETIVO,
) -> pd.DataFrame:
    """
    Añade columnas lag_N y media_movil_N a una serie diaria ordenada
    cronológicamente.

    IMPORTANTE (anti-fuga de información):
      - lag_N(t) = valor(t - N)               -> solo pasado
      - media_movil_N(t) = media(t-N ... t-1)  -> excluye el día actual,
        se calcula mediante shift(1) ANTES del rolling.

    La fila t nunca contiene información de t o de fechas posteriores.
    """
    serie = serie.copy().sort_values("fecha").reset_index(drop=True)

    for lag in lags:
        serie[f"lag_{lag}"] = serie[columna].shift(lag)

    pasado = serie[columna].shift(1)  # excluye el día actual
    for ventana in ventanas_media:
        serie[f"media_movil_{ventana}"] = pasado.rolling(window=ventana, min_periods=1).mean()

    return serie


# ================================================================
# 4. SPLIT CRONOLÓGICO TRAIN / VALIDATION / TEST
# ================================================================

def dividir_train_val_test(
    df: pd.DataFrame,
    val_size: float = 0.15,
    test_size: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Divide un DataFrame ya ordenado cronológicamente en tres bloques
    contiguos (train, validation, test), sin mezclar ni barajar fechas.

    train  = primer tramo (más antiguo)
    val    = tramo intermedio
    test   = último tramo (más reciente)
    """
    if not df["fecha"].is_monotonic_increasing:
        df = df.sort_values("fecha").reset_index(drop=True)

    n = len(df)
    n_test = max(1, int(round(n * test_size)))
    n_val = max(1, int(round(n * val_size)))
    n_train = n - n_val - n_test

    if n_train < 1:
        # Dataset muy pequeño: prioriza dejar al menos 1 registro en train
        n_train = max(1, n - 2)
        n_val = max(0, (n - n_train) // 2)
        n_test = n - n_train - n_val

    train = df.iloc[:n_train].reset_index(drop=True)
    val = df.iloc[n_train:n_train + n_val].reset_index(drop=True)
    test = df.iloc[n_train + n_val:].reset_index(drop=True)

    return train, val, test


# ================================================================
# 5. ESCALADO — AJUSTADO ÚNICAMENTE SOBRE TRAIN
# ================================================================

def escalar_features(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    columnas: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Ajusta un StandardScaler exclusivamente con el bloque de
    entrenamiento y transforma train/val/test con esos mismos
    parámetros (evita fuga de información desde validation/test).

    Retorna los tres DataFrames transformados (copias, columnas
    escaladas con sufijo "_esc") y un diccionario serializable con
    los parámetros de escalado.
    """
    columnas_presentes = [c for c in columnas if c in train.columns]
    scaler = StandardScaler()

    train = train.copy()
    val = val.copy()
    test = test.copy()

    if columnas_presentes and len(train) > 0:
        scaler.fit(train[columnas_presentes].fillna(0).values)
        for bloque in (train, val, test):
            if len(bloque) == 0:
                continue
            valores = scaler.transform(bloque[columnas_presentes].fillna(0).values)
            for i, col in enumerate(columnas_presentes):
                bloque[f"{col}_esc"] = valores[:, i]

    params = {
        "columnas": columnas_presentes,
        "media": scaler.mean_.tolist() if hasattr(scaler, "mean_") else [],
        "escala": scaler.scale_.tolist() if hasattr(scaler, "scale_") else [],
    }
    return train, val, test, params


# ================================================================
# 6. PIPELINE COMPLETO (orquestación, toca la base de datos)
# ================================================================

def preparar_pipeline_completo(
    id_plato: int,
    clima: int = 2,
    evento: int = 0,
    lags: tuple[int, ...] = LAGS_DEFECTO,
    ventanas_media: tuple[int, ...] = VENTANAS_MEDIA_DEFECTO,
    val_size: float = 0.15,
    test_size: float = 0.15,
) -> dict:
    """
    Orquesta el pipeline completo para un plato: construcción del
    dataset histórico, limpieza, enriquecimiento con features,
    lags/medias móviles sin fuga, y split train/val/test.

    Retorna un dict con:
      df_plato        : DataFrame enriquecido y limpio (por transacción)
      serie_diaria     : serie diaria continua con lags y medias móviles
      train, val, test : bloques cronológicos de la serie diaria
      scaler_params    : parámetros de escalado ajustados sobre train
      advertencias     : lista de advertencias encontradas
    """
    advertencias: list[str] = []

    df_global = construir_dataset_historico(id_plato=id_plato)
    if df_global.empty:
        return {
            "df_plato": df_global,
            "serie_diaria": pd.DataFrame(columns=["fecha", "cantidad"]),
            "train": pd.DataFrame(), "val": pd.DataFrame(), "test": pd.DataFrame(),
            "scaler_params": {},
            "advertencias": ["Sin datos históricos para este plato."],
        }

    df_limpio, adv_limpieza = limpiar_y_validar(df_global)
    advertencias += adv_limpieza

    df_enriquecido = enriquecer_features(df_limpio)
    serie = preparar_serie_diaria(df_enriquecido)
    serie = construir_lags_y_medias_moviles(serie, lags=lags, ventanas_media=ventanas_media)

    n_interpolados = int(serie["interpolado"].sum())
    if n_interpolados > 0:
        advertencias.append(
            f"{n_interpolados} día(s) sin ventas registradas fueron interpolados "
            f"linealmente para mantener una serie continua."
        )

    train, val, test = dividir_train_val_test(serie, val_size=val_size, test_size=test_size)

    columnas_escalar = [c for c in ["cantidad"] + [f"lag_{l}" for l in lags]
                        + [f"media_movil_{v}" for v in ventanas_media] if c in serie.columns]
    train_e, val_e, test_e, scaler_params = escalar_features(train, val, test, columnas_escalar)

    return {
        "df_plato": df_enriquecido,
        "serie_diaria": serie,
        "train": train_e, "val": val_e, "test": test_e,
        "scaler_params": scaler_params,
        "advertencias": advertencias,
    }
