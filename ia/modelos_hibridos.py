"""
=================================================================
SIGPDA - Modelos híbridos independientes: Transformer+RF, Transformer+GBR
=================================================================
Cada modelo combina las representaciones "atendidas" producidas por
MultiHeadSelfAttention (ver ia.predictor) con UN ÚNICO regresor de
scikit-learn, a diferencia de HybridTransformerModel (ia/predictor.py),
que combina un ensemble de 4 modelos (RF+GBR+LR+DT) con un
meta-learner Ridge. HybridTransformerModel se conserva intacto
únicamente por compatibilidad con el endpoint /predecir existente
(modelo_tipo="transformer_hibrido").

Esto permite que Transformer+Random Forest y Transformer+Gradient
Boosting aparezcan como dos modelos científicamente independientes
en la comparación de 5 modelos exigida por la tesis.

NOTA DE HONESTIDAD CIENTÍFICA
------------------------------
La capa de atención (MultiHeadSelfAttention) usa proyecciones
W_Q/W_K/W_V/W_O inicializadas aleatoriamente y NO actualizadas por
retropropagación: es una transformación aleatoria fija que expande
el espacio de features, no un Transformer entrenado end-to-end.
Esto se documenta explícitamente en get_info() de cada modelo para
no sobrerrepresentar la arquitectura ante el lector de la tesis.
La migración a un encoder Transformer real entrenable (PyTorch) se
evalúa como fase final independiente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from ia.predictor import MultiHeadSelfAttention, FEATURES

NOTA_ATENCION_NO_ENTRENADA = (
    "La proyección de atención (W_Q/W_K/W_V/W_O) es aleatoria fija y NO se "
    "actualiza por retropropagación; actúa como expansión no lineal de "
    "features, no como un Transformer entrenado end-to-end."
)


def _auto_hiperparametros_atencion(n_muestras: int) -> tuple[int, int]:
    """Mismo criterio heurístico usado por HybridTransformerModel."""
    if n_muestras >= 200:
        return 4, 16
    elif n_muestras >= 100:
        return 4, 8
    elif n_muestras >= 50:
        return 2, 8
    else:
        return 2, 4


# ================================================================
# MODELOS — PIPELINE COMPARTIDO, REGRESOR INTERCAMBIABLE
# ================================================================

class _BaseAttentionHybridModel:
    """
    Pipeline compartido:
      StandardScaler -> MultiHeadSelfAttention (fija) ->
      concatenación [originales ‖ atendidas] -> UN regresor.

    Las subclases solo definen `_crear_regresor()` y `NOMBRE_REGRESOR`.
    """
    MAX_CONTEXT = 200
    NOMBRE_REGRESOR = "base"

    def __init__(self, n_heads: int = 4, d_k: int = 16, semilla: int = 42, **hp_regresor):
        self.n_heads = n_heads
        self.d_k = d_k
        self.semilla = semilla
        self.hp_regresor = hp_regresor
        self.scaler = StandardScaler()
        self.attention: MultiHeadSelfAttention | None = None
        self.regresor = None
        self.X_context: np.ndarray | None = None
        self.is_fitted = False

    def _crear_regresor(self):
        raise NotImplementedError

    def fit(self, X: np.ndarray, y: np.ndarray) -> "_BaseAttentionHybridModel":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, d = X.shape

        self.scaler.fit(X)
        Xs = self.scaler.transform(X)
        self.X_context = Xs[-self.MAX_CONTEXT:]

        self.attention = MultiHeadSelfAttention(d, self.n_heads, self.d_k, seed=self.semilla)
        Xa, _ = self.attention.forward(Xs)
        Xc = np.concatenate([Xs, Xa], axis=1)

        self.regresor = self._crear_regresor()
        self.regresor.fit(Xc, y)
        self.is_fitted = True
        return self

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("El modelo no ha sido entrenado (llame a fit() primero).")

        X_test = np.asarray(X_test, dtype=float)
        Xs_test = self.scaler.transform(X_test)

        # Concatenar contexto de entrenamiento + test para que la atención
        # tenga referencia histórica (mismo criterio que HybridTransformerModel).
        X_full = np.concatenate([self.X_context, Xs_test], axis=0)
        X_full_att, _ = self.attention.forward(X_full)
        Xa_test = X_full_att[-len(X_test):]
        Xc_test = np.concatenate([Xs_test, Xa_test], axis=1)

        return np.maximum(0, self.regresor.predict(Xc_test))

    def get_info(self) -> dict:
        info = {
            "arquitectura": f"Atención MHA({self.n_heads} cab., d_k={self.d_k}) + {self.NOMBRE_REGRESOR}",
            "n_heads": self.n_heads,
            "d_k": self.d_k,
            "regresor": self.NOMBRE_REGRESOR,
            "hiperparametros_regresor": {k: v for k, v in self.hp_regresor.items()},
            "nota_atencion": NOTA_ATENCION_NO_ENTRENADA,
        }
        if hasattr(self.regresor, "feature_importances_"):
            n_orig = len(FEATURES)
            importancias = self.regresor.feature_importances_[:n_orig]
            info["importancia_features"] = {
                name: float(imp) for name, imp in zip(FEATURES, importancias)
            }
        return info


class TransformerRandomForestModel(_BaseAttentionHybridModel):
    NOMBRE_REGRESOR = "Random Forest"

    def _crear_regresor(self):
        hp = {"n_estimators": 150, "max_depth": 10, "random_state": self.semilla, "n_jobs": -1}
        hp.update(self.hp_regresor)
        return RandomForestRegressor(**hp)


class TransformerGradientBoostingModel(_BaseAttentionHybridModel):
    NOMBRE_REGRESOR = "Gradient Boosting"

    def _crear_regresor(self):
        hp = {"n_estimators": 100, "learning_rate": 0.08, "max_depth": 4, "random_state": self.semilla}
        hp.update(self.hp_regresor)
        return GradientBoostingRegressor(**hp)


# ================================================================
# CONSTRUCCIÓN DE FEATURES PARA FECHAS DE TEST/FUTURO (centralizada)
# ================================================================

def construir_features_desde_serie(
    serie_fechas: pd.DataFrame,
    ventas_7d_ref: float,
    cat_enc: int,
    clima: int,
    evento: int,
) -> np.ndarray:
    """
    Construye la matriz de features para un modelo híbrido a partir de
    fechas (test o futuro), sin usar información posterior a esas fechas.

    ventas_7d_ref: media de los últimos 7 días del período de entrenamiento
    (o del histórico completo, si se predice el futuro).
    """
    filas = []
    for fecha in serie_fechas["fecha"]:
        fecha_dt = pd.Timestamp(fecha)
        filas.append({
            "dia_semana": fecha_dt.dayofweek,
            "mes": fecha_dt.month,
            "dia_mes": fecha_dt.day,
            "es_finde": int(fecha_dt.dayofweek >= 5),
            "clima": clima,
            "evento": evento,
            "cat_enc": cat_enc,
            "ventas_7d": ventas_7d_ref,
        })
    return pd.DataFrame(filas)[FEATURES].values


# ================================================================
# ENTRENAMIENTO + EVALUACIÓN (usados por la comparación de modelos)
# ================================================================

def _entrenar_evaluar_hibrido(
    clase_modelo,
    df_plato_train: pd.DataFrame,
    serie_train: pd.DataFrame,
    serie_test: pd.DataFrame,
    cat_enc: int,
    clima: int,
    evento: int,
    hiperparametros: dict | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    if len(df_plato_train) < 5:
        raise ValueError(
            f"Datos insuficientes en el período de entrenamiento para el modelo "
            f"híbrido (solo {len(df_plato_train)} registros)."
        )

    X_train = df_plato_train[FEATURES].fillna(0).values
    y_train = df_plato_train["cantidad"].values.astype(float)

    hp = dict(hiperparametros or {})
    n_heads = hp.pop("n_heads", None)
    d_k = hp.pop("d_k", None)
    if n_heads is None or d_k is None:
        n_heads, d_k = _auto_hiperparametros_atencion(len(X_train))

    modelo = clase_modelo(n_heads=n_heads, d_k=d_k, **hp)
    modelo.fit(X_train, y_train)

    ventas_7d_ref = float(serie_train["cantidad"].tail(7).mean())
    X_test = construir_features_desde_serie(serie_test, ventas_7d_ref, cat_enc, clima, evento)
    pred_test = np.maximum(0.0, modelo.predict(X_test))
    vals_test = serie_test["cantidad"].values.astype(float)
    errores = np.abs(vals_test - pred_test)

    return pred_test, errores, modelo.get_info()


def entrenar_evaluar_transformer_rf(
    df_plato_train, serie_train, serie_test, cat_enc, clima, evento, hiperparametros=None,
):
    return _entrenar_evaluar_hibrido(
        TransformerRandomForestModel, df_plato_train, serie_train, serie_test,
        cat_enc, clima, evento, hiperparametros,
    )


def entrenar_evaluar_transformer_gbr(
    df_plato_train, serie_train, serie_test, cat_enc, clima, evento, hiperparametros=None,
):
    return _entrenar_evaluar_hibrido(
        TransformerGradientBoostingModel, df_plato_train, serie_train, serie_test,
        cat_enc, clima, evento, hiperparametros,
    )


# ================================================================
# PREDICCIÓN FUTURA
# ================================================================

def _predecir_futuro_hibrido(
    clase_modelo, df_plato, fechas_futuras, ventas_7d_ref, cat_enc, clima, evento,
    hiperparametros=None,
) -> np.ndarray:
    X = df_plato[FEATURES].fillna(0).values
    y = df_plato["cantidad"].values.astype(float)

    hp = dict(hiperparametros or {})
    n_heads = hp.pop("n_heads", None)
    d_k = hp.pop("d_k", None)
    if n_heads is None or d_k is None:
        n_heads, d_k = _auto_hiperparametros_atencion(len(X))

    modelo = clase_modelo(n_heads=n_heads, d_k=d_k, **hp)
    modelo.fit(X, y)

    filas_futuras = pd.DataFrame({"fecha": pd.to_datetime(list(fechas_futuras))})
    X_fut = construir_features_desde_serie(filas_futuras, ventas_7d_ref, cat_enc, clima, evento)
    return np.maximum(0.0, modelo.predict(X_fut))


def predecir_futuro_transformer_rf(
    df_plato, fechas_futuras, ventas_7d_ref, cat_enc, clima, evento, hiperparametros=None,
):
    return _predecir_futuro_hibrido(
        TransformerRandomForestModel, df_plato, fechas_futuras, ventas_7d_ref,
        cat_enc, clima, evento, hiperparametros,
    )


def predecir_futuro_transformer_gbr(
    df_plato, fechas_futuras, ventas_7d_ref, cat_enc, clima, evento, hiperparametros=None,
):
    return _predecir_futuro_hibrido(
        TransformerGradientBoostingModel, df_plato, fechas_futuras, ventas_7d_ref,
        cat_enc, clima, evento, hiperparametros,
    )


# ================================================================
# AJUSTE SOBRE TODO EL DATASET (para persistir con ia.model_registry)
# ================================================================

def ajustar_hibrido_completo(
    clase_modelo, df_plato: pd.DataFrame, hiperparametros: dict | None = None,
) -> tuple["_BaseAttentionHybridModel", dict]:
    """
    Entrena un modelo híbrido sobre TODO el histórico disponible del
    plato (sin split) y retorna la instancia ya ajustada (picklable
    con joblib) junto a la información de su arquitectura, para que
    ia.model_registry pueda guardarla y predecir después sin reentrenar.
    """
    X = df_plato[FEATURES].fillna(0).values
    y = df_plato["cantidad"].values.astype(float)

    hp = dict(hiperparametros or {})
    n_heads = hp.pop("n_heads", None)
    d_k = hp.pop("d_k", None)
    if n_heads is None or d_k is None:
        n_heads, d_k = _auto_hiperparametros_atencion(len(X))

    modelo = clase_modelo(n_heads=n_heads, d_k=d_k, **hp)
    modelo.fit(X, y)
    return modelo, modelo.get_info()
