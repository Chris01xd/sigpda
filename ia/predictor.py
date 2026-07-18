"""
=================================================================
SIGPDA - Módulo de IA / Predicción de Demanda
=================================================================
Modelos disponibles:
  - random_forest       : RandomForestRegressor (sklearn)
  - regresion_lineal    : LinearRegression (sklearn)
  - decision_tree       : DecisionTreeRegressor (sklearn)
  - transformer_hibrido : Multi-Head Self-Attention (NumPy) +
                          Ensemble RF/GBR/LR/DT + Ridge Meta-Learner

Variables de entrada (FEATURES):
  dia_semana · mes · dia_mes · es_finde · clima
  evento · cat_enc · ventas_7d

Salidas:
  demanda estimada · recomendación de producción
  riesgo de desperdicio · MAE · R² · (transformer: pesos ensemble)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler

from database.conexion import obtener_sesion
from database.modelos import Venta, DetalleVenta, Plato


# ================================================================
# CONSTRUCCIÓN DEL DATASET HISTÓRICO
# ================================================================

def construir_dataset_historico(id_plato: int = None) -> pd.DataFrame:
    """Genera un DataFrame con histórico de demanda diaria por plato."""
    sesion = obtener_sesion()
    query = sesion.query(
        DetalleVenta.id_plato,
        Venta.fecha,
        DetalleVenta.cantidad,
        Plato.categoria,
        Plato.precio_venta,
    ).join(Venta, DetalleVenta.id_venta == Venta.id_venta) \
     .join(Plato, DetalleVenta.id_plato == Plato.id_plato)

    if id_plato:
        query = query.filter(DetalleVenta.id_plato == id_plato)

    filas = query.all()
    sesion.close()

    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas, columns=["id_plato", "fecha", "cantidad", "categoria", "precio"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.groupby(["fecha", "id_plato", "categoria"], as_index=False).agg({
        "cantidad": "sum",
        "precio": "first",
    })
    return df


def enriquecer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega variables de calendario y simulación de clima/eventos."""
    if df.empty:
        return df

    df = df.copy().sort_values(["id_plato", "fecha"])
    df["dia_semana"] = df["fecha"].dt.dayofweek
    df["mes"] = df["fecha"].dt.month
    df["dia_mes"] = df["fecha"].dt.day
    df["es_finde"] = (df["dia_semana"] >= 5).astype(int)

    rng = np.random.default_rng(seed=42)
    df["clima"] = rng.integers(1, 4, size=len(df))

    feriados_peru = [
        "01-01", "05-01", "06-29", "07-28", "07-29",
        "08-30", "10-08", "11-01", "12-08", "12-25",
    ]
    df["evento"] = df["fecha"].dt.strftime("%m-%d").isin(feriados_peru).astype(int) * 2
    df.loc[df["fecha"].dt.day == 15, "evento"] = 1

    le = LabelEncoder()
    df["cat_enc"] = le.fit_transform(df["categoria"].astype(str))

    df["ventas_7d"] = df.groupby("id_plato")["cantidad"].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    return df


FEATURES = ["dia_semana", "mes", "dia_mes", "es_finde", "clima", "evento", "cat_enc", "ventas_7d"]
FEATURE_NAMES = ["Día semana", "Mes", "Día mes", "Fin de semana", "Clima", "Evento", "Categoría", "Media 7d"]


# ================================================================
# TRANSFORMER HÍBRIDO — ARQUITECTURA
# ================================================================

class MultiHeadSelfAttention:
    """
    Multi-Head Self-Attention implementado en NumPy (sin PyTorch/TensorFlow).

    Opera sobre la matriz de muestras X ∈ R^(n×d):
      - Cada muestra "atiende" a otras muestras históricamente similares.
      - Los pesos de atención capturan relaciones entre días de demanda.
      - n_heads cabezas permiten capturar diferentes tipos de similaridad.
    """

    def __init__(self, n_features: int, n_heads: int = 4, d_k: int = 16, seed: int = 42):
        self.n_features = n_features
        self.n_heads = n_heads
        self.d_k = d_k

        rng = np.random.default_rng(seed)
        s = np.sqrt(2.0 / (n_features + d_k))

        # Proyecciones Q, K, V por cabeza: (n_features, d_k)
        self.W_Q = [rng.normal(0, s, (n_features, d_k)) for _ in range(n_heads)]
        self.W_K = [rng.normal(0, s, (n_features, d_k)) for _ in range(n_heads)]
        self.W_V = [rng.normal(0, s, (n_features, d_k)) for _ in range(n_heads)]
        # Proyección de salida: (n_heads * d_k, n_features)
        self.W_O = rng.normal(0, s, (n_heads * d_k, n_features))

        # Feed-Forward Network (2 capas): n_features → 2*n_features → n_features
        d_ff = n_features * 2
        self.W_ff1 = rng.normal(0, s, (n_features, d_ff))
        self.W_ff2 = rng.normal(0, s, (d_ff, n_features))

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        x = x - x.max(axis=-1, keepdims=True)
        e = np.exp(np.clip(x, -100, 100))
        return e / (e.sum(axis=-1, keepdims=True) + 1e-9)

    @staticmethod
    def _layer_norm(x: np.ndarray) -> np.ndarray:
        mean = x.mean(axis=-1, keepdims=True)
        std = x.std(axis=-1, keepdims=True) + 1e-9
        return (x - mean) / std

    def forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        X : (n_samples, n_features)
        Retorna:
          out     : (n_samples, n_features)  representaciones enriquecidas
          weights : (n_samples, n_samples)   pesos promedio de atención
        """
        head_outs, head_weights = [], []

        for h in range(self.n_heads):
            Q = X @ self.W_Q[h]   # (n, d_k)
            K = X @ self.W_K[h]
            V = X @ self.W_V[h]

            # Scaled dot-product attention: (n, n)
            scores = Q @ K.T / np.sqrt(self.d_k)
            W = self._softmax(scores)
            head_outs.append(W @ V)   # (n, d_k)
            head_weights.append(W)

        # Proyección multi-cabeza + residual + LayerNorm
        concat = np.concatenate(head_outs, axis=-1)   # (n, n_heads*d_k)
        mha_out = concat @ self.W_O                    # (n, n_features)
        out = self._layer_norm(mha_out + X)

        # Feed-Forward: ReLU + residual + LayerNorm
        ffn = np.maximum(0, out @ self.W_ff1) @ self.W_ff2
        out = self._layer_norm(ffn + out)

        avg_weights = np.mean(head_weights, axis=0)   # (n, n)
        return out, avg_weights


class HybridTransformerModel:
    """
    Modelo híbrido para predicción de demanda:

    1. StandardScaler  — normalización de features
    2. MultiHeadSelfAttention (NumPy) — representaciones enriquecidas
    3. Concatenación  [features originales ‖ features atendidas]
    4. Ensemble de modelos base (RF, GBR, LR, DT) — predicciones individuales
    5. Ridge Meta-Learner — combinación óptima de predicciones
    """

    BASE_MODELS = {
        "rf":  lambda: RandomForestRegressor(n_estimators=150, random_state=42, max_depth=10, n_jobs=-1),
        "gbr": lambda: GradientBoostingRegressor(n_estimators=100, random_state=42, learning_rate=0.08, max_depth=4),
        "lr":  lambda: LinearRegression(),
        "dt":  lambda: DecisionTreeRegressor(random_state=42, max_depth=7),
    }
    BASE_LABELS = {"rf": "Random Forest", "gbr": "Gradient Boosting", "lr": "Regresión Lineal", "dt": "Árbol Decisión"}
    MAX_CONTEXT = 200   # muestras máximas para atención en inferencia

    def __init__(self, n_heads: int = 4, d_k: int = 16):
        self.n_heads = n_heads
        self.d_k = d_k
        self.scaler = StandardScaler()
        self.attention: MultiHeadSelfAttention | None = None
        self.models: dict = {}
        self.meta: Ridge = Ridge(alpha=0.5)
        self.X_context: np.ndarray | None = None
        self.meta_weights_: dict = {}
        self.feature_importances_: np.ndarray | None = None
        self.train_attention_: np.ndarray | None = None
        self.is_fitted = False

    def _attended(self, X_sc: np.ndarray) -> np.ndarray:
        out, weights = self.attention.forward(X_sc)
        return out, weights

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HybridTransformerModel":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n, d = X.shape

        self.scaler.fit(X)
        Xs = self.scaler.transform(X)

        # Guardar contexto para inferencia
        self.X_context = Xs[-self.MAX_CONTEXT:]

        # Inicializar y aplicar atención
        self.attention = MultiHeadSelfAttention(d, self.n_heads, self.d_k)
        Xa, self.train_attention_ = self._attended(Xs)

        # Features combinadas: [originales ‖ atendidas]
        Xc = np.concatenate([Xs, Xa], axis=1)

        # Instanciar modelos base
        self.models = {k: fn() for k, fn in self.BASE_MODELS.items()}

        # Obtener predicciones OOF para el meta-learner
        n_cv = min(5, max(2, n // 5))
        meta_X = np.zeros((n, len(self.models)))

        for i, (key, model) in enumerate(self.models.items()):
            if n >= n_cv * 3:
                try:
                    oof = cross_val_predict(model, Xc, y, cv=n_cv)
                    meta_X[:, i] = np.maximum(0, oof)
                except Exception:
                    model.fit(Xc, y)
                    meta_X[:, i] = np.maximum(0, model.predict(Xc))
            else:
                model.fit(Xc, y)
                meta_X[:, i] = np.maximum(0, model.predict(Xc))
            model.fit(Xc, y)   # Re-entrenar en todos los datos

        # Meta-learner
        self.meta.fit(meta_X, y)

        # Guardar info interpretable
        self.meta_weights_ = {
            self.BASE_LABELS[k]: float(w)
            for k, w in zip(self.models.keys(), self.meta.coef_)
        }
        if hasattr(self.models["rf"], "feature_importances_"):
            full_imp = self.models["rf"].feature_importances_
            self.feature_importances_ = full_imp[:d]   # Solo features originales

        self.is_fitted = True
        return self

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        X_test = np.asarray(X_test, dtype=float)
        Xs_test = self.scaler.transform(X_test)

        # Concatenar contexto + test para que la atención tenga referencia histórica
        X_full = np.concatenate([self.X_context, Xs_test], axis=0)
        X_full_att, _ = self._attended(X_full)

        # Extraer solo las filas de test
        Xa_test = X_full_att[-len(X_test):]
        Xc_test = np.concatenate([Xs_test, Xa_test], axis=1)

        meta_X = np.zeros((len(X_test), len(self.models)))
        for i, model in enumerate(self.models.values()):
            meta_X[:, i] = np.maximum(0, model.predict(Xc_test))

        return np.maximum(0, self.meta.predict(meta_X))

    def get_info(self) -> dict:
        """Retorna métricas interpretables del modelo para visualización."""
        return {
            "arquitectura": f"MHA({self.n_heads} cabezas, d_k={self.d_k}) + Ensemble + Ridge",
            "n_heads": self.n_heads,
            "d_k": self.d_k,
            "pesos_ensemble": self.meta_weights_,
            "importancia_features": {
                name: float(imp)
                for name, imp in zip(FEATURE_NAMES, self.feature_importances_)
            } if self.feature_importances_ is not None else {},
        }


# ================================================================
# MODELOS CLÁSICOS
# ================================================================

def entrenar_modelo(df: pd.DataFrame, modelo_tipo: str = "random_forest"):
    """
    Entrena un modelo clásico (no-transformer) y retorna (modelo, mae, r2).
    Para transformer_hibrido usar entrenar_transformer().
    """
    if df.empty or len(df) < 10:
        return None, None, None

    X = df[FEATURES].fillna(0).values
    y = df["cantidad"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if modelo_tipo == "random_forest":
        modelo = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    elif modelo_tipo == "regresion_lineal":
        modelo = LinearRegression()
    elif modelo_tipo == "decision_tree":
        modelo = DecisionTreeRegressor(random_state=42, max_depth=8)
    else:
        modelo = RandomForestRegressor(n_estimators=100, random_state=42)

    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else 0.0

    return modelo, mae, r2


def entrenar_transformer(df: pd.DataFrame, n_heads: int = 4, d_k: int = 16):
    """
    Entrena el HybridTransformerModel y retorna (modelo, mae, r2).
    """
    if df.empty or len(df) < 10:
        return None, None, None

    X = df[FEATURES].fillna(0).values
    y = df["cantidad"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo = HybridTransformerModel(n_heads=n_heads, d_k=d_k)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred)) if len(y_test) > 1 else 0.0

    return modelo, mae, r2


# ================================================================
# PREDICCIÓN (INFERENCIA)
# ================================================================

def predecir_demanda(modelo, fecha_objetivo: date, plato_info: dict,
                     clima: int = 2, evento: int = 0, ventas_7d: float = 0) -> float:
    """Predice la demanda para un plato en una fecha específica."""
    fecha_dt = pd.Timestamp(fecha_objetivo)
    X_pred = pd.DataFrame([{
        "dia_semana": fecha_dt.dayofweek,
        "mes":        fecha_dt.month,
        "dia_mes":    fecha_dt.day,
        "es_finde":   1 if fecha_dt.dayofweek >= 5 else 0,
        "clima":      clima,
        "evento":     evento,
        "cat_enc":    plato_info.get("cat_enc", 0),
        "ventas_7d":  ventas_7d,
    }])
    pred = modelo.predict(X_pred.values)[0]
    return max(0.0, float(pred))


def calcular_riesgo_desperdicio(demanda: float, produccion: float, mae: float) -> str:
    if demanda <= 0:
        return "alto"
    sobreprod_pct = (produccion - demanda) / demanda * 100
    error_rel = (mae / demanda * 100) if demanda > 0 else 100
    if error_rel > 40 or sobreprod_pct > 25:
        return "alto"
    if error_rel > 20 or sobreprod_pct > 15:
        return "medio"
    return "bajo"


def recomendar_produccion(demanda: float, mae: float, factor: float = 1.10) -> int:
    valor = demanda * factor
    valor = max(valor, demanda + mae * 0.5)
    return int(np.ceil(valor))


# ================================================================
# PIPELINE COMPLETO
# ================================================================

def ejecutar_prediccion_completa(
    id_plato: int,
    fechas_objetivo: list,
    modelo_tipo: str = "random_forest",
    clima: int = 2,
    evento: int = 0,
    n_heads: int = 4,
    d_k: int = 16,
):
    """
    Pipeline completo de predicción.

    Retorna:
      resultados : list[dict]  — predicción por fecha
      mensaje    : str
      mae        : float | None
      r2         : float | None
      transformer_info : dict | None  — solo si modelo_tipo == "transformer_hibrido"
    """
    df_global = construir_dataset_historico()
    if df_global.empty:
        return [], "Sin datos históricos. Genere ventas primero.", None, None, None

    df_global = enriquecer_features(df_global)
    df_plato = df_global[df_global["id_plato"] == id_plato]

    if df_plato.empty:
        return [], f"Sin datos históricos para el plato {id_plato}.", None, None, None

    # —————— Entrenar ——————
    transformer_info = None

    if modelo_tipo == "transformer_hibrido":
        modelo, mae, r2 = entrenar_transformer(df_global, n_heads=n_heads, d_k=d_k)
        if modelo is None:
            return [], "Datos insuficientes para transformer (mínimo 10 registros).", None, None, None
        transformer_info = modelo.get_info()
    else:
        modelo, mae, r2 = entrenar_modelo(df_global, modelo_tipo)
        if modelo is None:
            return [], "Datos insuficientes para entrenar (mínimo 10 registros).", None, None, None

    cat_enc = int(df_plato["cat_enc"].iloc[0]) if len(df_plato) > 0 else 0
    ventas_7d = float(df_plato["ventas_7d"].iloc[-1]) if len(df_plato) > 0 else 0

    # —————— Inferencia ——————
    resultados = []
    for f_obj in fechas_objetivo:
        demanda = predecir_demanda(
            modelo, f_obj, {"cat_enc": cat_enc},
            clima=clima, evento=evento, ventas_7d=ventas_7d,
        )
        recomendacion = recomendar_produccion(demanda, mae or 1)
        riesgo = calcular_riesgo_desperdicio(demanda, recomendacion, mae or 1)
        confianza = max(0.0, min(1.0, r2)) if r2 else 0.0

        resultados.append({
            "fecha":             f_obj,
            "demanda_estimada":  round(demanda, 2),
            "recomendacion":     recomendacion,
            "riesgo":            riesgo,
            "mae":               round(mae, 3) if mae else 0,
            "r2":                round(r2, 3) if r2 else 0,
            "confianza":         round(confianza, 3),
            "modelo":            modelo_tipo,
        })

    return resultados, "OK", mae, r2, transformer_info
