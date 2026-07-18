"""
=================================================================
SIGPDA - Registro de modelos entrenados (persistencia sin reentrenar)
=================================================================
Guarda el modelo ganador de la comparación de 5 modelos para poder
predecir sin volver a entrenar. Cada plato tiene como máximo UN
modelo activo guardado en disco (el más reciente); el historial
completo de ejecuciones se conserva en la base de datos (tablas
EjecucionEntrenamiento / ModeloGuardado, ver Fase 7).

Seguridad (evita path traversal): la ruta de cada modelo se deriva
EXCLUSIVAMENTE de int(id_plato); nunca se acepta una ruta de archivo
proporcionada por el cliente.

Escritura atómica: el artefacto y los metadatos se escriben primero
en un archivo temporal en el mismo directorio y luego se renombran
(os.replace, atómico en el mismo sistema de archivos), para no dejar
modelos parcialmente escritos si el proceso se interrumpe.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
import sklearn
import statsmodels

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
VERSION_MODELO = "1.0"

TIPOS_VALIDOS = {
    "arima",
    "prophet",
    "holt_winters",
    "transformer_random_forest",
    "transformer_gradient_boosting",
}


# ================================================================
# UTILIDADES DE SEGURIDAD Y ESCRITURA ATÓMICA
# ================================================================

def _ruta_plato(id_plato) -> Path:
    """
    Deriva la ruta del directorio del modelo EXCLUSIVAMENTE a partir de
    un id_plato entero validado (nunca de una ruta externa), evitando
    path traversal.
    """
    try:
        id_plato_int = int(id_plato)
    except (TypeError, ValueError):
        raise ValueError("id_plato debe ser un entero.") from None

    if id_plato_int <= 0:
        raise ValueError("id_plato debe ser un entero positivo.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR / f"plato_{id_plato_int}"


def _escribir_atomico(ruta_destino: Path, escribir_fn: Callable[[str], None]) -> None:
    """Escribe en un archivo temporal en el mismo directorio y renombra atómicamente."""
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    fd, ruta_tmp = tempfile.mkstemp(dir=str(ruta_destino.parent), prefix=".tmp_")
    os.close(fd)
    try:
        escribir_fn(ruta_tmp)
        os.replace(ruta_tmp, ruta_destino)
    except Exception:
        if os.path.exists(ruta_tmp):
            os.remove(ruta_tmp)
        raise


def _versiones_librerias() -> dict:
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "statsmodels": statsmodels.__version__,
    }


def calcular_hash_dataset(n_registros: int, fecha_inicio, fecha_fin, suma_cantidad: float) -> str:
    """
    Firma ligera y reproducible del dataset usado para entrenar. No es
    un hash criptográfico de todos los bytes de los datos; basta para
    detectar si el histórico cambió sustancialmente desde el último
    entrenamiento (nuevos registros, rango de fechas distinto, etc.).
    """
    firma = f"{n_registros}|{fecha_inicio}|{fecha_fin}|{round(float(suma_cantidad), 2)}"
    return hashlib.sha256(firma.encode("utf-8")).hexdigest()[:16]


def _metadata_publica(metadata: dict) -> dict:
    """Copia de metadata sin exponer rutas internas del sistema de archivos."""
    return {k: v for k, v in metadata.items() if k not in ("ruta_artefacto",)}


# ================================================================
# GUARDAR / CARGAR
# ================================================================

def guardar_modelo(
    id_plato,
    nombre_plato: str,
    tipo_modelo: str,
    modelo_objeto,
    hiperparametros: dict,
    metricas: dict,
    n_registros: int,
    fecha_inicio_datos: str,
    fecha_fin_datos: str,
    hash_datos: str,
    id_ejecucion: int | None = None,
    semilla: int = 42,
    contexto_prediccion: dict | None = None,
) -> dict:
    """
    Guarda el modelo ganador de forma atómica: artefacto (joblib) +
    metadatos (JSON). Sobrescribe el modelo previamente guardado para
    ese plato — solo se conserva el más reciente en disco.
    """
    if tipo_modelo not in TIPOS_VALIDOS:
        raise ValueError(f"tipo_modelo inválido: {tipo_modelo!r}. Válidos: {sorted(TIPOS_VALIDOS)}")

    directorio = _ruta_plato(id_plato)
    ruta_artefacto = directorio / "modelo.joblib"
    ruta_metadata = directorio / "metadata.json"

    metadata = {
        "id_plato": int(id_plato),
        "nombre_plato": nombre_plato,
        "tipo_modelo": tipo_modelo,
        "tipo_modelo_legible": tipo_modelo.replace("_", " ").title(),
        "id_ejecucion": id_ejecucion,
        "hiperparametros": hiperparametros,
        "metricas": metricas,
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        "rango_temporal_datos": {"inicio": fecha_inicio_datos, "fin": fecha_fin_datos},
        "n_registros": int(n_registros),
        "version_modelo": VERSION_MODELO,
        "versiones_librerias": _versiones_librerias(),
        "hash_datos": hash_datos,
        "semilla": semilla,
        "contexto_prediccion": contexto_prediccion or {},
    }

    _escribir_atomico(ruta_artefacto, lambda tmp: joblib.dump(modelo_objeto, tmp))
    _escribir_atomico(
        ruta_metadata,
        lambda tmp: Path(tmp).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"),
    )

    logger.info(f"Modelo '{tipo_modelo}' guardado para el plato {id_plato}.")
    return {"guardado": True, "tipo_modelo": tipo_modelo, "fecha": metadata["fecha_entrenamiento"]}


def cargar_modelo(id_plato):
    """Retorna (modelo_objeto, metadata) o None si no hay modelo guardado para el plato."""
    directorio = _ruta_plato(id_plato)
    ruta_artefacto = directorio / "modelo.joblib"
    ruta_metadata = directorio / "metadata.json"

    if not ruta_artefacto.exists() or not ruta_metadata.exists():
        return None

    metadata = json.loads(ruta_metadata.read_text(encoding="utf-8"))
    modelo_objeto = joblib.load(ruta_artefacto)
    return modelo_objeto, metadata


def existe_modelo_vigente(id_plato, hash_datos_actual: str | None = None) -> dict:
    """
    Informa si hay un modelo guardado, cuándo se entrenó, qué modelo
    es, sus métricas, y si los datos han cambiado desde entonces
    (recomendando reentrenar en ese caso).
    """
    cargado = cargar_modelo(id_plato)
    if cargado is None:
        return {
            "existe": False, "vigente": False, "metadata": None,
            "recomienda_reentrenar": True,
            "motivo": "No hay modelo guardado para este plato.",
        }

    _modelo, metadata = cargado
    metadata_publica = _metadata_publica(metadata)

    if hash_datos_actual is None:
        return {
            "existe": True, "vigente": True, "metadata": metadata_publica,
            "recomienda_reentrenar": False,
            "motivo": "Modelo guardado disponible.",
        }

    datos_cambiaron = metadata.get("hash_datos") != hash_datos_actual
    return {
        "existe": True,
        "vigente": not datos_cambiaron,
        "metadata": metadata_publica,
        "recomienda_reentrenar": datos_cambiaron,
        "motivo": (
            "Los datos históricos cambiaron desde el último entrenamiento."
            if datos_cambiaron else
            "El modelo guardado sigue vigente para los datos actuales."
        ),
    }


def listar_modelos_guardados() -> list:
    """Lista los modelos guardados (uno por plato como máximo)."""
    if not MODELS_DIR.exists():
        return []

    resultados = []
    for directorio in sorted(MODELS_DIR.iterdir()):
        if not directorio.is_dir() or not directorio.name.startswith("plato_"):
            continue
        ruta_metadata = directorio / "metadata.json"
        if not ruta_metadata.exists():
            continue
        try:
            metadata = json.loads(ruta_metadata.read_text(encoding="utf-8"))
            resultados.append(_metadata_publica(metadata))
        except Exception as exc:
            logger.warning(f"No se pudo leer metadata en {directorio}: {exc}")

    return resultados


def eliminar_modelo(id_plato) -> dict:
    """Elimina el modelo guardado de un plato, solo si existe y la ruta es segura."""
    directorio = _ruta_plato(id_plato)
    if not directorio.exists():
        return {"eliminado": False, "motivo": "No hay modelo guardado para este plato."}

    # Cinturón de seguridad adicional: nunca borrar fuera de MODELS_DIR.
    if MODELS_DIR.resolve() not in directorio.resolve().parents:
        raise RuntimeError("Ruta de modelo fuera del directorio esperado; operación abortada.")

    shutil.rmtree(directorio)
    logger.info(f"Modelo eliminado para el plato {id_plato}.")
    return {"eliminado": True}


# ================================================================
# PREDICCIÓN CON EL MODELO GUARDADO (SIN REENTRENAR)
# ================================================================

def predecir_con_modelo_guardado(id_plato, dias_adelante: int, clima: int = 2, evento: int = 0) -> dict:
    """Predice usando el modelo guardado, sin volver a entrenarlo."""
    from ia.modelos_hibridos import construir_features_desde_serie
    from ia.predictor import recomendar_produccion, calcular_riesgo_desperdicio

    cargado = cargar_modelo(id_plato)
    if cargado is None:
        return {"error": f"No hay modelo guardado para el plato {id_plato}."}

    modelo_objeto, metadata = cargado
    tipo = metadata["tipo_modelo"]
    contexto = metadata.get("contexto_prediccion", {})

    hoy = date.today()
    fechas_futuras = [hoy + timedelta(days=i + 1) for i in range(dias_adelante)]

    try:
        if tipo == "arima":
            valores = np.maximum(0.0, modelo_objeto.forecast(steps=dias_adelante))
        elif tipo == "prophet":
            df_futuro = pd.DataFrame({"ds": pd.to_datetime(fechas_futuras)})
            pronostico = modelo_objeto.predict(df_futuro)
            valores = np.maximum(0.0, pronostico["yhat"].values)
        elif tipo == "holt_winters":
            valores = np.maximum(0.0, modelo_objeto.forecast(dias_adelante))
        elif tipo in ("transformer_random_forest", "transformer_gradient_boosting"):
            ventas_7d_ref = contexto.get("ventas_7d", 0.0)
            cat_enc = contexto.get("cat_enc", 0)
            X_fut = construir_features_desde_serie(
                pd.DataFrame({"fecha": pd.to_datetime(fechas_futuras)}),
                ventas_7d_ref, cat_enc, clima, evento,
            )
            valores = modelo_objeto.predict(X_fut)
        else:
            return {"error": f"Tipo de modelo guardado desconocido: {tipo}"}
    except Exception as exc:
        logger.error(f"Error prediciendo con modelo guardado (plato {id_plato}): {exc}")
        return {"error": "No se pudo generar la predicción con el modelo guardado."}

    mae_referencia = (metadata.get("metricas") or {}).get("mae") or 1.0
    predicciones = []
    for fecha_f, demanda_f in zip(fechas_futuras, valores):
        demanda_f = max(0.0, float(demanda_f))
        recomendacion = recomendar_produccion(demanda_f, mae_referencia)
        riesgo = calcular_riesgo_desperdicio(demanda_f, recomendacion, mae_referencia)
        predicciones.append({
            "fecha": fecha_f.isoformat(),
            "demanda_estimada": round(demanda_f, 2),
            "recomendacion": recomendacion,
            "riesgo": riesgo,
        })

    return {
        "usando_modelo_guardado": True,
        "tipo_modelo": tipo,
        "tipo_modelo_legible": metadata.get("tipo_modelo_legible", tipo),
        "fecha_entrenamiento": metadata.get("fecha_entrenamiento"),
        "metricas_entrenamiento": metadata.get("metricas"),
        "predicciones_futuras": predicciones,
    }
